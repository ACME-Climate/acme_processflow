"""
A python wrapper around the AMWG diagnostics
"""
import os
import re
import logging

from subprocess import call
from bs4 import BeautifulSoup

from jobs.diag import Diag
from lib.util import render, print_line
from lib.jobstatus import JobStatus


class AMWG(Diag):
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
            config (dict): the global configuration object
            custom_args (dict): a dictionary of user supplied arguments
                to pass to the resource manager
        """
        super(AMWG, self).__init__(*args, **kwargs)
        self._job_type = 'amwg'
        self._requires = 'climo'
        self._data_required = ['climo_regrid']
        self._host_path = ''
        self._short_comp_name = ''
        custom_args = kwargs['config']['diags']['amwg'].get('custom_args')
        if custom_args:
            self.set_custom_args(custom_args)
        if self.comparison == 'obs':
            self._short_comp_name = 'obs'
        else:
            self._short_comp_name = kwargs['config']['simulations'][self.comparison]['short_name']
    # -----------------------------------------------

    def _dep_filter(self, job):
        """
        find the climo job we're waiting for, assuming there's only
        one climo job in this case with the same start and end years
        """
        if job.job_type != self._requires:
            return False
        if job.start_year != self.start_year:
            return False
        if job.end_year != self.end_year:
            return False
        return True
    # -----------------------------------------------

    def setup_dependencies(self, *args, **kwargs):
        """
        AMWG requires climos
        """
        jobs = kwargs['jobs']
        if self.comparison != 'obs':
            other_jobs = kwargs['comparison_jobs']
            try:
                self_climo, = [job for job in jobs if self._dep_filter(job)]
            except ValueError:
                msg = 'Unable to find climo for {}, is this case set to generate climos?'.format(
                    self.msg_prefix())
                raise Exception(msg)
            try:
                comparison_climo, = [job for job in other_jobs if self._dep_filter(job)]
            except ValueError:
                msg = 'Unable to find climo for {}, is that case set to generates climos?'.format(
                    self.comparison)
                raise Exception(msg)
            self.depends_on.extend((self_climo.id, comparison_climo.id))
        else:
            try:
                self_climo, = [job for job in jobs if self._dep_filter(job)]
            except ValueError:
                msg = 'Unable to find climo for {}, is this case set to generate climos?'.format(
                    self.msg_prefix())
                raise Exception(msg)
            self.depends_on.append(self_climo.id)
    # -----------------------------------------------

    def execute(self, config, event_list, custom_args=None, dryrun=False):
        """
        Execute the AMWG job

        Parameters
        ----------
            config (dict): the global config object
            event_list (EventList): an EventList to push notifications into
            dryrun (bool): if true this job will generate all scripts,
                setup data, and exit without submitting the job
        Returns
        -------
            True if the job has already been executed
            False if the job cannot be executed
            jobid (str): the resource managers assigned job id
                if the job was submitted to the resource manager
        """
        self._dryrun = dryrun

        # setup the output directory, creating it if it doesnt already exist
        self._output_path = os.path.join(
            config['global']['project_path'],
            'output', 'diags', self.short_name, 'amwg',
            '{start:04d}_{end:04d}_vs_{comp}'.format(
                start=self.start_year,
                end=self.end_year,
                comp=self._short_comp_name))
        if not os.path.exists(self._output_path):
            os.makedirs(self._output_path)

        # setup template
        csh_template_out = os.path.join(
            config['global']['run_scripts_path'],
            'amwg_{start:04d}_{end:04d}_{case}_vs_{comp}.csh'.format(
                start=self.start_year,
                end=self.end_year,
                case=self.short_name,
                comp=self._short_comp_name))
        variables = dict()
        input_path, _ = os.path.split(self._input_file_paths[0])
        variables['test_casename'] = self.case
        variables['short_name'] = self.short_name
        variables['test_path_history'] = input_path + os.sep
        variables['test_path_climo'] = input_path + os.sep
        variables['test_path_diag'] = self._output_path + os.sep
        variables['diag_home'] = config['diags']['amwg']['diag_home']

        if 'all' in config['diags']['amwg']['sets']:
            variables['all_sets'] = '0'
            set_names = ['set_' + str(x) for x in range(1, 16)] + ['set_4a']
            for diag in set_names:
                variables[diag] = '0'
        else:
            variables['all_sets'] = '1'
            set_numbers = [str(x) for x in range(1, 17)] + ['4a']
            set_names = ['set_' + str(x) for x in range(1, 16)] + ['set_4a']
            for idx, diag in enumerate(set_names):
                variables[diag] = '0' if set_numbers[idx] in config['diags']['amwg']['sets'] else '1'

        if self.comparison == 'obs':
            template_input_path = os.path.join(
                config['global']['resource_path'],
                'amwg_template_vs_obs.csh')
        else:
            template_input_path = os.path.join(
                config['global']['resource_path'],
                'amwg_template_vs_model.csh')
            variables['cntl_casename'] = self.comparison
            variables['cntl_short_name'] = self._short_comp_name
            variables['cntl_path_history'] = input_path + os.sep
            variables['cntl_path_climo'] = input_path + os.sep

        # get environment path to use as NCARG_ROOT
        variables['NCARG_ROOT'] = os.environ['CONDA_PREFIX']

        render(
            variables=variables,
            input_path=template_input_path,
            output_path=csh_template_out)

        # change input file names to match what amwg expects
        self._change_input_file_names()

        # create the run command and submit it
        self._has_been_executed = True
        cmd = ['csh', csh_template_out]
        return self._submit_cmd_to_manager(config, cmd)
    # -----------------------------------------------

    def postvalidate(self, config, *args, **kwargs):
        """
        Validates that the job ran correctly

        Parameters
        ----------
            config (dict): the global config object
        Returns
        -------
            True if the job ran successfully
            False if there is missong output
        """
        if not self._output_path:
            self._output_path = os.path.join(
                config['global']['project_path'],
                'output', 'diags', self.short_name, 'amwg',
                '{start:04d}_{end:04d}_vs_{comp}'.format(
                    start=self.start_year,
                    end=self.end_year,
                    comp=self._short_comp_name))
        if not self._host_path:
            if config['global']['host']:
                self._host_path = os.path.join(
                    config['img_hosting']['host_directory'],
                    self.case,
                    'amwg',
                    '{start:04d}_{end:04d}_vs_{comp}'.format(
                        start=self.start_year,
                        end=self.end_year,
                        comp=self._short_comp_name))

        if self.comparison == 'obs':
            expected_files = {
                "set4": 50,
                "set5_6": 100,
                "set7": 100,
                "set1": 10,
                "set2": 3,
                "set3": 100,
                "set8": 20,
                "set9": 20,
                "set16": 3,
                "set14": 10,
                "set15": 50,
                "set12": 50,
                "set13": 100,
                "set10": 100,
                "set11": 10,
                "set4a": 50
            }
        else:
            expected_files = {
                "set4": 60,
                "set5_6": 100,
                "set7": 100,
                "set1": 10,
                "set2": 5,
                "set3": 100,
                "set8": 20,
                "set9": 5,
                "set16": 3,
                "set14": 10,
                "set15": 50,
                "set12": 50,
                "set13": 300,
                "set10": 50,
                "set11": 10,
                "set4a": 20
            }

        passed = True
        if 'all' in config['diags']['amwg']['sets']:
            sets = [str(x) for x in range(1, 16)] + ['4a']
        else:
            sets = config['diags']['amwg']['sets']

        img_source = os.path.join(
            self._output_path,
            '{case}-vs-{comp}'.format(
                case=self.short_name,
                comp=self._short_comp_name))
        img_source_tar = img_source + '.tar'
        # check that there have been enough plots created to call this a successful run
        for item in sets:
            if item == 'all':
                continue
            setname = 'set5_6' if item == '6' or item == '5' else 'set' + item
            directory = os.path.join(
                self._output_path,
                '{}-vs-{}'.format(self.short_name, self._short_comp_name),
                setname)
            if not os.path.exists(directory):
                if not self._has_been_executed:
                    return False
                msg = '{prefix}: could not find output directory {dir}'.format(
                    prefix=self.msg_prefix(),
                    dir=directory)
                logging.error(msg)
            else:
                count = len(os.listdir(directory))
                if count < expected_files[setname]:
                    if not self._has_been_executed:
                        return False
                    msg = '{prefix}: set {set} only produced {numProduced} when {numExpected} were expected'.format(
                        prefix=self.msg_prefix(),
                        set=setname,
                        numProduced=count,
                        numExpected=expected_files[setname])
                    logging.error(msg)
                    passed = False

        if not passed:
            if os.path.exists(img_source_tar):
                msg = '{prefix}: extracting images from tar archive'.format(
                    prefix=self.msg_prefix())
                print_line(msg, kwargs['event_list'])
                call(['tar', '-xf', img_source_tar,
                      '--directory', self._output_path])
                passed = True
                for item in config['diags']['amwg']['sets']:
                    if item == 'all':
                        continue
                    setname = 'set5_6' if item == '6' or item == '5' else 'set' + item
                    directory = os.path.join(
                        self._output_path,
                        '{}-vs-{}'.format(self.short_name,
                                          self._short_comp_name),
                        setname)
                    if not os.path.exists(directory):
                        passed = False
                        if self._has_been_executed:
                            msg = '{prefix}: could not find output directory after inflating tar archive: {dir}'.format(
                                prefix=self.msg_prefix(),
                                dir=directory)
                            logging.error(msg)
                            print_line(msg, kwargs['event_list'])
                    else:
                        count = len(os.listdir(directory))
                        if count < expected_files[setname]:
                            msg = '{prefix}: set {set} only produced {numProduced} when {numExpected} were expected'.format(
                                prefix=self.msg_prefix(),
                                set=setname,
                                numProduced=count,
                                numExpected=expected_files[setname])
                            logging.error(msg)
                            print_line(msg, kwargs['event_list'])
                            passed = False

        if passed:
            msg = '{prefix}: all expected output images found'.format(
                prefix=self.msg_prefix())
            print_line(msg, kwargs['event_list'])
            logging.info(msg)
            self._check_links(config)
            return True
        else:
            return False
    # -----------------------------------------------
    def handle_completion(self, filemanager, event_list, config, *args, **kwargs):
        """
        Sets up variables needed to web hosting

        Parameters
        ----------
            event_list (EventList): an EventList to push user notifications into
            config (dict): the global config object
        """
        if self.status == JobStatus.COMPLETED:
            msg = '{prefix}: Job complete'.format(
                prefix=self.msg_prefix())
        else:
            msg = '{prefix}: Job failed'.format(
                prefix=self.msg_prefix())
        print_line(msg, event_list)
        logging.info(msg)

        # if hosting is turned off, simply return
        if not config['global']['host']:
            return

        img_source = os.path.join(
            self._output_path,
            '{case}-vs-{comp}'.format(
                case=self.short_name,
                comp=self._short_comp_name))

        # setup the web hosting
        self._host_path = os.path.join(
            config['img_hosting']['host_directory'],
            self.short_name,
            'amwg',
            '{start:04d}_{end:04d}_vs_{comp}'.format(
                start=self.start_year,
                end=self.end_year,
                comp=self._short_comp_name))

        if not os.path.exists(img_source):
            if os.path.exists(img_source + '.tar'):
                call(['tar', '-xf', img_source + '.tar',
                      '--directory', self._output_path])
            else:
                msg = '{prefix}: Unable to find output directory or tar archive'.format(
                    prefix=self.msg_prefix())
                print_line(msg, event_list)
                self.status = JobStatus.FAILED
                logging.info(msg)
                return
        self.setup_hosting(config['global']['always_copy'], img_source, self._host_path, event_list)

        self._host_url = 'https://{server}/{prefix}/{case}/amwg/{start:04d}_{end:04d}_vs_{comp}/index.html'.format(
            server=config['img_hosting']['img_host_server'],
            prefix=config['img_hosting']['url_prefix'],
            case=self.short_name,
            start=self.start_year,
            end=self.end_year,
            comp=self._short_comp_name)
    # -----------------------------------------------

    def _check_links(self, config):
        """
        Checks output page for all links, as well as first level subpages

        Parameters:
            None
        Returns:
            True if all links are found, False otherwise
        """
        self._output_path = os.path.join(
            config['global']['project_path'],
            'output', 'diags', self.short_name, 'amwg',
            '{start:04d}_{end:04d}_vs_{comp}'.format(
                start=self.start_year,
                end=self.end_year,
                comp=self._short_comp_name))
        missing_links = list()
        page_path = os.path.join(
            self._output_path,
            '{case}-vs-{comp}'.format(case=self.short_name,
                                      comp=self._short_comp_name),
            'index.html')
        page_tail, page_head = os.path.split(page_path)
        if not os.path.exists(page_path):
            msg = '{prefix}: No output page found'.format(
                prefix=self.msg_prefix())
            logging.error(msg)
            return False

        # read in the base output page and parse it
        with open(page_path, 'r') as page_pointer:
            output_page = BeautifulSoup(page_pointer, 'lxml')
            output_links = output_page.findAll('a')

        # iterate over all the links on the page
        missing_subpage_links = None
        for link in output_links:
            link_path = link.attrs['href']
            if link_path[-3:] == 'htm':
                subpage_path = os.path.join(page_tail, link.attrs['href'])
                subpage_tail, subpage_head = os.path.split(subpage_path)
                missing_subpage_links = list()
                if not os.path.exists(subpage_path):
                    link.replace_with_children()
                    msg = '{prefix}: web page missing {page}'.format(
                        prefix=self.msg_prefix(),
                        page=subpage_head)
                    logging.error(msg)
                    missing_links.append(subpage_path)
                    continue
                with open(subpage_path, 'r') as subpage_pointer:
                    subpage = BeautifulSoup(subpage_pointer, 'lxml')
                    subpage_links = subpage.findAll('a')
                for sublink in subpage_links:
                    sublink_href = sublink.attrs['href']
                    if sublink_href[-3:] != 'png':
                        continue
                    sublink_path = os.path.join(subpage_tail, sublink_href)
                    if not os.path.exists(sublink_path):
                        sublink.replace_with_children()
                        missing_subpage_links.append(sublink_path)
                if missing_subpage_links:
                    os.rename(subpage_path, subpage_path + '.bak')
                    with open(subpage_path, 'w') as outfile:
                        outfile.write(str(subpage))
            if missing_subpage_links:
                missing_links.extend(missing_subpage_links)
        if missing_links:
            os.rename(page_path, page_path + '.bak')
            with open(page_path, 'w') as outfile:
                outfile.write(str(output_page))
            return True
        else:
            msg = '{prefix}: all links found'.format(
                prefix=self.msg_prefix())
            logging.info(msg)
            return True
    # -----------------------------------------------

    def _change_input_file_names(self):
        """
        change case_01_000101_000201_climo.nc to
               case_01_climo.nc
        """
        input_path, _ = os.path.split(self._input_file_paths[0])
        pattern = r'\d{6}_\d{6}_'
        for file in self._input_file_paths:
            _, filename = os.path.split(file)
            index = re.search(pattern, filename).start()
            os.rename(file, os.path.join(
                input_path, filename[:index] + 'climo.nc'))
    # -----------------------------------------------
