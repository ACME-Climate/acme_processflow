"""
A module for the base Job class that all jobs decend from
"""
import json
import os
import sys
import logging
from uuid import uuid4

from lib.util import render
from lib.slurm import Slurm
from lib.pbs import PBS
from lib.jobstatus import JobStatus
from lib.util import create_symlink_dir, print_line


class Job(object):
    """
    A base job class for all post-processing and diagnostic jobs
    """

    def __init__(self, start, end, case, short_name, data_required=None, dryrun=False, **kwargs):
        self._start_year = start
        self._end_year = end
        self._data_required = data_required
        self._data_ready = False
        self._depends_on = list()
        self._id = uuid4().hex[:10]
        self._job_id = 0
        self._has_been_executed = False
        self._status = JobStatus.VALID
        self._case = case
        self._short_name = short_name
        self._run_type = kwargs.get('run_type')
        self._job_type = None
        self._input_file_paths = list()
        self._input_base_path = ''
        self._console_output_path = None
        self._output_path = ''
        self._dryrun = dryrun
        self._manager_args = {
            'slurm': ['-t 0-10:00', '-N 1'],
            'pbs': ['-l nodes=1:ppn=1', '-q acme', '-l walltime=02:00:00']
        }
        config = kwargs['config']
        # setup the default replacement dict
        self._replace_dict = {
            'PROJECT_PATH': config['global']['project_path'],
            'REMOTE_PATH': config['simulations'][case].get('remote_path', ''),
            'CASEID': case,
            'REST_YR': '{:04d}'.format(self.start_year + 1),
            'START_YR': '{:04d}'.format(self.start_year),
            'END_YR': '{:04d}'.format(self.end_year),
            'LOCAL_PATH': config['simulations'][case].get('local_path', ''),
        }
    # -----------------------------------------------

    def setup_output_directory(self, custom_output_string):
        for string, val in list(self._replace_dict.items()):
            if string in custom_output_string:
                custom_output_string = custom_output_string.replace(
                    string, val)
        return custom_output_string
    # -----------------------------------------------

    def setup_dependencies(self, *args, **kwargs):
        msg = '{} has not implemented the setup_dependencies method'.format(
            self.job_type)
        raise Exception(msg)
    # -----------------------------------------------

    def execute(self, *args, **kwargs):
        msg = '{} has not implemented the execute method'.format(self.job_type)
        raise Exception(msg)
    # -----------------------------------------------

    def postvalidate(self, *args, **kwargs):
        msg = '{} has not implemented the postvalidate method'.format(
            self.job_type)
        raise Exception(msg)
    # -----------------------------------------------

    def handle_completion(self, filemanager, event_list, config, *args, **kwargs):
        msg = '{} has not implemented the handle_completion method'.format(
            self.job_type)
        raise Exception(msg)
    # -----------------------------------------------

    def get_output_path(self):
        if self.status == JobStatus.COMPLETED:
            return self._output_path
        else:
            return self._console_output_path
    # -----------------------------------------------

    def set_custom_args(self, custom_args):
        """
        Adds the arguments in custom_args to the jobs resource manager arguments
        If any keys are already present in the jobs manager_args they are over
            written with the new args

        Parameters
        ----------
            custom_args (dict): a mapping of args to the arg values
        """
        for arg, val in custom_args.items():
            new_arg = '{} {}'.format(arg, val)
            for manager, manager_args in self._manager_args.items():
                found = False
                for marg in manager_args:
                    if arg in marg:
                        marg = new_arg
                        found = True
                        break
                if not found:
                    manager_args.append(new_arg)
    # -----------------------------------------------

    def get_report_string(self):
        return '{prefix} :: {status} :: {output}'.format(
            prefix=self.msg_prefix(),
            status=self.status.name,
            output=self.get_output_path())
    # -----------------------------------------------

    def setup_data(self, config, filemanager, case):
        """
        symlinks all data_types sepecified in the jobs _data_required field,
        and puts a copy of the path for the links into the _input_file_paths field
        """

        # loop over the data types, linking them in one at a time
        for datatype in self._data_required:

            datainfo = config['data_types'].get(datatype)

            # this should never be hit if the config validator did its job
            if not datainfo:
                print "ERROR: Unable to find config information for {}".format(
                    datatype)
                sys.exit(1)

            # are these history files?
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
                msg = "{prefix}: filemanager can't find input files for datatype {datatype}".format(
                    prefix=self.msg_prefix(),
                    datatype=datatype)
                logging.error(msg)
                continue

            # extract the file names
            filesnames = list()
            for file in files:
                tail, head = os.path.split(file)
                filesnames.append(head)

            # create the path to where we should place our temp symlinks
            self._input_base_path = self.setup_temp_path(
                config=config)
            if not os.path.exists(self._input_base_path):
                os.makedirs(self._input_base_path)

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

    def setup_temp_path(self, config, *args, **kwards):
        """
        creates the default input path structure
        /project/output/temp/case_short_name/job_type/start_end
        """
        return os.path.join(
            config['global']['project_path'],
            'output', 'temp', self._short_name, self._job_type,
            '{:04d}_{:04d}'.format(self._start_year, self._end_year))
    # -----------------------------------------------

    def check_data_ready(self, filemanager):
        """
        Checks that the data needed for the job is present on the machine, in the input directory
        """
        if self._data_ready == True:
            return
        else:
            self._data_ready = filemanager.check_data_ready(
                data_required=self._data_required,
                case=self._case,
                start_year=self.start_year,
                end_year=self.end_year)
        return
    # -----------------------------------------------

    def check_data_in_place(self):
        """
        Checks that the data needed for the job has been symlinked into the jobs temp directory

        This assumes that the job.setup_data method worked correctly and all files needed are in 
            the _input_file_paths list
        """
        if len(self._input_file_paths) == 0:
            return False

        for item in self._input_file_paths:
            if not os.path.exists(item):
                msg = '{prefix}: File not found in input temp directory {file}'.format(
                    prefix=self.msg_prefix(),
                    file=item)
                logging.error(msg)
                return False
        # nothing was missing
        return True
    # -----------------------------------------------

    def msg_prefix(self):
        if self._run_type:
            return '{type}-{run_type}-{start:04d}-{end:04d}-{case}'.format(
                type=self.job_type,
                run_type=self._run_type,
                start=self.start_year,
                end=self.end_year,
                case=self.short_name)
        else:
            return '{type}-{start:04d}-{end:04d}-{case}'.format(
                type=self.job_type,
                start=self.start_year,
                end=self.end_year,
                case=self.short_name)
    # -----------------------------------------------

    def get_run_name(self):
        return '{type}_{start:04d}_{end:04d}_{case}'.format(
            type=self.job_type,
            start=self.start_year,
            end=self.end_year,
            case=self.short_name)
    # -----------------------------------------------

    def _submit_cmd_to_manager(self, config, cmd, event_list):
        """
        Takes the jobs main cmd, generates a batch script and submits the script
        to the resource manager controller

        Parameters:
            cmd (list): a list of the command and its arguments to submit
            config (dict): the global configuration object
        Returns:
            job_id (int): the job_id from the resource manager
        """
        # setup for the run script
        scripts_path = os.path.join(
            config['global']['project_path'],
            'output', 'scripts')
        run_name = self.get_run_name()
        run_script = os.path.join(scripts_path, run_name)
        self._console_output_path = '{}.out'.format(run_script)
        if os.path.exists(run_script):
            os.remove(run_script)

        try:
            manager = Slurm()
            manager_prefix = '#SBATCH'
            self._manager_args['slurm'].append(
                '-o {}'.format(self._console_output_path))
        except:
            try:
                manager = PBS()
                manager_prefix = '#PBS'
                self._manager_args['pbs'].append(
                    '-o {}'.format(self._console_output_path))
                self._manager_args['pbs'].append(
                    '-e {}'.format(self._console_output_path.replace('.out', '.err')))
            except:
                raise Exception("No resource manager found")

        # generate the run script using the manager arguments and command
        command = ' '.join(cmd)
        script_prefix = ''

        if isinstance(manager, Slurm):
            margs = self._manager_args['slurm']
        else:
            margs = self._manager_args['pbs']
        for item in margs:
            script_prefix += '{prefix} {value}\n'.format(
                prefix=manager_prefix,
                value=item)

        with open(run_script, 'w') as batchfile:
            batchfile.write('#!/bin/bash\n')
            batchfile.write(script_prefix)

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
        # with open(run_script, 'w+') as batchfile:
        #     batchfile.write(command)

        # if this is a dry run, set the status and exit
        if self._dryrun:
            msg = '{}: dryrun is set, completing without running'.format(
                self.msg_prefix())
            logging.info(msg)
            self.status = JobStatus.COMPLETED
            return False

        # submit the run script to the resource controller
        self._job_id = manager.batch(run_script)
        self._has_been_executed = True
        return self._job_id
    # -----------------------------------------------

    def prevalidate(self, *args, **kwargs):
        if not self.data_ready:
            msg = '{prefix}: data not ready'.format(prefix=self.msg_prefix())
            logging.error(msg)
            return False
        if not self.check_data_in_place():
            msg = '{prefix}: data not in place'.format(
                prefix=self.msg_prefix())
            logging.error(msg)
            return False
        return True
    # -----------------------------------------------

    @property
    def short_name(self):
        return self._short_name
    # -----------------------------------------------

    @property
    def comparison(self):
        return 'obs'
    # -----------------------------------------------

    @property
    def case(self):
        return self._case
    # -----------------------------------------------

    @property
    def start_year(self):
        return self._start_year
    # -----------------------------------------------

    @property
    def end_year(self):
        return self._end_year
    # -----------------------------------------------

    @property
    def job_type(self):
        return self._job_type
    # -----------------------------------------------

    @property
    def depends_on(self):
        return self._depends_on
    # -----------------------------------------------

    @property
    def id(self):
        return self._id
    # -----------------------------------------------

    @property
    def data_ready(self):
        return self._data_ready
    # -----------------------------------------------

    @data_ready.setter
    def data_ready(self, ready):
        if not isinstance(ready, bool):
            raise Exception('Invalid data type, data_ready only accepts bools')
        self._data_ready = ready
    # -----------------------------------------------

    @property
    def run_type(self):
        return self._run_type
    # -----------------------------------------------

    @property
    def data_required(self):
        return self._data_required
    # -----------------------------------------------

    @data_required.setter
    def data_required(self, types):
        self._data_required = types
    # -----------------------------------------------

    @property
    def status(self):
        return self._status
    # -----------------------------------------------

    @status.setter
    def status(self, nstatus):
        self._status = nstatus
    # -----------------------------------------------

    @property
    def job_id(self):
        return self._job_id
    # -----------------------------------------------

    @job_id.setter
    def job_id(self, new_id):
        if not isinstance(new_id, str):
            msg = '{} is not a valid job_id type'.format(type(new_id))
            raise Exception(msg)
        self._job_id = new_id
    # -----------------------------------------------

    def __str__(self):
        return json.dumps({
            'type': self._job_type,
            'start_year': self._start_year,
            'end_year': self._end_year,
            'data_required': self._data_required,
            'data_ready': self._data_ready,
            'depends_on': self._depends_on,
            'id': self._id,
            'job_id': self._job_id,
            'status': self._status.name,
            'case': self._case,
            'short_name': self._short_name
        }, sort_keys=True, indent=4)

    # -----------------------------------------------
