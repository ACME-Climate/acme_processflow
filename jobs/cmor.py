import os
import re
import logging

from jobs.job import Job
from lib.util import render, print_line
from lib.jobstatus import JobStatus
from lib.filemanager import FileStatus


class Cmor(Job):
    """
    CMORize e3sm model output
    """

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
            config (dict): the global configuration object
        """
        super(Cmor, self).__init__(*args, **kwargs)
        self._job_type = 'cmor'
        self._requires = 'timeseries'
        self._data_required = ['ts_regrid']

        custom_args = kwargs['config']['post-processing'][self.job_type].get(
            'custom_args')
        if custom_args:
            self.set_custom_args(custom_args)

        # setup the output directory, creating it if it doesnt already exist
        custom_output_path = kwargs['config']['post-processing'][self.job_type].get(
            'custom_output_path')
        if custom_output_path:
            self._output_path = self.setup_output_directory(custom_output_path)
        else:
            self._output_path = os.path.join(
                kwargs['config']['global']['project_path'],
                'output',
                'pp',
                'cmor',
                self.short_name,
                self.job_type,
                '{start:04d}_{end:04d}'.format(
                    start=self.start_year,
                    end=self.end_year))
        if not os.path.exists(self._output_path):
            os.makedirs(self._output_path)
    # -----------------------------------------------

    def _dep_filter(self, job):
        if job.job_type != self._requires:
            return False
        if job.start_year != self.start_year:
            return False
        if job.end_year != self.end_year:
            return False
        return True
    # -----------------------------------------------

    def postvalidate(self, config, *args, **kwargs):
        """
        Validate that the CMOR job completed successfully

        Parameters
        ----------
            config (dict) the global config object
        Returns
        -------
            True if the job completed successfully
            False otherwise
        """
        found = list()
        for root, dirs, files in os.walk(self._output_path):
            if files is not None:
                for file in files:
                    if file.endswith('log') or file.endswith('json'):
                        continue
                    found.append(file)
        if config['post-processing']['cmor']['variable_list'] == 'all':
            expected_file_number = 20
        else:
            expected_file_number = len(config['post-processing']['cmor']['variable_list'])
        if len(found) >= expected_file_number:
            return True
        else:
            return False
    # -----------------------------------------------

    def setup_dependencies(self, *args, **kwargs):
        """
        CMOR requires timeseries output
        """
        for job in kwargs['jobs']:
            if job.job_type == self._requires \
                and job.start_year == self.start_year \
                    and job.end_year == self.end_year:
                        self.depends_on.append(job.id)
        if not self.depends_on:
            msg = 'Unable to find timeseries for {}, does this case generate timeseries?'.format(
                self.msg_prefix())
            raise Exception(msg)
    # -----------------------------------------------

    def execute(self, config, event_list, dryrun=False):
        """
        Execute the CMOR job

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

        input_path, _ = os.path.split(self._input_file_paths[0])
        cmd = [
            'e3sm_to_cmip',
            '--input', input_path,
            '--output', self._output_path,
            '--var-list', ' '.join(config['post-processing']
                                   ['cmor']['variable_list']),
            '--user-input', config['post-processing']['cmor'][self.case]['user_input_json_path'],
            '--tables', config['post-processing']['cmor']['cmor_tables_path'],
            '--num-proc', '24'
        ]
        custom_handlers = config['post-processing']['cmor'].get(
            'custom_handlers_path')
        if custom_handlers is not None:
            cmd.extend(['--handlers', custom_handlers])

        self._has_been_executed = True
        return self._submit_cmd_to_manager(config, cmd, event_list)
    # -----------------------------------------------

    def handle_completion(self, filemanager, event_list, config, *args, **kwargs):
        """
        Adds the output from cmor into the filemanager database as type 'cmorized'

        Paremeters
        ----------
            filemanager (FileManager): the manager to add files to
            event_list (EventList): an EventList to add notification messages to
            config (dict): the global config object
        Returns
        -------
            True if files added correctly
            False if there was any error
        """
        try:
            new_files = list()
            for root, dirs, files in os.walk(self._output_path):
                if files is not None:
                    for file in files:
                        new_files.append({
                            'name': file,
                            'local_path': os.path.abspath(file),
                            'case': self.case,
                            'year': self.start_year,
                            'month': self.end_year,  # use the month to hold the end year field
                            'local_status': FileStatus.PRESENT.value
                        })
            filemanager.add_files(
                data_type='cmorized',
                file_list=new_files,
                super_type='derived')
            filemanager.write_database()
            msg = '{prefix}: Job completion handler done'.format(
                prefix=self.msg_prefix())
            print_line(msg, event_list)
            logging.info(msg)
            return True
        except Exception as e:
            raise e
        return False
    # -----------------------------------------------
