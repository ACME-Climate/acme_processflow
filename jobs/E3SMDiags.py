import os
import json
import logging

from bs4 import BeautifulSoup
from subprocess import Popen, PIPE
from pprint import pformat
from datetime import datetime
from shutil import copyfile

from lib.events import EventList
from lib.slurm import Slurm
from JobStatus import JobStatus, StatusMap
from lib.util import (render,
                      get_climo_output_files,
                      create_symlink_dir,
                      print_line)


class E3SMDiags(object):
    def __init__(self, config, event_list):
        self.event_list = event_list
        self.inputs = {
            'short_name': '',
            'account': '',
            'ui': '',
            'regrid_base_path': '',
            'regrid_output_path': '',
            'regrided_climo_path': '',
            'reference_data_path': '',
            'test_data_path': '',
            'test_name': '',
            # 'seasons': '',
            'backend': '',
            'sets': '',
            'results_dir': '',
            'template_path': '',
            'run_scripts_path': '',
            'start_year': '',
            'end_year': '',
            'year_set': '',
            'experiment': '',
            'web_dir': '',
            'host_url': '',
            'output_path': ''
        }
        self.start_time = None
        self.end_time = None
        self.output_path = None
        self.config = {}
        self._status = JobStatus.INVALID
        self.host_suffix = '/viewer/index.html'
        self._type = "e3sm_diags"
        self.year_set = config.get('year_set', 0)
        self.start_year = config['start_year']
        self.end_year = config['end_year']
        self.job_id = 0
        self.depends_on = ['ncclimo']
        self.messages = []
        self.prevalidate(config)

    def __str__(self):
        return json.dumps({
            'type': self.type,
            'config': self.config,
            'status': self.status,
            'depends_on': self.depends_on,
            'job_id': self.job_id,
            'messages': self.messages
        }, sort_keys=True, indent=4)

    def prevalidate(self, config):
        for key, val in config.items():
            if key in self.inputs:
                self.config[key] = val
                if key == 'sets':
                    if isinstance(val, int):
                        self.config[key] = [self.config[key]]
                    elif isinstance(val, str):
                        self.config[key] = [int(self.config[key])]

        valid = True
        for key, val in self.config.items():
            if key == 'account':
                continue
            if val == '':
                valid = False
                msg = '{0}: {1} is missing or empty'.format(key, val)
                self.messages.append(msg)
                break

        if not os.path.exists(self.config.get('run_scripts_path')):
            os.makedirs(self.config.get('run_scripts_path'))
        # if isinstance(self.config['seasons'], str):
        #     self.config['seasons'] = [self.config['seasons']]
        if self.year_set == 0:
            self.messages.append('invalid year_set')
            self.status = JobStatus.INVALID
        if valid:
            self.status = JobStatus.VALID
    
    def _check_links(self):
        viewer_path = os.path.join(self.config['results_dir'], 'viewer', 'index.html')
        viewer_head = os.path.join(self.config['results_dir'], 'viewer')
        missing_links = list()
        with open(viewer_path, 'r') as viewer_pointer:
            viewer_page = BeautifulSoup(viewer_pointer, 'lxml')
            viewer_links = viewer_page.findAll('a')
            for link in viewer_links:
                link_path = os.path.join(viewer_head, link.attrs['href'])
                if not os.path.exists(link_path):
                    missing_links.append(link_path)
                    continue
                if link_path[-4:] == 'html':
                    link_tail, _ = os.path.split(link_path)
                    with open(link_path, 'r') as link_pointer:
                        link_page = BeautifulSoup(link_pointer, 'lxml')
                        link_links = link_page.findAll('a')
                        for sublink in link_links:
                            try:
                                sublink_preview = sublink.attrs['data-preview']
                            except:
                                continue
                            else:
                                sublink_path = os.path.join(link_tail, sublink_preview)
                                if not os.path.exists(sublink_path):
                                    missing_links.append(sublink_path)
        if missing_links:
            msg = 'e3sm-{}-{}: missing the following links'.format(
                self.start_year, self.end_year)
            logging.error(msg)
            logging.error(missing_links)
            return False
        else:
            msg = 'e3sm-{}-{}: all links found'.format(
                self.start_year, self.end_year)
            logging.info(msg)
            return True

    def postvalidate(self):
        if not os.path.exists(self.config['results_dir']):
            msg = 'e3sm_diags-{start:04d}-{end:04d}: no results directory found'.format(
                start=self.start_year, end=self.end_year)
            logging.error(msg)
            return False
        contents = os.listdir(self.config['results_dir'])
        if 'viewer' not in contents:
            msg = 'e3sm_diags-{start:04d}-{end:04d}: no viewer in output directory'.format(
                start=self.start_year, end=self.end_year)
            logging.error(msg)
            return False
        viewer_path = os.path.join(self.config['results_dir'], 'viewer')
        contents = os.listdir(viewer_path)
        if 'index.html' not in contents:
            msg = 'e3sm_diags-{start:04d}-{end:04d}: no index.html found in output viewer at {path}'.format(
                start=self.start_year, end=self.end_year, path=viewer_path)
            logging.error(msg)
            return False

        return self._check_links()

    def execute(self):

        # Check if the output already exists
        if self.postvalidate():
            self.status = JobStatus.COMPLETED
            return 0

        # render the parameters file
        self.output_path = self.config['output_path']
        template_out = os.path.join(
            self.output_path,
            'params.py')
        variables = {
            'short_name': self.config['short_name'],
            'sets': self.config['sets'],
            'backend': self.config['backend'],
            'reference_data_path': self.config['reference_data_path'],
            'test_data_path': self.config['regrided_climo_path'],
            'test_name': self.config['test_name'],
            # 'seasons': self.config['seasons'],
            'results_dir': self.config['results_dir']
        }
        render(
            variables=variables,
            input_path=self.config.get('template_path'),
            output_path=template_out)

        run_name = '{type}_{start:04d}_{end:04d}'.format(
            start=self.config.get('start_year'),
            end=self.config.get('end_year'),
            type=self.type)
        template_copy = os.path.join(
            self.config.get('run_scripts_path'),
            run_name)
        copyfile(
            src=template_out,
            dst=template_copy)

        # setup sbatch script
        run_script = os.path.join(
            self.config.get('run_scripts_path'),
            run_name)
        if os.path.exists(run_script):
            os.remove(run_script)

        # Create directory of regridded climos
        file_list = get_climo_output_files(
            input_path=self.config['regrid_output_path'],
            start_year=self.start_year,
            end_year=self.end_year)
        variables = {
            'ACCOUNT': self.config.get('account', ''),
            'SRC_LIST': file_list,
            'SRC_DIR': self.config['regrid_output_path'],
            'DST': self.config['regrided_climo_path'],
            'CONSOLE_OUTPUT': '{}.out'.format(run_script),
            'PARAMS_PATH': template_out
        }
        resource_dir, _ = os.path.split(self.config.get('template_path'))
        submission_template_path = os.path.join(
            resource_dir, 'e3sm_diags_submission_template.sh')
        render(
            variables=variables,
            input_path=submission_template_path,
            output_path=run_script)

        slurm = Slurm()
        msg = 'Submitting to queue {type}: {start:04d}-{end:04d}'.format(
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
