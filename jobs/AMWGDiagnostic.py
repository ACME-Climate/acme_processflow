
import logging
import os
import re
import json

from subprocess import Popen, PIPE
from pprint import pformat
from time import sleep
from datetime import datetime
from shutil import copyfile
from bs4 import BeautifulSoup

from JobStatus import JobStatus, StatusMap
from lib.slurm import Slurm
from lib.events import EventList
from lib.util import (print_debug,
                      print_message,
                      create_symlink_dir,
                      render,
                      print_line,
                      get_climo_output_files)


class AMWGDiagnostic(object):
    """
    A job class to perform the NCAR AMWG Diagnostic
    """

    def __init__(self, config, event_list):
        """
        Setup class attributes

        inputs:
            test_casename: the name of the test case e.g. b40.20th.track1.2deg.001
            test_filetype: the filetype of the history files, either monthly_history or time_series
            test_path_history: path to the directory holding your history files
            test_path_climo: path to directory holding climo files
            test_path_diag: the output path for the diagnostics to go

        """
        self.event_list = event_list
        self._status = JobStatus.INVALID
        self.start_time = None
        self.end_time = None
        self.output_path = None
        self.year_set = config.get('year_set', 0)
        self.inputs = {
            'short_name': '',
            'account': '',
            'simulation_start_year': '',
            'ui': '',
            'web_dir': '',
            'host_url': '',
            'test_casename': '',
            'test_filetype': 'monthly_history',
            'test_path_history': '',
            'test_path_climo': '',
            'test_path_diag': '',
            'regrided_climo_path': '',
            'start_year': '',
            'end_year': '',
            'year_set': '',
            'run_directory': '',
            'template_path': '',
            'run_scripts_path': '',
            'output_path': '',
            'diag_home': '',
        }
        self._type = 'amwg'
        self.config = {}
        self.start_year = config['start_year']
        self.end_year = config['end_year']
        self.job_id = 0
        self.depends_on = ['ncclimo']
        self.host_suffix = '/index.html'
        self.prevalidate(config)

    def __str__(self):
        return json.dumps({
            'type': self.type,
            'config': self.config,
            'status': self.status,
            'depends_on': self.depends_on,
            'job_id': self.job_id,
        }, sort_keys=True, indent=4)

    def prevalidate(self, config):
        """
        Iterate over given config dictionary making sure all the inputs are set
        and rejecting any inputs that arent in the input dict
        """
        for key, value in config.iteritems():
            if key in self.inputs:
                self.config[key] = value
        for key, value in self.inputs.iteritems():
            if key not in self.config:
                self.config[key] = value

        if self.year_set == 0:
            self.status = JobStatus.INVALID
            return
        self.status = JobStatus.VALID

    def postvalidate(self):
        """
        Check that what the job was supposed to do actually happened
        returns 1 if the job is done, 0 otherwise
        """
        base = str(os.sep).join(
            self.config.get('test_path_diag').split(os.sep)[:-1])
        year_set = 'year_set_{0}'.format(
            self.config.get('year_set'))
        web_dir = '{base}/{start:04d}-{end:04d}{casename}-obs'.format(
            base=base,
            start=self.config.get('start_year'),
            end=self.config.get('end_year'),
            casename=self.config.get('test_casename'))

        return self._check_links()
    
    def _check_links(self):
        """
        Checks output page for all links, as well as first level subpages
        
        Parameters:
            None
        Returns:
            True if all links are found, False otherwise
        """
        missing_links = list()
        page_path = os.path.join(self.config['web_dir'], 'index.html')
        if not os.path.exists(page_path):
            msg = 'amwg-{}-{}: No output page found'.format(
                self.start_year, self.end_year)
            logging.error(msg)
            return False
        with open(page_path, 'r') as page_pointer:
            output_page = BeautifulSoup(page_pointer, 'lxml')
            output_links = output_page.findAll('a')
            for link in output_links:
                link_path = link.attrs['href']
                if link_path[-3:] == 'htm':
                    subpage_path = os.path.join(self.config['web_dir'], link.attrs['href'])
                    subpage_head, _ = os.path.split(subpage_path)
                    if not os.path.exists(subpage_path):
                        msg = 'amwg-{}-{}: No output page found'.format(
                            self.start_year, self.end_year)
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
                            sublink_path = os.path.join(subpage_head, sublink_href)
                            if not os.path.exists(sublink_path):
                                missing_links.append(sublink_path)
        if missing_links:
            msg = 'amwg-{start:04d}-{end:04d}: missing {len} links'.format(
                start=self.start_year, end=self.end_year, len=len(missing_links))
            print_line(
                ui=self.config.get('ui', False),
                line=msg,
                event_list=self.event_list)
            msg = 'amwg-{start:04d}-{end:04d}: missing the following links'.format(
                start=self.start_year, end=self.end_year)
            logging.error(msg)
            logging.error(missing_links)
            return False
        else:
            msg = 'amwg-{start:04d}-{end:04d}: all links found'.format(
                start=self.start_year, end=self.end_year)
            logging.info(msg)
            return True


    def execute(self):
        """
        Perform the actual work
        """
        # First check if the job has already been completed
        if self.postvalidate():
            self.status = JobStatus.COMPLETED
            return 0

        # Create directory of regridded climos
        regrid_path = self.config['regrided_climo_path']
        file_list = get_climo_output_files(
            input_path=regrid_path,
            start_year=self.start_year,
            end_year=self.end_year)
        if not file_list or len(file_list) == 0:
            msg = """
ERROR: AMWG: {start:04d}-{end:04d} could not find input climatologies at {path}\n
did you add ncclimo to this year_set?""".format(start=self.start_year,
                                                end=self.end_year,
                                                path=regrid_path)
            print_line(
                ui=self.config.get('ui', False),
                line=msg,
                event_list=self.event_list)
            self.status = JobStatus.FAILED
            return 0
        if not os.path.exists(self.config['test_path_climo']):
            msg = 'creating temp directory for amwg'
            print_line(
                ui=self.config.get('ui', False),
                line=msg,
                event_list=self.event_list,
                current_state=True)
            os.makedirs(self.config['test_path_climo'])

        # render the csh script into the output directory
        self.output_path = self.config['output_path']
        template_out = os.path.join(
            self.output_path,
            'amwg.csh')
        render(
            variables=self.config,
            input_path=self.config.get('template_path'),
            output_path=template_out)

        expected_name = '{type}_{start:04d}-{end:04d}'.format(
            start=self.config.get('start_year'),
            end=self.config.get('end_year'),
            type=self.type)
        # Copy the rendered run script into the scripts directory
        run_script_template_out = os.path.join(
            self.config.get('run_scripts_path'),
            expected_name)
        copyfile(
            src=template_out,
            dst=run_script_template_out)

        # setup sbatch script
        run_script = os.path.join(
            self.config.get('run_scripts_path'),
            expected_name)
        if os.path.exists(run_script):
            os.remove(run_script)

        variables = {
            'ACCOUNT': self.config.get('account', ''),
            'SRC_DIR': regrid_path,
            'SRC_LIST': file_list,
            'DST': self.config['test_path_climo'],
            'CONSOLE_OUT': '{}.out'.format(run_script),
            'RUN_AMWG_PATH': template_out
        }
        resource_dir, _ = os.path.split(self.config.get('template_path'))
        submission_template_path = os.path.join(
            resource_dir, 'amwg_submission_template.sh')
        render(
            variables=variables,
            input_path=submission_template_path,
            output_path=run_script)

        slurm = Slurm()
        msg = 'submitting to queue {type}: {start:04d}-{end:04d}'.format(
            type=self.type,
            start=self.start_year,
            end=self.end_year)
        print_line(
            ui=self.config.get('ui', False),
            line=msg,
            event_list=self.event_list,
            current_state=True)
        self.job_id = slurm.batch(run_script, '--oversubscribe')

        status = slurm.showjob(self.job_id)
        self.status = StatusMap[status.get('JobState')]

        return self.job_id

    @property
    def type(self):
        return self._type

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        self._status = status
