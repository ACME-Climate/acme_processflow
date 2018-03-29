import os
import logging
import time
import re
from datetime import datetime
from threading import Thread
from shutil import copytree, move, copytree, rmtree, copy2
from subprocess import Popen

from lib.slurm import Slurm
from lib.util import (get_climo_output_files,
                      create_symlink_dir,
                      print_line,
                      render,
                      format_debug)

from lib.YearSet import YearSet, SetStatus
from jobs.Ncclimo import Climo
from jobs.Timeseries import Timeseries
from jobs.AMWGDiagnostic import AMWGDiagnostic
from jobs.APrimeDiags import APrimeDiags
from jobs.E3SMDiags import E3SMDiags
from jobs.JobStatus import JobStatus, StatusMap, ReverseMap


class RunManager(object):
    def __init__(self, event_list, output_path, caseID, scripts_path, thread_list, event, ui, resource_path, account, short_name, url_prefix, always_copy=False, no_host=False):
        self.short_name = short_name
        # self.account = account
        self.account = ''
        self.ui = ui
        self.output_path = output_path
        self.slurm = Slurm()
        self.event_list = event_list
        self.caseID = caseID
        self.job_sets = []
        self.running_jobs = []
        self.monitor_thread = None
        self.thread_list = thread_list
        self.kill_event = event
        self.scripts_path = scripts_path
        self._resource_path = resource_path
        self.max_running_jobs = self.slurm.get_node_number() * 6
        self.no_host = no_host
        self.url_prefix = url_prefix
        self._job_total = 0
        self._job_complete = 0
        self._always_copy = always_copy
        if not os.path.exists(self.scripts_path):
            os.makedirs(self.scripts_path)

    def check_max_running_jobs(self):
        """
        Checks if the maximum number of jobs are running

        Returns True if the max or more are running, false otherwise
        """
        try:
            job_info = self.slurm.queue()
        except:
            return True
        else:
            running_jobs = 0
            for job in job_info:
                if job['STATE'] in ['R', 'PD']:
                    running_jobs += 1
                if running_jobs >= self.max_running_jobs:
                    return True
            return False

    def setup_job_sets(self, set_frequency, sim_start_year, sim_end_year, config, filemanager):
        sim_length = sim_end_year - sim_start_year + 1
        for freq in set_frequency:
            number_of_sets_at_freq = sim_length / freq

            # initialize the YearSet
            for i in range(1, number_of_sets_at_freq + 1):
                start_year = sim_start_year + ((i - 1) * freq)
                end_year = start_year + freq - 1
                msg = 'Creating job_set for {:04d}-{:04d}'.format(start_year, end_year)
                print_line(
                    ui=self.ui,
                    line=msg,
                    event_list=self.event_list,
                    current_state=True)
                new_set = YearSet(
                    set_number=len(self.job_sets) + 1,
                    start_year=start_year,
                    end_year=end_year)
                self.add_jobs(
                    config=config,
                    year_set=new_set,
                    filemanager=filemanager)
                self.job_sets.append(new_set)

    def write_job_sets(self, path):
        if os.path.exists(path):
            os.remove(path)
        out_str = ''
        fp = open(path, 'w')
        for year_set in self.job_sets:
            out_str += 'Year_set {num}: {start:04d} - {end:04d}\n'.format(
                num=year_set.set_number,
                start=year_set.set_start_year,
                end=year_set.set_end_year)

            out_str += 'Status: {status}\n'.format(
                status=year_set.status)

            for job in year_set.jobs:
                out_str += '  >   {type} -- {id}: {status}\n'.format(
                    type=job.type,
                    id=job.job_id,
                    status=job.status)
            out_str += '\n'
            fp.write(out_str)
        fp.close()

    def add_jobs(self, config, year_set, filemanager):
        """
        Initializes and adds all the jobs to the year_set

        Parameters:
            year_set (YearSet): The YearSet to populate with jobs
            config (dict): the master configuration dict
            filemanager (FileManager): The global file manager instance
        """
        required_jobs = {}
        for job_type, freqs in config.get('global').get('set_jobs').items():
            # Default to not running
            required_jobs[job_type] = False
            if not freqs:
                # This job shouldnt be run
                continue
            if isinstance(freqs, str):
                freqs = [freqs]
            for freq in freqs:
                freq = int(freq)
                if freq == year_set.length:
                    # Add the job to this year_set
                    required_jobs[job_type] = True
                    break
        start_year = year_set.set_start_year
        end_year = year_set.set_end_year

        set_string = '{start:04d}-{end:04d}'.format(
            start=start_year,
            end=end_year)

        atm_path = os.path.join(
            config['global']['input_path'],
            'atm')
        output_base_path = config['global']['output_path']
        run_scripts_path = config['global']['run_scripts_path']
        regrid_map_name = config['global']['remap_grid_name']
        native_map_name = config['global']['native_grid_name']

        regrid_output_path = os.path.join(
            output_base_path, 'pp',
            regrid_map_name, 'climo',
            '{}yr'.format(year_set.length))
        if not os.path.exists(regrid_output_path):
            os.makedirs(regrid_output_path)

        native_output_path = os.path.join(
            output_base_path, 'pp',
            native_map_name, 'climo',
            '{}yr'.format(year_set.length))
        if not os.path.exists(native_output_path):
            os.makedirs(native_output_path)

        if required_jobs.get('ncclimo'):
            # Add the ncclimo job to the runmanager
            self.add_climo(
                start_year=year_set.set_start_year,
                end_year=year_set.set_end_year,
                year_set=year_set,
                input_path=atm_path,
                regrid_map_path=config['ncclimo']['regrid_map_path'],
                native_output_path=native_output_path,
                regrid_output_path=regrid_output_path)

        if required_jobs.get('timeseries'):

            regrid_output_path_ts = os.path.join(
                output_base_path, 'pp',
                regrid_map_name, 'ts', 'monthly',
                '{}yr'.format(year_set.length))
            if not os.path.exists(regrid_output_path_ts):
                os.makedirs(regrid_output_path_ts)

            native_output_path = os.path.join(
                output_base_path, 'pp',
                native_map_name, 'ts', 'monthly',
                '{}yr'.format(year_set.length))
            if not os.path.exists(native_output_path):
                os.makedirs(native_output_path)

            # Add the timeseries job to the runmanager
            self.add_timeseries(
                filemanager=filemanager,
                start_year=year_set.set_start_year,
                end_year=year_set.set_end_year,
                year_set=year_set,
                input_path=atm_path,
                regrid_map_path=config['ncclimo']['regrid_map_path'],
                var_list=config['ncclimo']['var_list'],
                regrid_output_path=regrid_output_path_ts,
                native_output_path=native_output_path)

        if required_jobs.get('aprime') or required_jobs.get('aprime_diags'):
            # Add the aprime job
            host_directory = "{experiment}_years{start}-{end}_vs_obs".format(
                experiment=config['global']['experiment'],
                start=year_set.set_start_year,
                end=year_set.set_end_year)
            url_list = [config['global']['img_host_server']]
            if self.url_prefix:
                url_list.append(self.url_prefix)
            url_list += [os.environ['USER'],
                         config['global']['experiment'],
                         config.get('aprime_diags').get('host_directory'),
                         set_string]
            host_url = '/'.join(url_list)

            target_host_path = os.path.join(
                config['global']['host_directory'],
                os.environ['USER'],
                config['global']['experiment'],
                config['aprime_diags']['host_directory'],
                set_string)

            output_path = os.path.join(
                output_base_path,
                'diags',
                regrid_map_name,
                config['aprime_diags']['host_directory'],
                set_string)
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            self.add_aprime(
                simulation_start_year=config['global']['simulation_start_year'],
                target_host_path=target_host_path,
                output_path=output_path,
                web_directory=config['global']['host_directory'],
                host_url=host_url,
                start_year=year_set.set_start_year,
                end_year=year_set.set_end_year,
                year_set=year_set,
                input_base_path=config['global']['output_path'],
                resource_path=config['global']['resource_dir'],
                test_atm_res=config['aprime_diags']['test_atm_res'],
                test_mpas_mesh_name=config['aprime_diags']['test_mpas_mesh_name'],
                aprime_code_path=config['aprime_diags']['aprime_code_path'],
                filemanager=filemanager)

        if required_jobs.get('amwg') or required_jobs.get('AMWG') or required_jobs.get('amwg_diags'):
            # Add AMWG
            web_directory = os.path.join(
                config.get('global').get('host_directory'),
                os.environ['USER'],
                config.get('global').get('experiment'),
                config.get('amwg').get('host_directory'),
                set_string)
            url_list = [config['global']['img_host_server']]
            if self.url_prefix:
                url_list.append(self.url_prefix)
            url_list += [os.environ['USER'],
                         config['global']['experiment'],
                         config.get('amwg').get('host_directory'),
                         set_string]
            host_url = '/'.join(url_list)

            output_path = os.path.join(
                output_base_path,
                'diags',
                regrid_map_name,
                config['amwg']['host_directory'],
                set_string)
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            self.add_amwg(
                start_year=year_set.set_start_year,
                end_year=year_set.set_end_year,
                year_set=year_set,
                resource_path=config['global']['resource_dir'],
                web_directory=web_directory,
                host_url=host_url,
                output_path=output_path,
                regrid_path=regrid_output_path,
                diag_home=config['amwg']['diag_home'])

        if required_jobs.get('e3sm_diags') or required_jobs.get('acme_diags'):
            # Add the e3sm diags
            web_directory = os.path.join(
                config['global']['host_directory'],
                os.environ['USER'],
                config['global']['experiment'],
                config['e3sm_diags']['host_directory'],
                set_string)
            url_list = [config['global']['img_host_server']]
            if self.url_prefix:
                url_list.append(self.url_prefix)
            url_list += [os.environ['USER'],
                         config['global']['experiment'],
                         config.get('e3sm_diags').get('host_directory'),
                         set_string]
            host_url = '/'.join(url_list)

            output_path = os.path.join(
                output_base_path, 
                'diags',
                regrid_map_name, 
                config['e3sm_diags']['host_directory'],
                set_string)
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            self.add_e3sm(
                regrid_output_path=regrid_output_path,
                start_year=year_set.set_start_year,
                end_year=year_set.set_end_year,
                year_set=year_set,
                resource_path=config['global']['resource_dir'],
                web_directory=web_directory,
                host_url=host_url,
                reference_data_path=config['e3sm_diags']['reference_data_path'],
                output_path=output_path,
                # seasons=config['e3sm_diags']['seasons'],
                backend=config['e3sm_diags']['backend'],
                sets=config['e3sm_diags']['sets'])

    def add_climo(self, **kwargs):
        """
        Add an ncclimo job to the job_list

        Parameters:
            start_year (int): the first year
            end_year (int): the last year
            year_set (int): the set number
            input_path (str): the path to the raw cam.h0 files
            regrid_map_path (str): the path to the regrid map
            regrid_output_path (str): the output path for regridded climos
            native_output_path (str): the output path for native climos
        """
        start_year = kwargs['start_year']
        end_year = kwargs['end_year']
        regrid_output_path = kwargs['regrid_output_path']
        native_output_path = kwargs['native_output_path']
        year_set = kwargs['year_set']
        input_path = kwargs['input_path']
        regrid_map_path = kwargs['regrid_map_path']

        if not self._precheck(year_set, 'ncclimo'):
            return

        config = {
            'account': self.account,
            'ui': self.ui,
            'run_scripts_path': self.scripts_path,
            'start_year': start_year,
            'end_year': end_year,
            'caseId': self.caseID,
            'annual_mode': 'sdd',
            'regrid_map_path': regrid_map_path,
            'input_directory': input_path,
            'climo_output_directory': native_output_path,
            'regrid_output_directory': regrid_output_path,
            'year_set': year_set.set_number,
        }
        climo = Climo(
            config=config,
            event_list=self.event_list)
        msg = 'Adding Ncclimo job to the job list: {}'.format(str(climo))
        logging.info(msg)
        year_set.add_job(climo)
        self._job_total += 1

    def add_timeseries(self, **kwargs):
        """
        Add a timeseries job to the job_list

        Parameters:
            start_year (int): the first year
            end_year (int): the last year
            year_set (int): the set number
            input_path (str): the path to the raw cam.h0 files
            regrid_map_path (str): the path to the regrid map
            var_list (list(str)): the list of variables to extract
            regrid_output_path (str): the path to store the regridded timeseries output
            native_output_path (str): the path to store the native timeseries output
            filemanager (FileManager): A pointer to the global filemanager
        """
        start_year = kwargs['start_year']
        end_year = kwargs['end_year']
        year_set = kwargs['year_set']
        input_path = kwargs['input_path']
        regrid_output_path = kwargs['regrid_output_path']
        native_output_path = kwargs['native_output_path']
        regrid_map_path = kwargs['regrid_map_path']
        var_list = kwargs['var_list']
        filemanager = kwargs['filemanager']

        if not self._precheck(year_set, 'timeseries'):
            return

        config = {
            'account': self.account,
            'filemanager': filemanager,
            'ui': self.ui,
            'run_scripts_path': self.scripts_path,
            'annual_mode': 'sdd',
            'caseId': self.caseID,
            'year_set': year_set.set_number,
            'var_list': var_list,
            'start_year': start_year,
            'end_year': end_year,
            'regrid_output_directory': regrid_output_path,
            'native_output_directory': native_output_path,
            'regrid_map_path': regrid_map_path
        }
        timeseries = Timeseries(
            config=config,
            event_list=self.event_list)
        msg = 'Adding Timeseries job to the job list: {}'.format(
            str(timeseries))
        logging.info(msg)
        year_set.add_job(timeseries)
        self._job_total += 1

    def add_aprime(self, **kwargs):
        """
        Add an APrime job to the job_list

        Parameters:
            output_path (str): The path to store the output
            web_directory (str): The path to the directory to store images for hosting
            host_url (str): The url to access the images once their hosted
            year_set (YearSet): The YearSet that this job belongs to
            start_year (int): The start year of this set
            end_year (int): The end year of this set
            input_base_path (str): the global input path
            resource_path (str): Path to the resource directory
            test_atm_res (str): the atm resolution for the test input
            test_mpas_mesh_name (str): The test mpas mesh name
            aprime_code_path (str): the path to the aprime code
            target_host_path (str): the real hosting directory
            sim_start_year (int): the simulation start year
            resource_path (str): path to processflow resource files
        """
        target_host_path = kwargs['target_host_path']
        web_directory = kwargs['web_directory']
        host_url = kwargs['host_url']
        year_set = kwargs['year_set']
        start_year = kwargs['start_year']
        end_year = kwargs['end_year']
        input_base_path = kwargs['input_base_path']
        output_path = kwargs['output_path']
        resource_path = kwargs['resource_path']
        test_atm_res = kwargs['test_atm_res']
        test_mpas_mesh_name = kwargs['test_mpas_mesh_name']
        aprime_code_path = kwargs['aprime_code_path']
        filemanager = kwargs['filemanager']
        simulation_start_year = kwargs['simulation_start_year']
        resource_path = kwargs['resource_path']

        if not self._precheck(year_set, 'aprime_diags'):
            return

        year_set_string = '{start:04d}-{end:04d}'.format(
            start=start_year,
            end=end_year)

        project_dir = output_path
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)

        input_path = os.path.join(
            input_base_path,
            'tmp',
            'aprime',
            year_set_string)
        if not os.path.exists(input_path):
            os.makedirs(input_path)

        # Varify the template
        template_path = os.path.join(
            resource_path,
            'aprime_template.bash')
        if not os.path.exists(template_path):
            msg = 'Unable to find amwg template at {path}'.format(
                path=template_path)
            print_line(
                ui=self.ui,
                line=msg,
                event_list=self.event_list)
            logging.error(msg)
            return

        config = {
            'resource_path': resource_path,
            'account': self.account,
            'simulation_start_year': simulation_start_year,
            'target_host_path': target_host_path,
            'ui': self.ui,
            'web_dir': web_directory,
            'host_url': host_url,
            'experiment': self.caseID,
            'run_scripts_path': self.scripts_path,
            'year_set': year_set.set_number,
            'input_path': input_path,
            'start_year': start_year,
            'end_year': end_year,
            'output_path': project_dir,
            'template_path': template_path,
            'test_atm_res': test_atm_res,
            'test_mpas_mesh_name': test_mpas_mesh_name,
            'aprime_code_path': aprime_code_path,
            'filemanager': filemanager
        }
        aprime = APrimeDiags(
            config=config,
            event_list=self.event_list)
        msg = 'Creating aprime diagnostic: {}'.format(str(aprime))
        logging.info(msg)
        logging.info('Prevalidating aprime')
        year_set.add_job(aprime)
        self._job_total += 1
        

    def add_amwg(self, **kwargs):
        """
        Add an amwg job to the job_list

        Parameters:
            start_year (int): the first year
            end_year (int): the last year
            year_set (int): the set number
            resource_path (str): path to the resource directory
            web_directory (str): the directory to store files for hosting
            host_url (str): the url to view the hosted files
            regrid_path (str): path to the regridded history files
        """
        start_year = kwargs['start_year']
        end_year = kwargs['end_year']
        year_set = kwargs['year_set']
        resource_path = kwargs['resource_path']
        web_directory = kwargs['web_directory']
        host_url = kwargs['host_url']
        regrid_path = kwargs['regrid_path']
        diag_home = kwargs['diag_home']
        output_path = kwargs['output_path']

        if not self._precheck(year_set, 'amwg'):
            return

        year_set_string = '{start:04d}-{end:04d}'.format(
            start=start_year,
            end=end_year)

        # Setup the AMWG temp directory
        temp_path = os.path.join(
            self.output_path,
            'tmp',
            'amwg',
            year_set_string)
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)

        # Varify the template
        template_path = os.path.join(
            resource_path,
            'amwg_template.csh')
        if not os.path.exists(template_path):
            msg = 'Unable to find amwg template at {path}'.format(
                path=template_path)
            logging.error(msg)
            return

        config = {
            'short_name': self.short_name,
            'account': self.account,
            'ui': self.ui,
            'web_dir': web_directory,
            'host_url': host_url,
            'experiment': self.caseID,
            'run_scripts_path': self.scripts_path,
            'output_path': output_path,
            'test_casename': self.caseID,
            'test_path_history': regrid_path + os.sep,
            'regrided_climo_path': regrid_path + os.sep,
            'test_path_climo': temp_path,
            'test_path_diag': output_path,
            'start_year': start_year,
            'end_year': end_year,
            'year_set': year_set.set_number,
            'run_directory': output_path,
            'template_path': template_path,
            'diag_home': diag_home
        }
        amwg_diag = AMWGDiagnostic(
            config=config,
            event_list=self.event_list)
        msg = 'Adding AMWGDiagnostic job to the job list: {}'.format(
            str(amwg_diag))
        logging.info(msg)
        year_set.add_job(amwg_diag)
        self._job_total += 1

    def add_e3sm(self, **kwargs):
        """
        Add an E3SM job to the job_list

        Parameters:
            start_year (int): the first year
            end_year (int): the last year
            year_set (int): the set number
            resource_path (str): path to the resource directory
            web_directory (str): the directory to store files for hosting
            host_url (str): the url to view the hosted files
            reference_data_path (str): Path to the e3sm reference data
        """
        start_year = kwargs['start_year']
        end_year = kwargs['end_year']
        year_set = kwargs['year_set']
        resource_path = kwargs['resource_path']
        web_directory = kwargs['web_directory']
        host_url = kwargs['host_url']
        reference_data_path = kwargs['reference_data_path']
        # seasons = kwargs['seasons']
        backend = kwargs['backend']
        sets = kwargs['sets']
        resource_path = kwargs['resource_path']
        output_path = kwargs['output_path']
        regrid_output_path = kwargs['regrid_output_path']

        if not self._precheck(year_set, 'e3sm_diags'):
            msg = 'Rejecting e3sm_diags-{:04d}-{:04d}'.format(
                year_set.start_year, year_set.end_year)
            print_line(
                ui=self.ui,
                line=msg,
                event_list=self.event_list)
            return

        set_string = '{start:04d}-{end:04d}'.format(
            start=start_year,
            end=end_year)

        # Setup temp directory
        temp_path = os.path.join(
            self.output_path,
            'tmp',
            'e3sm_diags',
            set_string)
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)

        # Varify the template
        template_path = os.path.join(
            resource_path,
            'e3sm_diags_template.py')
        if not os.path.exists(template_path):
            msg = 'Unable to find amwg template at {path}'.format(
                path=template_path)
            logging.error(msg)
            return

        config = {
            'short_name': self.short_name,
            'account': self.account,
            'ui': self.ui,
            'regrid_output_path': regrid_output_path,
            'web_dir': web_directory,
            'host_url': host_url,
            'experiment': self.caseID,
            'regrided_climo_path': temp_path,
            'reference_data_path': reference_data_path,
            'test_name': self.caseID,
            # 'seasons': seasons,
            'backend': backend,
            'sets': sets,
            'results_dir': output_path,
            'template_path': template_path,
            'run_scripts_path': self.scripts_path,
            'end_year': end_year,
            'start_year': start_year,
            'year_set': year_set.set_number,
            'output_path': output_path
        }
        e3sm_diag = E3SMDiags(
            config=config,
            event_list=self.event_list)
        msg = "Adding E3SM Diagnostic to the job list: {}".format(
            str(e3sm_diag))
        logging.info(msg)
        year_set.add_job(e3sm_diag)
        self._job_total += 1

    def _precheck(self, year_set, jobtype):
        """
        Check that the jobtype for that given yearset isnt
        already in the job_list

        Parameters:
            set_number (int): the yearset number to check
            jobtype (str): the type of job to check for
        Returns:
            1 if the job/yearset combo are NOT in the job_list
            0 if they are
        """
        for job in year_set.jobs:
            if job.type == jobtype:
                return False
        return True

    def start_ready_job_sets(self):
        """
        Iterates over the job sets checking for ready ready jobs, and starts them
        """
        all_data_needed = True
        for job_set in self.job_sets:
            # if the job state is ready, but hasnt started yet
            if job_set.status in [SetStatus.DATA_READY, SetStatus.RUNNING, SetStatus.FAILED]:
                # Iterate over all jobs in the set
                for job in job_set.jobs:
                    if job.status == JobStatus.INVALID:
                        msg = 'ERROR: {job}-{start:04d}-{end:04d} is in an INVALID state, see log for details'.format(
                            job=job.type,
                            start=job_set.start_year,
                            end=job_set.end_year)
                        print_line(
                            ui=self.ui,
                            line=msg,
                            event_list=self.event_list,
                            current_state=False,
                            ignore_text=False)
                        logging.error(msg)
                        logging.error(str(job))
                        continue

                    # If the job has any dependencies
                    # iterate through the list to see if they're done
                    ready = True
                    if job.depends_on is not None and len(job.depends_on) > 0:
                        for dependancy in job.depends_on:
                            for dependent_job in job_set.jobs:
                                if dependent_job.type == dependancy:
                                    if dependent_job.status != JobStatus.COMPLETED:
                                        ready = False
                                        msg = '{job} is waiting on {dep}'.format(
                                            job=job.type,
                                            dep=dependent_job.type)
                                        logging.info(msg)
                                        break
                    # If the job isnt ready, skip it
                    if not ready:
                        continue
                    # If the job isnt valid, skip it and move on
                    if job.status not in [JobStatus.VALID, JobStatus.WAITING_ON_INPUT]:
                        continue

                    if self.check_max_running_jobs():
                        msg = 'Too many jobs are running, waiting for the queue to shrink before submitting'
                        logging.info(msg)
                        return
                    msg = "{job}-{start:04d}-{end:04d}: Starting job setup and execute".format(
                        job=job.type,
                        start=job.start_year,
                        end=job.end_year)
                    print_line(
                        ui=self.ui,
                        line=msg,
                        event_list=self.event_list,
                        current_state=True,
                        ignore_text=True)

                    try:
                        # status will be the job id if it started, or -1 if the job needs additional data
                        status = job.execute()
                    except Exception as e:
                        # Slurm threw an exception. Reset the job so we can try again
                        msg = '{job}-{start:04d}-{end:04d}: failed to start execution'.format(
                            job=job.type, start=job.start_year, end=job.end_year)
                        logging.error(msg)
                        msg = format_debug(e)
                        logging.error(e)
                        job.status = JobStatus.VALID
                        continue
                    else:
                        if status == -1:
                            msg = '{job}-{start:04d}-{end:04d}: Requires additional data'.format(
                                job=job.type, start=job.start_year, end=job.end_year)
                            logging.info(msg)
                            job.status = JobStatus.WAITING_ON_INPUT
                            all_data_needed = False
                            continue

                    if job.job_id == 0:
                        self._job_complete += 1
                        msg = '{job}-{start:04d}-{end:04d}: Precomputed, skipping'.format(
                            job=job.type,
                            start=job.start_year,
                            end=job.end_year)
                        print_line(
                            ui=self.ui,
                            line=msg,
                            event_list=self.event_list)
                        logging.info(msg)
                        self.handle_completed_job(job)
                        continue

                    # Check that the job was actually submitted to the queue
                    try:
                        slurm = Slurm()
                        slurm.showjob(job.job_id)
                    except:
                        msg = "Error submitting {job} to queue".format(
                            job=job.type)
                        print_line(
                            ui=self.ui,
                            line=msg,
                            event_list=self.event_list)
                        job.status = JobStatus.VALID
                        return all_data_needed
                    else:
                        self.running_jobs.append(job)
                        self.monitor_running_jobs()
            if job_set.status in [SetStatus.NO_DATA, SetStatus.PARTIAL_DATA]:
                all_data_needed = False
        return all_data_needed

    def monitor_running_jobs(self):
        msg = 'Updating job list'
        print_line(
            ui=self.ui,
            line=msg,
            event_list=self.event_list,
            current_state=True,
            ignore_text=True)
        slurm = Slurm()
        for job in self.running_jobs:
            if job.job_id == 0:
                self._job_complete += 1
                self.handle_completed_job(job)
                self.running_jobs.remove(job)
                continue
            try:
                job_info = slurm.showjob(job.job_id)
            except Exception as e:
                self.running_jobs.remove(job)
                self._job_complete += 1
                if job.postvalidate():
                    job.status = JobStatus.COMPLETED
                else:
                    line = "slurm lookup error for {job}: {id}".format(
                        job=job.type,
                        id=job.job_id)
                    print_line(
                        ui=self.ui,
                        line=line,
                        event_list=self.event_list)
                continue
            status = StatusMap[job_info.get('JobState')]
            if status != job.status:
                msg = '{job}-{start:04d}-{end:04d}: Job id {id} changed from {s1} to {s2}'.format(
                    job=job.type,
                    start=job.start_year,
                    end=job.end_year,
                    s1=ReverseMap[job.status],
                    s2=ReverseMap[status],
                    id=job.job_id)
                print_line(
                    ui=self.ui,
                    line=msg,
                    event_list=self.event_list,
                    current_state=False)
                job.status = status

                if status == JobStatus.RUNNING:
                    job.start_time = datetime.now()
                    for job_set in self.job_sets:
                        if job_set.set_number == job.year_set \
                                and job_set.status != SetStatus.FAILED:
                            job_set.status = SetStatus.RUNNING
                            break
                elif status == JobStatus.COMPLETED:
                    self._job_complete += 1
                    job.end_time = datetime.now()
                    self.handle_completed_job(job)
                    self.running_jobs.remove(job)
                elif status in [JobStatus.FAILED, JobStatus.CANCELLED]:
                    self._job_complete += 1
                    job.end_time = datetime.now()
                    for job_set in self.job_sets:
                        if job_set.set_number == job.year_set:
                            job_set.status = SetStatus.FAILED
                            break
                    self.running_jobs.remove(job)

    def handle_completed_job(self, job):
        """
        Perform post execution tasks
        """
        msg = '{job}-{start:04d}-{end:04d}: Starting post-completion handler'.format(
            job=job.type,
            start=job.start_year,
            end=job.end_year)
        print_line(
            ui=self.ui,
            line=msg,
            event_list=self.event_list,
            current_state=False)
        msg = 'Total status: {percent:.2f}% or {complete}/{total} complete'.format(
            complete=self._job_complete,
            total=self._job_total,
            percent=((self._job_complete * 1.0)/self._job_total)*100)
        print_line(
            ui=self.ui,
            line=msg,
            event_list=self.event_list,
            current_state=True)
        job_set = None
        for s in self.job_sets:
            if s.set_number == job.year_set:
                job_set = s
                break

        # First check that we have the expected output
        if not job.postvalidate():
            msg = '{job}-{start:04d}-{end:04d}: Postvalidate failed after job completion'.format(
                job=job.type,
                start=job.start_year,
                end=job.end_year)
            print_line(
                ui=self.ui,
                line=msg,
                event_list=self.event_list)
            logging.error(msg)
            job.status = JobStatus.FAILED
            job_set.status = SetStatus.FAILED
            return

        # The job completed and has expected output
        done = True if job_set else False
        if done:
            for j in job_set.jobs:
                if j.status != JobStatus.COMPLETED:
                    done = False
                    break
        if done:
            job_set.status = SetStatus.COMPLETED

        if self.no_host:
            msg = '{job}-{start:04d}-{end:04d}: Skipping output hosting'.format(
                job=job.type, start=job.start_year, end=job.end_year)
            print_line(
                ui=self.ui,
                line=msg,
                event_list=self.event_list)
            return

        # Finally host the files
        if job.type == 'aprime_diags':

            # aprime handles its own hosting
            host_directory = "{experiment}_years{start}-{end}_vs_obs".format(
                experiment=job.config['experiment'],
                start=job.start_year,
                end=job.end_year)
            # this is the native aprime host directory
            host_dir = os.path.join(
                job.config['web_dir'],
                os.environ['USER'],
                host_directory)

            # move the files from the place that aprime auto
            # generates them to where we actually want them to be
            # first make sure the parent directory exists
            target_host_dir = job.config['target_host_path']
            head, tail = os.path.split(target_host_dir)
            if not os.path.exists(head):
                os.makedirs(head)

            # next copy over the aprime output
            if os.path.exists(host_dir) and os.path.isdir(host_dir):
                # if the web hosting in aprime worked correctly
                if os.path.exists(target_host_dir):
                    if not self._always_copy:
                        msg = 'aprime-{start:04d}-{end:04d}: previous output found at {src}, not copying'.format(
                            start=job.start_year, end=job.end_year, src=host_dir)
                        logging.info(msg)
                        return
                    rmtree(target_host_dir)
                try:
                    msg = 'aprime-{start:04d}-{end:04d}: copying native host directory from \n\t{src} to \n\t{dst}'.format(
                        start=job.start_year, end=job.end_year, src=host_dir, dst=target_host_dir)
                    logging.info(msg)
                    copytree(
                        src=host_dir,
                        dst=target_host_dir)
                except:
                    msg = 'aprime-{start:04d}-{end:04d}: failed to copy directory from \n\t{src} to \n\t{dst}'.format(
                        start=job.start_year, end=job.end_year, src=host_dir, dst=target_host_dir)
                    logging.info(msg)
                    return
                else:
                    msg = 'aprime-{start:04d}-{end:04d}: removing native host directory {dir}'.format(
                        start=job.start_year, end=job.end_year, dir=host_dir)
                    logging.info(msg)
                    rmtree(host_dir)
            else:
                msg = 'aprime-{start:04d}-{end:04d}: native aprime webhosting failed, attempting to compensate'.format(
                    start=job.start_year, end=job.end_year)
                logging.error(msg)
                # aprimes' webhosting failed, have to compensate
                if os.path.exists(target_host_dir):
                    msg = 'aprime-{start:04d}-{end:04d}: removing previous output'.format(
                        start=job.start_year, end=job.end_year)
                    logging.info(msg)
                    rmtree(target_host_dir)
                source = os.path.join(
                    job.config['output_path'],
                    'coupled_diagnostics',
                    '{exp}_vs_obs'.format(exp=job.config['experiment']),
                    '{exp}_years{start}-{end}_vs_obs'.format(
                        exp=job.config['experiment'], start=job.start_year, end=job.end_year))
                if os.path.exists(source):
                    copytree(
                        src=source,
                        dst=target_host_dir)
                else:
                    msg = 'Unable to find source directory: {}'.format(
                        source)
                    logging.error(msg)

            if not os.path.exists(target_host_dir):
                msg = "aprime-{start:04d}-{end:04d}: Error hosting output at {dir}".format(
                    start=job.start_year, end=job.end_year, dir=target_host_dir)
                logging.error(msg)
                return

            if not os.path.exists(os.path.join(target_host_dir, 'index.html')):
                msg = 'aprime-{:04d}-{:04d}: native index generation failed, rendering from resource'.format(
                    job.start_year, job.end_year)
                logging.info(msg)
                variables = {
                    'experiment': job.config['experiment'],
                    'start_year': '{:04d}'.format(job.start_year),
                    'end_year': '{:04d}'.format(job.end_year)
                }
                resource_path = os.path.join(
                    self._resource_path,
                    'aprime_index.html')
                output_path = os.path.join(
                    target_host_dir,
                    'index.html')
                try:
                    render(
                        variables=variables,
                        input_path=resource_path,
                        output_path=output_path)
                except:
                    msg = 'Failed to render index for a-prime'
                    logging.error(msg)

            if not os.path.exists(os.path.join(target_host_dir, 'acme-banner_1.jpg')):
                try:
                    src = os.path.join(self._resource_path,
                                       'acme-banner_1.jpg')
                    dst = os.path.join(target_host_dir, 'acme-banner_1.jpg')
                    copy2(
                        src=src,
                        dst=dst)
                except Exception as e:
                    msg = 'Failed to copy e3sm banner from {src} to {dst}'.format(
                        src=src, dst=dst)
                    logging.error(msg)

            msg = 'Fixing permissions for {}'.format(target_host_dir)
            print_line(
                ui=self.ui,
                line=msg,
                event_list=self.event_list)
            while True:
                try:
                    p = Popen(['chmod', '-R', '0755', target_host_dir])
                except:
                    sleep(1)
                else:
                    break
            out, err = p.communicate()
            head, _ = os.path.split(target_host_dir)
            os.chmod(head, 0755)

            url = self._format_url(job)
            msg = '{job}-{start:04d}-{end:04d}: Hosted at {url}'.format(
                url=url, job=job.type, start=job.start_year, end=job.end_year)
            print_line(
                ui=self.ui,
                line=msg,
                event_list=self.event_list)

        elif job.type == 'amwg':
            img_dir = '{start:04d}-{end:04d}{casename}-obs'.format(
                start=job.config.get('start_year'),
                end=job.config.get('end_year'),
                casename=job.config.get('test_casename'))
            head, _ = os.path.split(job.config.get('test_path_diag'))
            img_src = os.path.join(head, img_dir)
            self.setup_local_hosting(job, img_src)

            url = self._format_url(job)
            msg = '{job}-{start:04d}-{end:04d}: Hosted at {url}'.format(
                url=url, job=job.type, start=job.start_year, end=job.end_year)
            print_line(
                ui=self.ui,
                line=msg,
                event_list=self.event_list)
        elif job.type == 'e3sm_diags':
            img_src = job.config.get('results_dir')
            self.setup_local_hosting(job, img_src)
            url = self._format_url(job)
            msg = '{job}-{start:04d}-{end:04d}: Hosted at {url}'.format(
                url=url, job=job.type, start=job.start_year, end=job.end_year)
            print_line(
                ui=self.ui,
                line=msg,
                event_list=self.event_list)
    
    def _format_url(self, job):
        """
        Formats the hosted url for a completed diagnostic job
        
        Parameters:
            job (Job): the job to print the link for
        Returns:
            url (str): formatted url for the given job
        """
        if job.type == 'e3sm_diags':
            url = '{host_url}/viewer/index.html'.format(
            host_url=job.config['host_url'],
            prefix=self.url_prefix)
        else:
            url = '{host_url}/index.html'.format(
                host_url=job.config['host_url'],
                prefix=self.url_prefix)
        return url

    def setup_local_hosting(self, job, img_src):
        """
        Sets up the local directory for hosting diagnostic output
        """

        host_dir = job.config.get('web_dir')
        url = job.config.get('host_url')
        if os.path.exists(job.config.get('web_dir')):
            if not self._always_copy:
                return
            msg = '{job}-{start:04d}-{end:04d}: Removing previously hosted output'.format(
                job=job.type, start=job.start_year, end=job.end_year)
            print_line(
                ui=self.ui,
                line=msg,
                event_list=self.event_list,
                current_state=True)
            rmtree(job.config.get('web_dir'))
        msg = '{job}-{start:04d}-{end:04d}: Moving files for web hosting'.format(
            job=job.type, start=job.start_year, end=job.end_year)
        print_line(
            ui=self.ui,
            line=msg,
            event_list=self.event_list,
            current_state=True)
        if not os.path.exists(img_src):
            msg = '{job}-{start:04d}-{end:04d}: Hosting failed, no image source at {path}'.format(
                job=job.type, path=img_src, start=job.start_year, end=job.end_year)
            print_line(
                ui=self.ui,
                line=msg,
                event_list=self.event_list,
                current_state=True,
                ignore_text=False)
            logging.error(msg)
            return
        try:
            msg = 'Copying images from \n\t{src} to \n\t{dst}'.format(
                src=img_src, dst=host_dir)
            logging.info(msg)
            if os.path.exists(img_src) and not os.path.exists(host_dir):
                copytree(src=img_src, dst=host_dir)

            msg = 'Fixing permissions for {dir}'.format(
                dir=host_dir)
            print_line(
                ui=self.ui,
                line=msg,
                event_list=self.event_list,
                current_state=True,
                ignore_text=False)

            while True:
                try:
                    p = Popen(['chmod', '-R', '0755', host_dir])
                except:
                    sleep(1)
                else:
                    break
            out, err = p.communicate()
            head, _ = os.path.split(host_dir)
            os.chmod(head, 0755)
            head, _ = os.path.split(head)
            os.chmod(head, 0755)
        except Exception as e:
            from lib.util import print_debug
            print_debug(e)
            msg = 'Error copying {0} to host directory {1}'.format(
                job.type, host_dir)
            print_line(
                ui=self.ui,
                line=msg,
                event_list=self.event_list,
                current_state=True,
                ignore_text=False)
            return

    def is_all_done(self):
        """
        Check if all job_sets are done, and all processing has been completed

        return -1 if still running
        return 0 if a jobset failed
        return 1 if all complete
        """

        # First check for pending jobs
        #  if any of the sets havent finished yet, we must still be running
        for job_set in self.job_sets:
            if len(job_set.jobs) == 0:
                continue
            if job_set.status not in [SetStatus.COMPLETED, SetStatus.FAILED]:
                return -1
        # all job sets are either complete or failed
        for job_set in self.job_sets:
            if len(job_set.jobs) == 0:
                job_set.status == SetStatus.COMPLETED
            if job_set.status != SetStatus.COMPLETED:
                return 0
        return 1
