import os
import logging
from jobs.job import Job
from lib.jobstatus import JobStatus
from lib.util import get_ts_output_files, print_line
from lib.filemanager import FileStatus


class Timeseries(Job):
    def __init__(self, *args, **kwargs):
        super(Timeseries, self).__init__(*args, **kwargs)
        self._job_type = 'timeseries'
        self._data_required = [self._run_type]
        self._regrid = False
        custom_args = kwargs['config']['post-processing']['timeseries'].get(
            'custom_args')
        if custom_args:
            self.set_custom_args(custom_args)
    # -----------------------------------------------

    def setup_dependencies(self, *args, **kwargs):
        """
        Timeseries doesnt require any other jobs
        """
        return True
    # -----------------------------------------------

    def postvalidate(self, config, *args, **kwargs):
        """
        validate that all the timeseries variable files were producted as expected
        
        Parameters
        ----------
            config (dict): the global config object
        Returns
        -------
            True if all the files exist
            False otherwise
        """

        # First check that all the native grid ts files were created
        ts_path = os.path.join(
            config['global']['project_path'],
            'output',
            'pp',
            config['simulations'][self.case]['native_grid_name'],
            self._short_name,
            'ts',
            '{length}yr'.format(length=self.end_year - self.start_year + 1))

        regrid_map_path = config['post-processing']['timeseries'].get(
            'regrid_map_path')
        if regrid_map_path:
            regrid_path = os.path.join(
                config['global']['project_path'],
                'output',
                'pp',
                config['post-processing']['timeseries']['destination_grid_name'],
                self._short_name,
                'ts',
                '{length}yr'.format(length=self.end_year - self.start_year + 1))
            self._regrid = True
            self._output_path = regrid_path
        else:
            self._regrid = False
            self._output_path = ts_path

        if self._dryrun:
            return True

        for var in config['post-processing']['timeseries'][self._run_type]:
            file_name = "{var}_{start:04d}01_{end:04d}12.nc".format(
                var=var, start=self.start_year, end=self.end_year)
            file_path = os.path.join(ts_path, file_name)
            if not os.path.exists(file_path):
                if self._has_been_executed:
                    msg = "{prefix}: Unable to find {file} after execution".format(
                        prefix=self.msg_prefix(),
                        file=file_path)
                    logging.error(msg)
                return False

        # next, if regridding is turned on check that all regrid ts files were created
        if self._regrid:
            regrid_path = os.path.join(
                config['global']['project_path'],
                'output',
                'pp',
                config['post-processing']['timeseries']['destination_grid_name'],
                self._short_name,
                'ts',
                '{length}yr'.format(length=self.end_year - self.start_year + 1))
            for var in config['post-processing']['timeseries'][self._run_type]:
                file_name = "{var}_{start:04d}01_{end:04d}12.nc".format(
                    var=var, start=self.start_year, end=self.end_year)
                file_path = os.path.join(regrid_path, file_name)
                if not os.path.exists(file_path):
                    if self._has_been_executed:
                        msg = "{prefix}: Unable to find {file} after execution".format(
                            prefix=self.msg_prefix(),
                            file=file_path)
                        logging.error(msg)
                    return False

        # if nothing was missing then we must be done
        return True
    # -----------------------------------------------

    def execute(self, config, event_list, dryrun=False):
        """
        Generates and submits a run script for e3sm_diags

        Parameters
        ----------
            config (dict): the globus processflow config object
            event_list (EventList): an event list to push user notifications into
            dryrun (bool): a flag to denote that all the data should be set,
                and the scripts generated, but not actually submitted
        """
        self._dryrun = dryrun

        # setup the ts output path
        ts_path = os.path.join(
            config['global']['project_path'],
            'output',
            'pp',
            config['simulations'][self.case]['native_grid_name'],
            self._short_name,
            'ts',
            '{length}yr'.format(length=self.end_year - self.start_year + 1))
        if not os.path.exists(ts_path):
            os.makedirs(ts_path)

        regrid_map_path = config['post-processing']['timeseries'].get(
            'regrid_map_path')
        if regrid_map_path:
            regrid_path = os.path.join(
                config['global']['project_path'],
                'output',
                'pp',
                config['post-processing']['timeseries']['destination_grid_name'],
                self._short_name,
                'ts',
                '{length}yr'.format(length=self.end_year - self.start_year + 1))
            self._regrid = True
            self._output_path = regrid_path
        else:
            self._regrid = False
            self._output_path = ts_path

        # sort the input files
        self._input_file_paths.sort()
        list_string = ' '.join(self._input_file_paths)

        # create the ncclimo command string
        var_list = config['post-processing']['timeseries'][self._run_type]
        cmd = [
            'ncclimo',
            '-a', 'sdd',
            '-c', self.case,
            '-v', ','.join(var_list),
            '-s', str(self.start_year),
            '-e', str(self.end_year),
            '--ypf={}'.format(self.end_year - self.start_year + 1),
            '-o', ts_path
        ]
        if self._regrid:
            cmd.extend([
                '-O', regrid_path,
                '--map={}'.format(regrid_map_path),
            ])
        cmd.append(list_string)

        return self._submit_cmd_to_manager(config, cmd)
    # -----------------------------------------------

    def handle_completion(self, filemanager, event_list, config):
        """
        Post run handler, adds produced timeseries variable files into
        the filemanagers database
        
        Parameters
        ----------
            filemanager (FileManager): The filemanager to add the files to
            event_list (EventList): an event list to push user notifications into
            config (dict): the global config object
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

        var_list = config['post-processing']['timeseries'][self._run_type]

        # add native timeseries files to the filemanager db
        ts_path = os.path.join(
            config['global']['project_path'],
            'output',
            'pp',
            config['simulations'][self.case]['native_grid_name'],
            self._short_name,
            'ts',
            '{length}yr'.format(length=self.end_year - self.start_year + 1))

        new_files = list()
        for ts_file in get_ts_output_files(ts_path, var_list, self.start_year, self.end_year):
            new_files.append({
                'name': ts_file,
                'local_path': os.path.join(ts_path, ts_file),
                'case': self.case,
                'year': self.start_year,
                'month': self.end_year,
                'local_status': FileStatus.PRESENT.value
            })
        filemanager.add_files(
            data_type='{}_ts_native'.format(self.data_type),
            file_list=new_files)
        if not config['data_types'].get('ts_native'):
            config['data_types']['ts_native'] = {'monthly': False}

        if self._regrid:
            # add regridded timeseries files to the filemanager db
            regrid_path = os.path.join(
                config['global']['project_path'],
                'output',
                'pp',
                config['post-processing']['timeseries']['destination_grid_name'],
                self._short_name,
                'ts',
                '{length}yr'.format(length=self.end_year - self.start_year + 1))

            new_files = list()
            ts_files = get_ts_output_files(ts_path, var_list, self.start_year, self.end_year)
            for regrid_file in ts_files:
                new_files.append({
                    'name': regrid_file,
                    'local_path': os.path.join(regrid_path, regrid_file),
                    'case': self.case,
                    'year': self.start_year,
                    'month': self.end_year,
                    'local_status': FileStatus.PRESENT.value
                })
            filemanager.add_files(
                data_type='{}_ts_regrid'.format(self.data_type),
                file_list=new_files)
            if not config['data_types'].get('ts_regrid'):
                config['data_types']['ts_regrid'] = {'monthly': False}

        msg = '{prefix}: Job completion handler done'.format(
            prefix=self.msg_prefix())
        print_line(msg, event_list)
        logging.info(msg)
    # -----------------------------------------------
