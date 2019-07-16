import logging
import os
import re

from processflow.jobs.job import Job
from processflow.lib.jobstatus import JobStatus
from processflow.lib.util import print_line, get_data_output_files
from processflow.lib.filemanager import FileStatus


class Regrid(Job):
    """
    Perform regridding with no climatology or timeseries generation on atm, lnd, and orn data
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize a regrid job
        Parameters:
            data_type (str): what type of data to run on (atm, lnd)
        """
        super(Regrid, self).__init__(*args, **kwargs)
        self._job_type = 'regrid'
        self._data_required = [self._run_type]

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
                'regrid_' + kwargs['config']['post-processing']['regrid'][self.run_type]['destination_grid_name'],
                self._short_name,
                self.run_type)
        if not os.path.exists(self._output_path):
            os.makedirs(self._output_path)
    # -----------------------------------------------

    def setup_dependencies(self, *args, **kwargs):
        """
        Regrid doesnt require any other jobs
        """
        return True
    # -----------------------------------------------

    def execute(self, config, event_list, dryrun=False):
        """
        Generates and submits a run script for ncremap to regrid model output

        Parameters
        ----------
            config (dict): the global processflow config object
            event_list (EventList): an event list to push user notifications into
            dryrun (bool): a flag to denote that all the data should be set,
                and the scripts generated, but not actually submitted
        """
        self._dryrun = dryrun

        input_path, _ = os.path.split(self._input_file_paths[0])
        # setups the ncremap run command
        cmd = ['ncks --version\n',
               'ncremap --version\n',
               'ncremap -I {}'.format(input_path)]

        if self.run_type == 'lnd':
            cmd.extend([
                '-P', 'sgs',
                '-a', 'conserve',
                '-s', config['post-processing']['regrid']['lnd']['source_grid_path'],
                '-g', config['post-processing']['regrid']['lnd']['destination_grid_path']
            ])
        elif self.run_type == 'ocn' or self.run_type == 'cice': 
            cmd.extend([
                '-P', 'mpas',
                '-m', config['post-processing']['regrid'][self.run_type]['regrid_map_path']
            ])
        elif self.run_type == 'atm':
            cmd.extend([
                '-m', config['post-processing']['regrid'][self.run_type]['regrid_map_path']
            ])
        else:
            msg = 'Unsupported regrid type'
            logging.error(msg)
            self.status = JobStatus.FAILED
            return 0

        # input_path, _ = os.path.split(self._input_file_paths[0])

        # clean up the input directory to make sure there's only nc files
        for item in os.listdir(input_path):
            if not item[-3:] == '.nc':
                os.remove(os.path.join(input_path, item))

        cmd.extend([
            '-O', self._output_path,
        ])

        self._has_been_executed = True
        return self._submit_cmd_to_manager(config, cmd, event_list)
    # -----------------------------------------------

    def postvalidate(self, config, *args, **kwargs):

        contents = os.listdir(self._output_path)
        contents.sort()
        for year in range(self.start_year, self.end_year + 1):
            for month in range(1, 13):
                pattern = r'%04d-%02d' % (year, month)
                found = False
                for item in contents:
                    if re.search(pattern, item):
                        found = True
                        break
                if not found:
                    if not self._has_been_executed:
                        msg = '{prefix}: Unable to find regridded output file for {yr}-{mon}'.format(
                            prefix=self.msg_prefix(),
                            yr=year,
                            mon=month)
                        logging.error(msg)
                    return False
        return True
    # -----------------------------------------------

    def handle_completion(self, filemanager, event_list, config, *args, **kwargs):
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
        regrid_files = get_data_output_files(
            self._output_path, self.case, self.start_year, self.end_year)
        for regrid_file in regrid_files:
            new_files.append({
                'name': regrid_file,
                'local_path': os.path.join(self._output_path, regrid_file),
                'case': self.case,
                'year': self.start_year,
                'local_status': FileStatus.PRESENT.value
            })
        filemanager.add_files(
            data_type='regrid',
            file_list=new_files,
            super_type='derived')
        if not config['data_types'].get('regrid'):
            config['data_types']['regrid'] = {'monthly': True}
    # -----------------------------------------------

    @property
    def run_type(self):
        return self._run_type
    # -----------------------------------------------

    def setup_temp_path(self, config, *args, **kwards):
        """
        creates the input structure for the regrid job
        /project/output/temp/case_short_name/job_type_run_type/start_end
        """
        return os.path.join(
            config['global']['project_path'],
            'output', 'temp', self._short_name,
            '{}_{}'.format(self._job_type, self._run_type),
            '{:04d}_{:04d}'.format(self._start_year, self._end_year))
    # -----------------------------------------------

    def get_run_name(self):
        return '{type}_{run_type}_{start:04d}_{end:04d}_{case}'.format(
            type=self.job_type,
            run_type=self._run_type,
            start=self.start_year,
            end=self.end_year,
            case=self.short_name)
    # -----------------------------------------------

