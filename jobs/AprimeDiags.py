import os
import sys
import logging
import time
import re

from pprint import pformat
from time import sleep
from datetime import datetime
from shutil import copyfile

from lib.util import render
from lib.util import print_debug
from lib.events import Event_list
from lib.slurm import Slurm
from JobStatus import JobStatus, StatusMap


class AprimeDiags(object):
    def __init__(self, config, event_list):
        """
        Setup class attributes
        """
        self.event_list = event_list
        self.inputs = {
            'web_dir': '',
            'host_url': '',
            'experiment': '',
            'run_scripts_path': '',
            'year_set': '',
            'input_path': '',
            'start_year': '',
            'end_year': '',
            'output_path': '',
            'template_path': '',
            'test_atm_res': '',
            'test_mpas_mesh_name': '',
            'aprime_code_path': ''
        }
        self.slurm_args = {
            'num_cores': '-n 16',  # 16 cores
            'run_time': '-t 0-02:00',  # 1 hour run time
            'num_machines': '-N 1',  # run on one machine
            'oversubscribe': '--oversubscribe'
        }
        self.start_time = None
        self.end_time = None
        self.output_path = None
        self.config = {}
        self.status = JobStatus.INVALID
        self._type = 'aprime_diags'
        self.year_set = config.get('yearset', 0)
        self.start_year = config['start_year']
        self.end_year = config['end_year']
        self.job_id = 0
        self.depends_on = []
        self.prevalidate(config)

    def __str__(self):
        return pformat({
            'type': self.type,
            'config': self.config,
            'status': self.status,
            'depends_on': self.depends_on,
            'job_id': self.job_id,
            'year_set': self.year_set
        })

    @property
    def type(self):
        return self._type

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        self._status = status

    def prevalidate(self, config):
        """
        Create input and output directories
        """
        self.config = config
        self.status = JobStatus.VALID

        if not os.path.exists(self.config.get('run_scripts_path')):
            os.makedirs(self.config.get('run_scripts_path'))

        set_string = '{start:04d}-{end:04d}'.format(
            start=self.start_year,
            end=self.end_year)

        if self.year_set == 0:
            self.status = JobStatus.INVALID

    def postvalidate(self):
        """
        Check that what the job was supposed to do actually happened
        returns 1 if the job is done, 0 otherwise
        """
        # find the directory generated by coupled diags
        output_path = self.config.get('output_base_dir')
        if not os.path.exists(output_path):
            return False
        try:
            output_contents = os.listdir(output_path)
        except IOError:
            return False
        if not output_contents:
            return False
        output_directory = None
        for item in output_contents:
            if item.split('-')[-1] == 'obs':
                output_directory = item
        if not output_directory:
            return False
        output_directory = os.path.join(output_path, output_directory)
        if os.path.exists(output_directory):
            contents = os.listdir(output_directory)
            target_output = 35
            return bool(len(contents) >= target_output)
        else:
            return False

    def setup_input_directory(self, filemanager):

        for datatype in ['atm', 'ocn', 'ice', 'streams.ocean', 'streams.cice', 'rest']:
            input_files = filemanager.get_file_paths_by_year(
                start_year=self.start_year,
                end_year=self.end_year,
                _type=datatype)
            for file in input_files:
                head, tail = os.path.split(file)
                os.symlink(
                    src=file,
                    dst=os.path.join(self.config['input_path'], tail))

    def execute(self, dryrun=False):
        """
        Perform the actual work
        """
        # First check if the job has already been completed
        if self.postvalidate():
            self.status = JobStatus.COMPLETED
            message = 'Coupled_diag job already computed, skipping'
            self.event_list.push(message=message)
            return 0

        self.output_path = self.config['output_path']
        # create symlinks to the input data
        setup_status = self.setup_input_directory()
        sys.exit()
        if not setup_status:
            return -1
        elif setup_status == 2:
            return False

        # Setup output directory
        output_path = os.path.join(
            self.config['output_base_path'],
            'aprime',
            set_string)
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        self.config['output_path'] = output_path
        # Setup temp directory
        tmp_path = os.path.join(
            self.config['output_base_path'],
            'tmp', 'aprime',
            set_string)
        if not os.path.exists(tmp_path):
            os.makedirs(tmp_path)
        self.config['tmp_path'] = tmp_path

        # render the run_AIMS.csh script
        template_out = self.config.get('rendered_output_path')
        render(
            variables=self.config,
            input_path=self.config.get('coupled_template_path'),
            output_path=template_out,
            delimiter='%%')
        run_script_template_out = os.path.join(
            self.config.get('run_scripts_path'), 'coupled_diag_{0}-{1}.csh'.format(
                self.config.get('start_year'),
                self.config.get('end_year')))
        copyfile(
            src=template_out,
            dst=run_script_template_out)

        cmd = 'csh {run_AIMS}'.format(
            run_AIMS=self.config.get('rendered_output_path'))

        expected_name = 'coupled_diag_set_{set}_{start}_{end}'.format(
            set=self.config.get('year_set'),
            start='{:04d}'.format(self.config.get('test_begin_yr_climo')),
            end='{:04d}'.format(self.config.get('test_end_yr_climo')))

        run_script = os.path.join(self.config.get(
            'run_scripts_path'), expected_name)
        if os.path.exists(run_script):
            os.remove(run_script)

        self.slurm_args['out_file'] = '-o {out}'.format(
            out=run_script + '.out')
        self.slurm_args['working_dir'] = '--workdir {dir}'.format(
            dir=self.config.get('coupled_diags_home'))
        slurm_args = ['#SBATCH {}'.format(
            self.slurm_args[s]) for s in self.slurm_args]
        slurm_prefix = '\n'.join(slurm_args) + '\n'

        with open(run_script, 'w') as batchfile:
            batchfile.write('#!/bin/bash\n')
            batchfile.write(slurm_prefix)
            batchfile.write(cmd)

        slurm = Slurm()
        print 'submitting to queue {type}: {start:04d}-{end:04d}'.format(
            type=self.type,
            start=self.start_year,
            end=self.end_year)
        self.job_id = slurm.batch(run_script, '--oversubscribe')
        status = slurm.showjob(self.job_id)
        self.status = StatusMap[status.get('JobState')]
        message = "## {job} id: {id} changed status to {status}".format(
            job=self.type,
            id=self.job_id,
            status=self.status)
        logging.info(message)

        return self.job_id
