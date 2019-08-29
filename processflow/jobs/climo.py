"""
A wrapper for ncclimo climatology generation
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import logging
import os

from processflow.jobs.job import Job
from processflow.lib.jobstatus import JobStatus
from processflow.lib.util import get_climo_output_files, print_line
from processflow.lib.filemanager import FileStatus


class Climo(Job):
    def __init__(self, *args, **kwargs):
        super(Climo, self).__init__(*args, **kwargs)
        self._job_type = 'climo'
        self._data_required = ['atm']
        self._dryrun = True if kwargs.get('dryrun') == True else False
        self._regrid_path = ""

        custom_args = kwargs['config']['post-processing'][self.job_type].get(
            'custom_args')
        if custom_args:
            self.set_custom_args(custom_args)

        # setup the output directory, creating it if it doesnt already exist
        custom_output_path = kwargs['config']['post-processing'][self.job_type].get(
            'custom_output_path')
        if custom_output_path:
            self._output_path = self.setup_output_directory(custom_output_path)
            self._regrid_path = self._output_path
        else:
            self._output_path = os.path.join(
                kwargs['config']['global']['project_path'],
                'output',
                'pp',
                'climos_native',
                kwargs['config']['simulations'][self.case]['native_grid_name'],
                self._short_name,
                '{length}yr'.format(length=self.end_year - self.start_year + 1))
            self._regrid_path = os.path.join(
                kwargs['config']['global']['project_path'],
                'output',
                'pp',
                'climos_regrid',
                kwargs['config']['post-processing']['climo']['destination_grid_name'],
                self._short_name,
                '{length}yr'.format(length=self.end_year - self.start_year + 1))
        for path in [self._output_path, self._regrid_path]:
            if not os.path.exists(path):
                os.makedirs(path)
    # -----------------------------------------------

    def setup_dependencies(self, *args, **kwargs):
        """
        Climo doesnt require any other jobs
        """
        return True
    # -----------------------------------------------

    def postvalidate(self, config, *args, **kwargs):
        """
        Postrun validation for Ncclimo

        Ncclimo outputs 17 files, one for each month and then one for the 5 seasons

        Parameters
        ----------
            config (dict): the global configuration object
        Returns
        -------
            True if all output exists as expected
            False otherwise
        """
        if self._dryrun:
            return True

        file_list = get_climo_output_files(
            input_path=self._regrid_path,
            start_year=self.start_year,
            end_year=self.end_year)
        if len(file_list) < 17:  # number of months plus seasons and annual
            if self._has_been_executed:
                msg = '{prefix}: Failed to produce all regridded climos'.format(
                    prefix=self.msg_prefix())
                logging.error(msg)
            return False
        file_list = get_climo_output_files(
            input_path=self._output_path,
            start_year=self.start_year,
            end_year=self.end_year)
        if len(file_list) < 17:  # number of months plus seasons and annual
            if self._has_been_executed:
                msg = '{prefix}: Failed to produce all native grid climos'.format(
                    prefix=self.msg_prefix())
                logging.error(msg)
            return False

        # nothing's gone wrong, so we must be done
        return True
    # -----------------------------------------------

    def execute(self, config, event_list, dryrun=False):
        """
        Generates and submits a run script for ncremap to regrid model output

        Parameters
        ----------
            config (dict): the global processflow config object
            dryrun (bool): a flag to denote that all the data should be set,
                and the scripts generated, but not actually submitted
        """
        self._dryrun = dryrun

        if dryrun:
            if not config['data_types'].get('climo_regrid'):
                config['data_types']['climo_regrid'] = {'monthly': True}
            if not config['data_types'].get('climo_native'):
                config['data_types']['climo_native'] = {'monthly': True}
            input_path = os.path.join(
                config['global']['project_path'], 'dummpy_input_path')
        else:
            input_path, _ = os.path.split(self._input_file_paths[0])

        cmd = [
            'ncclimo',
            '-c', self.case,
            '-a', 'sdd',
            '-s', str(self.start_year),
            '-e', str(self.end_year),
            '-i', input_path,
            '-r', config['post-processing']['climo']['regrid_map_path'],
            '-o', self._output_path,
            '-O', self._regrid_path,
            '--no_amwg_links',
        ]

        self._has_been_executed = True
        return self._submit_cmd_to_manager(config, cmd, event_list)
    # -----------------------------------------------

    def handle_completion(self, filemanager, event_list, config, *args, **kwargs):
        """
        Adds the output files to the filemanager database
            as 'climo_regrid' and 'climo_native' data types

        Parameters
        ----------
            filemanager (FileManager): The filemanager to add the climo files to
            event_list (EventList): an event list to push notifications into
            config (dict): the global configuration object
        """
        if self.status != JobStatus.COMPLETED:
            msg = '{prefix}: Job failed, not running completion handler'.format(
                prefix=self.msg_prefix())
            print_line(msg, event_list)
            logging.info(msg)
            return
        else:
            msg = '{prefix}: Job complete'.format(
                prefix=self.msg_prefix())
            print_line(msg, event_list)
            logging.info(msg)

        new_files = list()
        for regrid_file in get_climo_output_files(self._regrid_path, self.start_year, self.end_year):
            new_files.append({
                'name': regrid_file,
                'local_path': os.path.join(self._regrid_path, regrid_file),
                'case': self.case,
                'year': self.start_year,
                'month': self.end_year,  # use the month to hold the end year field
                'local_status': FileStatus.PRESENT.value
            })
        filemanager.add_files(
            data_type='climo_regrid',
            file_list=new_files,
            super_type='derived')
        
        if not config['data_types'].get('climo_regrid'):
            config['data_types']['climo_regrid'] = {'monthly': True}

        for climo_file in get_climo_output_files(self._output_path, self.start_year, self.end_year):
            new_files.append({
                'name': climo_file,
                'local_path': os.path.join(self._regrid_path, climo_file),
                'case': self.case,
                'year': self.start_year,
                'month': self.end_year,  # use the month to hold the end year field
                'local_status': FileStatus.PRESENT.value
            })
        filemanager.add_files(
            data_type='climo_native',
            file_list=new_files,
            super_type='derived')
        if not config['data_types'].get('climo_native'):
            config['data_types']['climo_native'] = {'monthly': True}

        filemanager.write_database()
        msg = '{prefix}: Job completion handler done'.format(
            prefix=self.msg_prefix())
        print_line(msg, event_list)
        logging.info(msg)
    # -----------------------------------------------
