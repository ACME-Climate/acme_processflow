import os

from subprocess import Popen, PIPE

from processflow.jobs.diag import Diag
from processflow.lib.jobstatus import JobStatus
from processflow.lib.util import render


class MPASAnalysis(Diag):
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
            config (dict): the global configuration object
            custom_args (dict): a dictionary of user supplied arguments
                to pass to the resource manager
        """
        super(MPASAnalysis, self).__init__(*args, **kwargs)
        self._job_type = 'mpas_analysis'
        self._requires = ''
        self._host_url = ''
        self.case_start_year = kwargs['config']['simulations']['start_year']
        self._data_required = ['cice', 'ocn',
                               'ocn_restart', 'cice_restart',
                               'ocn_streams', 'cice_streams',
                               'ocn_in', 'cice_in',
                               'meridionalHeatTransport']

        config = kwargs.get('config')
        if config and config['global'].get('host'):
            self._host_path = os.path.join(
                config['img_hosting']['host_directory'],
                self.short_name,
                'mpas_analysis',
                '{start:04d}_{end:04d}_vs_{comp}'.format(
                    start=self.start_year,
                    end=self.end_year,
                    comp=self._short_comp_name))
        else:
            self._host_path = 'html'

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

    # -----------------------------------------------

    def setup_dependencies(self, *args, **kwargs):
        """
        mpas_analysis doesnt depend on any other jobs
        """
        return
    # -----------------------------------------------

    def execute(self, config, event_list, dryrun=False):
        """
        Generates and submits a run script for mpas_analysis

        Parameters
        ----------
            config (dict): the global processflow config object
            event_list (EventList): an EventList to push user notifications into
            dryrun (bool): a flag to denote that all the data should be set,
                and the scripts generated, but not actually submitted
        """
        self._dryrun = dryrun
        mpas_config = config['diags']['mpas_analysis']

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
            'mpas_a_vs_obs.cfg')

        # create the "generate_plots" string
        generate_string = '["' + '", "'.join(
            [x for x in mpas_config.get('generate_plots', '')]) + '"]'

        # setup the start year offset for nino and ts plots
        offset = int(config['simulations']['start_year'])
        if self._start_year == offset or (self._start_year - offset) < 0:
            start_offset = 0
        else:
            start_offset = int(mpas_config.get('start_year_offset', 0))

        variables = {
            'case': self.case,
            'numWorkers': mpas_config.get('num_workers', 8),
            'baseInputPath': self._input_base_path,
            'restartSubPath': self._input_base_path,
            'ocnHistSubPath': self._input_base_path,
            'iceHistSubPath': self._input_base_path,
            'meshName': config['simulations'][self.case].get('native_mpas_grid_name', ''),
            'mappingPath': mpas_config.get('mapping_directory', ''),
            'ocnNamelistName': mpas_config.get('ocean_namelist_name', 'mpaso_in'),
            'ocnStreamsName': mpas_config.get('ocean_streams_name', 'streams.ocean'),
            'iceNamelistName': mpas_config.get('seaice_namelist_name', 'mpassi_in'),
            'iceStreamsName': mpas_config.get('seaice_streams_name', 'streams.seaice'),
            'outputBasePath': self._output_path,
            'generatePlots': generate_string,
            'startYear': self.start_year,
            'endYear': self.end_year,
            'tsStart': self.start_year - start_offset,
            'tsEnd': self.end_year,
            'ninoStart': self.start_year - start_offset,
            'ninoEnd': self.end_year,
            'ocnObsPath': mpas_config.get('ocn_obs_data_path', ''),
            'iceObs': mpas_config.get('seaice_obs_data_path', ''),
            'regionMaskPath': mpas_config.get('region_mask_path', ''),
            'runMOC': mpas_config.get('run_MOC', ''),
            'htmlSubdirectory': self._host_path
        }
        # remove previous run script if it exists
        if os.path.exists(template_out):
            os.remove(template_out)
        render(
            variables=variables,
            input_path=template_input_path,
            output_path=template_out)

        cmd = ['mpas_analysis', template_out]
        self._has_been_executed = True
        return self._submit_cmd_to_manager(config, cmd, event_list)
    # -----------------------------------------------

    def postvalidate(self, config, *args, **kwargs):
        """
        Validates that the diagnostic produced its expected output

        Parameters
        ----------
            config (dict): the global cofiguration object
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
        # otherwise, maybe this job hasnt been run yet in this instance, but the output might be there
        else:
            log_path = os.path.join(self._output_path, 'logs')
            if os.path.exists(log_path):
                # Check that there are actually files inside the log directory
                if len(os.listdir(log_path)) < 50:
                    return False
                # grep the logs directory for any errors, if the logs directory exists, and
                # doesnt contain any errors, then the job was probably run previously and finished successfully
                cmd = 'grep Error {}/*.log'.format(log_path)
                out, err = Popen(cmd, stdout=PIPE, stderr=PIPE,
                                 shell=True).communicate()
                if out or err:
                    return False
                else:
                    return True
            # if there's no logs directory, the job has never been started
            else:
                return False
    # -----------------------------------------------

    def handle_completion(self, filemanager, event_list, config, *args, **kwargs):
        """
        Setup for webhosting after a successful run

        MPAS-Analysis handles moving the files to the correct location, so no extra handling is required

        Parameters
        ----------
            event_list (EventList): an event list to push user notifications into
            config (dict): the global config object
        """
        self._host_url = 'https://{server}/{prefix}/{case}/mpas_analysis/{start:04d}_{end:04d}_vs_{comp}/index.html'.format(
            server=config['img_hosting']['img_host_server'],
            prefix=config['img_hosting']['url_prefix'],
            case=self.short_name,
            start=self.start_year,
            end=self.end_year,
            comp=self._short_comp_name)

    # -----------------------------------------------
