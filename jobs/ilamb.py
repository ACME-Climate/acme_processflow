"""
A wrapper class around ILAMB
"""
import os
import shutil
import errno
import glob
import logging

from jobs.diag import Diag
from lib.util import render, get_cmor_output_files, format_debug, mkdir_p
from lib.jobstatus import JobStatus


class ILAMB(Diag):
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
            config (dict): the global configuration object
            custom_args (dict): a dictionary of user supplied arguments
                to pass to the resource manager
        """
        super(ILAMB, self).__init__(*args, **kwargs)
        self._job_type = 'ilamb'
        self._requires = 'cmor'
        self._host_url = ''
        self.case_start_year = kwargs['config']['simulations']['start_year']
        self._data_required = ['cmorized']

        if kwargs['config']['global']['host']:
            self._host_path = os.path.join(
                kwargs['config']['img_hosting']['host_directory'],
                self.short_name,
                'ilamb',
                '{start:04d}_{end:04d}_vs_{comp}'.format(
                    start=self.start_year,
                    end=self.end_year,
                    comp=self._short_comp_name))
        else:
            self._host_path = os.path.join(
                'html', 'ilamb', self.short_name,
                '{start:04d}_{end:04d}_vs_{comp}'.format(
                                               start=self.start_year,
                                               end=self.end_year,
                                               comp=self._short_comp_name))
        mkdir_p(self._host_path)

        custom_args = kwargs['config']['diags'][self.job_type].get(
            'custom_args')
        if custom_args:
            self.set_custom_args(custom_args)

        # setup the output directory, creating it if it doesnt already exist
        custom_output_path = kwargs['config']['diags'][self.job_type].get(
            'custom_output_path')
        if custom_output_path:
            self._replace_dict['COMPARISON'] = self._short_comp_name
            self._output_path = self.setup_output_directory(custom_output_path)
        else:
            self._output_path = os.path.join(
                kwargs['config']['global']['project_path'],
                'output',
                'diags',
                self.short_name,
                self.job_type,
                '{start:04d}_{end:04d}_vs_{comp}'.format(
                    start=self.start_year,
                    end=self.end_year,
                    comp=self._short_comp_name))
        if not os.path.exists(self._output_path):
            os.makedirs(self._output_path)

        # need to know the cmor output directory as well
        custom_cmor_path = kwargs['config']['post-processing']['cmor'].get(
            'custom_output_path')
        if custom_cmor_path:
            self._cmor_path = self.setup_output_directory(custom_cmor_path)
        else:
            self._cmor_path = os.path.join(
                kwargs['config']['global']['project_path'],
                'output', 'pp', 'cmor', self.short_name, 'cmor')

        # create an ILAMB models directory and input data path subdirectory
        self._ilamb_models_dir = os.path.join(self._output_path, 'MODELS')
        self._input_base_path = os.path.join(self._ilamb_models_dir,
                                             self.short_name)
        # make sure both directories exist
        mkdir_p(self._input_base_path)

    def _dep_filter(self, job):
        """
        find the CMOR job we're waiting for, assuming there's only
        one CMOR job in this case with the same start and end years
        """
        if job.job_type != self._requires:
            return False
        if job.start_year != self.start_year:
            return False
        if job.end_year != self.end_year:
            return False
        return True

    def setup_dependencies(self, jobs, *args, **kwargs):
        """
        Adds CMOR jobs from this or the comparison case to the list of
        dependent jobs

        Parameters
        ----------
            jobs (list): a list of the rest of the run managers jobs
            optional: comparison_jobs (list): if this job is being compared to
                another case, the cmorized output for that other case has to
                be done already too
        """
        if self.comparison != 'obs':
            other_jobs = kwargs['comparison_jobs']
            try:
                self_cmor, = filter(lambda job: self._dep_filter(job),
                                    other_jobs)
            except ValueError:
                msg = 'Unable to find CMOR for {}, is this case set to ' \
                      'generate CMORized output?'.format(self.msg_prefix())
                raise Exception(msg)
        else:
            try:
                self_cmor, = filter(lambda job: self._dep_filter(job), jobs)
            except ValueError:
                msg = 'Unable to find CMOR for {}, is this case set to ' \
                      'generate CMORized output?'.format(self.msg_prefix())
                raise Exception(msg)

    def setup_data(self, config, filemanager, case):
        """
        Copy all data_types specified in the jobs _data_required field,
        and appends the path to the copies into the _input_file_paths list
        """

        # loop over the data types, linking them in one at a time
        for datatype in self._data_required:
            # do the normal thing non-cmorized data
            if datatype != 'cmorized':
                super(ILAMB, self).setup_data(config, filemanager, case)

            files = get_cmor_output_files(os.path.abspath(self._cmor_path),
                                          self.start_year,
                                          self.end_year)

            if not files or len(files) == 0:
                msg = "{prefix}: filemanager can't find input files for " \
                      "datatype {datatype}".format(prefix=self.msg_prefix(),
                                                   datatype=datatype)
                logging.error(msg)
                continue

            for file_ in files:
                destination = os.path.join(self._input_base_path,
                                           os.path.basename(file_))
                # keep a reference to the input data for later
                self._input_file_paths.append(destination)
                try:
                    shutil.copy(file_, destination)
                except Exception as e:
                    msg = format_debug(e)
                    logging.error(msg)

    def execute(self, config, event_list, slurm_args=None, dryrun=False):
        """
        Generates and submits a run script for ILAMB

        Parameters
        ----------
            config (dict): the globus processflow config object
            dryrun (bool): a flag to denote that all the data should be set,
                and the scripts generated, but not actually submitted
        """
        self._dryrun = dryrun
        ilamb_config = config['diags']['ilamb']

        # setup template
        template_out = os.path.join(
            config['global']['run_scripts_path'],
            '{job}_{start:04d}_{end:04d}_{case}_vs_{comp}.cfg'.format(
                job=self._job_type,
                start=self.start_year,
                end=self.end_year,
                case=self.short_name,
                comp=self._short_comp_name))
        template_input_path = os.path.join(
            config['global']['resource_path'],
            'ilamb_vs_obs.cfg')

        # remove previous run script if it exists
        if os.path.exists(template_out):
            os.remove(template_out)
        render(
            variables={},
            input_path=template_input_path,
            output_path=template_out)

        cmd = ['export ILAMB_ROOT={} '.format(ilamb_config['ilamb_root']),
               '\nilamb-run',
               '--config', template_out,
               '--model_root', self._ilamb_models_dir,
               '--models', self.short_name,
               '--build_dir', self._host_path]
        if ilamb_config.get('confrontation'):
            cmd.extend(['--confrontation',
                        ' '.join(list(ilamb_config['confrontation']))])
        if ilamb_config.get('shift_from') and ilamb_config.get('shift_to'):
            cmd.extend(['--model_year',
                        '{} {}'.format(ilamb_config['shift_from'],
                                       ilamb_config['shift_to'])
                        ])
        if ilamb_config.get('regions'):
            cmd.extend(['--regions',
                        ' '.join(list(ilamb_config['regions']))])
        if ilamb_config.get('region_definition_files'):
            cmd.extend(['--define_regions',
                        ' '.join(list(ilamb_config['region_definition_files']))])
        if ilamb_config.get('clean') in [1, '1', 'true', 'True']:
            cmd.append('--clean')
        if ilamb_config.get('disable_logging') in [1, '1', 'true', 'True']:
            cmd.append('--disable_logging')

        self._has_been_executed = True
        return self._submit_cmd_to_manager(config, cmd, event_list)

    def postvalidate(self, config, *args, **kwargs):
        """
        Validates that the diagnostic produced its expected output

        Parameters
        ----------
            config (dict): the global config object
        Returns
        -------
            True if all output exists as expected
            False otherwise
        """
        # if the job ran through slurm can came back complete, just return True
        if self.status == JobStatus.COMPLETED:
            return True
        elif self.status == JobStatus.FAILED:
            return False
        # otherwise, maybe this job hasnt been run yet in this instance, but the
        # output might be there
        else:
            logs = glob.glob(os.path.join(self._host_path, 'ILAMB*.log'))
            if logs:
                return True
            else:
                return False

    def handle_completion(self, filemanager, event_list, config,
                          *args, **kwargs):
        """
        Setup for webhosting after a successful run

        ILAMB handles moving the files to the correct location, so no extra
        handling is required

        Parameters
        ----------
            filemanager ():
            event_list (EventList): event list to push user notifications into
            config (dict): the global config object
        """
        pass
