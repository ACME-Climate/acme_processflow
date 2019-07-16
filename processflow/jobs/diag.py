"""
A child of Job, the Diag class is the parent for all diagnostic jobs
"""
import json
import logging
import os
import sys

from distutils.dir_util import copy_tree
from shutil import rmtree
from subprocess import call

from processflow.jobs.job import Job
from processflow.lib.jobstatus import JobStatus
from processflow.lib.slurm import Slurm
from processflow.lib.util import print_line, print_message
from processflow.lib.util import create_symlink_dir, render
from processflow.lib.pbs import PBS


class Diag(Job):
    def __init__(self, *args, **kwargs):
        super(Diag, self).__init__(*args, **kwargs)
        self._host_url = ''
        self._short_comp_name = ""
        self._comparison = kwargs.get('comparison', 'obs')

        # setup the comparison name
        if self._comparison == 'obs':
            self._short_comp_name = 'obs'
        else:
            self._short_comp_name = kwargs['config']['simulations'][self.comparison]['short_name']
    # -----------------------------------------------

    @property
    def comparison(self):
        return self._comparison
    # -----------------------------------------------

    def __str__(self):
        return json.dumps({
            'type': self._job_type,
            'start_year': self._start_year,
            'end_year': self._end_year,
            'data_required': self._data_required,
            'depends_on': self._depends_on,
            'id': self._id,
            'comparison': self._comparison,
            'status': self._status.name,
            'case': self._case
        }, sort_keys=True, indent=4)
    # -----------------------------------------------

    def msg_prefix(self):
        return '{type}-{start:04d}-{end:04d}-{case}-vs-{comp}'.format(
            type=self.job_type,
            start=self.start_year,
            end=self.end_year,
            case=self.short_name,
            comp=self._short_comp_name)
    # -----------------------------------------------

    def setup_hosting(self, always_copy, img_source, host_path, event_list):
        """
        Performs file copys for images into the web hosting directory

        Parameters
        ----------
            always_copy (bool): if previous output exists in the target location, should the new output overwrite
            img_source (str): the path to where the images are coming from
            host_path (str): the path for where the images should be hosted
            event_list (EventList): an eventlist to push user notifications into
        """
        if always_copy:
            if os.path.exists(host_path):
                msg = '{prefix}: Removing previous output from host location'.format(
                    prefix=self.msg_prefix())
                print_line(msg, event_list, newline=False)
                rmtree(host_path)
                msg = '... complete'
                print msg

        if not os.path.exists(host_path):
            msg = '{prefix}: Moving files for web hosting'.format(
                prefix=self.msg_prefix())
            print_line(msg, event_list, newline=False)
            copy_tree(
                src=img_source,
                dst=host_path)
            msg = '... complete'
            print msg
            # fix permissions for apache
            msg = '{prefix}: Fixing permissions'.format(
                prefix=self.msg_prefix())
            print_line(msg, event_list, newline=False)
            call(['chmod', '-R', 'go+rx', host_path])
            tail, _ = os.path.split(host_path)
            for _ in range(2):
                call(['chmod', 'go+rx', tail])
                tail, _ = os.path.split(tail)
            msg = '... complete'
            print msg
        else:
            msg = '{prefix}: Files already present at host location, skipping'.format(
                prefix=self.msg_prefix())
            print_line(msg, event_list)

    # -----------------------------------------------

    def get_report_string(self):
        """
        Returns a nice report string of job status information
        """
        if self._dryrun:
            return '{prefix} :: {status} :: Dry run mode, no output generated'.format(
                prefix=self.msg_prefix(),
                status=self.status.name)

        # if the job failed or img hosting is turned off, report the status and a path to the jobs console output
        if self.status != JobStatus.COMPLETED or not self._host_url:
            return '{prefix} :: {status} :: {console_path}'.format(
                prefix=self.msg_prefix(),
                status=self.status.name,
                console_path=self._console_output_path)
        # otherwise report the status and give a url to view the output
        else:
            return '{prefix} :: {status} :: {url}'.format(
                prefix=self.msg_prefix(),
                status=self.status.name,
                url=self._host_url)
    # -----------------------------------------------

    def setup_temp_path(self, config, *args, **kwards):
        """
        creates the default temp path for diagnostics
        /project/output/temp/case_short_name/job_type/start_end_vs_comparison
        """
        if self._comparison == 'obs':
            comp = 'obs'
        else:
            comp = config['simulations'][self.comparison]['short_name']

        temp_path = os.path.join(
            config['global']['project_path'],
            'output', 'temp', self._short_name, self._job_type,
            '{:04d}_{:04d}_vs_{}'.format(self._start_year, self._end_year, comp))
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)
        return temp_path
    # -----------------------------------------------

    def get_run_name(self):
        return '{type}_{start:04d}_{end:04d}_{case}_vs_{comp}'.format(
            type=self.job_type,
            run_type=self._run_type,
            start=self.start_year,
            end=self.end_year,
            case=self.short_name,
            comp=self._short_comp_name)

    # -----------------------------------------------

    def setup_data(self, config, filemanager, case):
        """
        symlinks all data_types sepecified in the jobs _data_required field,
        and puts a copy of the path for the links into the _input_file_paths field
        """

        # create the path to where we should place our temp symlinks
        self._input_base_path = self.setup_temp_path(
            config=config)

        for datatype in self._data_required:
            datainfo = config['data_types'].get(datatype)
            if not datainfo:
                print "ERROR: Unable to find config information for {}".format(
                    datatype)
                sys.exit(1)
            monthly = datainfo.get('monthly')
            # first get the list of file paths to the data
            if monthly == 'True' or monthly == True:
                files = filemanager.get_file_paths_by_year(
                    datatype=datatype,
                    case=case,
                    start_year=self._start_year,
                    end_year=self._end_year)
            else:
                files = filemanager.get_file_paths_by_year(
                    datatype=datatype,
                    case=case)
            if not files or len(files) == 0:
                msg = '{prefix}: filemanager cant find input files for datatype {datatype}'.format(
                    prefix=self.msg_prefix(),
                    datatype=datatype)
                logging.error(msg)
                continue

            # extract the file names
            filesnames = list()
            for file in files:
                tail, head = os.path.split(file)
                filesnames.append(head)

            # keep a reference to the input data for later
            self._input_file_paths.extend(
                [os.path.join(self._input_base_path, x) for x in filesnames])

            # create the symlinks
            create_symlink_dir(
                src_dir=tail,
                src_list=filesnames,
                dst=self._input_base_path)

        return
    # -----------------------------------------------

    def _submit_cmd_to_manager(self, config, cmd, event_list):
        """
        Takes the jobs main cmd, generates a batch script and submits the script
        to the resource manager controller

        Parameters:
            cmd (str): the command to submit
            config (dict): the global configuration object
        Retuns:
            job_id (int): the job_id from the resource manager
        """
        # setup for the run script
        scripts_path = os.path.join(
            config['global']['project_path'],
            'output', 'scripts')
        if self._run_type is not None:
            run_name = '{type}_{run_type}_{start:04d}_{end:04d}_{case}'.format(
                type=self.job_type,
                run_type=self._run_type,
                start=self.start_year,
                end=self.end_year,
                case=self.short_name)
        else:
            run_name = '{type}_{start:04d}_{end:04d}_{case}_vs_{comp}'.format(
                type=self.job_type,
                run_type=self._run_type,
                start=self.start_year,
                end=self.end_year,
                case=self.short_name,
                comp=self._short_comp_name)

        run_script = os.path.join(scripts_path, run_name)
        self._console_output_path = '{}.out'.format(run_script)
        if os.path.exists(run_script):
            os.remove(run_script)

        # generate the run script using the manager arguments and command
        command = ' '.join(cmd)
        script_prefix = ''

        if isinstance(self._manager, Slurm):
            margs = self._manager_args['slurm']
            margs.append(
                '-o {}'.format(self._console_output_path))
            manager_prefix = '#SBATCH'
            for item in margs:
                script_prefix += '{prefix} {value}\n'.format(
                    prefix=manager_prefix,
                    value=item)
        elif isinstance(self._manager, PBS):
            margs = self._manager_args['pbs']
            margs.append(
                '-o {}'.format(self._console_output_path))
            margs.append(
                '-e {}'.format(self._console_output_path.replace('.out', '.err')))
            manager_prefix = '#PBS'
            for item in margs:
                script_prefix += '{prefix} {value}\n'.format(
                    prefix=manager_prefix,
                    value=item)

        with open(run_script, 'w') as batchfile:
            batchfile.write('#!/bin/bash\n')
            batchfile.write(script_prefix)

        if config['global'].get('native_env'):
            template_input_path = os.path.join(
                config['global']['resource_path'],
                'env_loader_lite.bash')
        else:
            template_input_path = os.path.join(
                config['global']['resource_path'],
                'env_loader.bash')
        variables = {
            'user_env_path': os.environ['CONDA_PREFIX'],
            'cmd': command
        }
        render(
            variables=variables,
            input_path=template_input_path,
            output_path=run_script)

        # if this is a dry run, set the status and exit
        if self._dryrun:
            msg = '{}: dryrun is set, completing without running'.format(
                self.msg_prefix())
            logging.info(msg)
            print_message(msg, 'ok')
            self.status = JobStatus.COMPLETED
            return False

        msg = '{}: Job ready, submitting to queue'.format(
            self.msg_prefix())
        print_message(msg, 'ok')

        # submit the run script to the resource controller
        self._job_id = self._manager.batch(run_script)
        self._has_been_executed = True
        return self._job_id
    # -----------------------------------------------
