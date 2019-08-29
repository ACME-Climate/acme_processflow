"""
A wrapper class around E3SM Diags
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import logging
import os

from bs4 import BeautifulSoup

from processflow.jobs.diag import Diag
from processflow.lib.jobstatus import JobStatus
from processflow.lib.util import render, print_line


class E3SMDiags(Diag):
    def __init__(self, *args, **kwargs):
        super(E3SMDiags, self).__init__(*args, **kwargs)
        self._job_type = 'e3sm_diags'
        self._requires = 'climo'
        self._data_required = ['climo_regrid']

        if kwargs['config']['global']['host']:
            self._host_path = os.path.join(
                kwargs['config']['img_hosting']['host_directory'],
                self.short_name,
                'e3sm_diags',
                '{start:04d}_{end:04d}_vs_{comp}'.format(
                    start=self.start_year,
                    end=self.end_year,
                    comp=self._short_comp_name))
        else:
            self._host_path = ''

        custom_args = kwargs['config']['diags']['e3sm_diags'].get(
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

    def _dep_filter(self, job):
        """
        find the climo job we're waiting for, assuming there's only
        one climo job in this case with the same start and end years
        """
        if job.job_type != self._requires:
            return False
        if job.start_year != self.start_year:
            return False
        if job.end_year != self.end_year:
            return False
        return True
    # -----------------------------------------------

    def setup_dependencies(self, jobs, *args, **kwargs):
        """
        Adds climo jobs from this or the comparison case to the list of dependent jobs

        Parameters
        ----------
            jobs (list): a list of the rest of the run managers jobs
            optional: comparison_jobs (list): if this job is being compared to
                another case, the climos for that other case have to be done already too
        """
        if self.comparison != 'obs':
            other_jobs = kwargs['comparison_jobs']
            try:
                self_climo, = [job for job in jobs if self._dep_filter(job)]
            except ValueError:
                msg = 'Unable to find climo for {}, is this case set to generate climos?'.format(
                    self.msg_prefix())
                raise Exception(msg)
            try:
                comparison_climo, = [job for job in other_jobs if self._dep_filter(job)]
            except ValueError:
                msg = 'Unable to find climo for {}, is that case set to generates climos?'.format(
                    self.comparison)
                raise Exception(msg)
            self.depends_on.extend((self_climo.id, comparison_climo.id))
        else:
            try:
                self_climo, = [job for job in jobs if self._dep_filter(job)]
            except ValueError:
                msg = 'Unable to find climo for {}, is this case set to generate climos?'.format(
                    self.msg_prefix())
                raise Exception(msg)
            self.depends_on.append(self_climo.id)
    # -----------------------------------------------

    def execute(self, config, event_list, slurm_args=None, dryrun=False):
        """
        Generates and submits a run script for e3sm_diags

        Parameters
        ----------
            config (dict): the global processflow config object
            dryrun (bool): a flag to denote that all the data should be set,
                and the scripts generated, but not actually submitted
        """
        self._dryrun = dryrun

        # render the parameter file from the template
        param_template_out = os.path.join(
            config['global']['run_scripts_path'],
            'e3sm_diags_{start:04d}_{end:04d}_{case}_vs_{comp}_params.py'.format(
                start=self.start_year,
                end=self.end_year,
                case=self.short_name,
                comp=self._short_comp_name))
        variables = dict()

        if dryrun:
            input_path = os.path.join(config['global']['project_path'], 'dummpy_input_path')
        else:
            input_path, _ = os.path.split(self._input_file_paths[0])

        variables['short_test_name'] = self.short_name
        variables['test_data_path'] = input_path
        variables['test_name'] = self.case
        variables['backend'] = config['diags']['e3sm_diags']['backend']
        variables['results_dir'] = self._output_path
        variables['num_workers'] = config['diags']['e3sm_diags'].get('num_workers', 24)

        if self.comparison == 'obs':
            template_input_path = os.path.join(
                config['global']['resource_path'],
                'e3sm_diags_template_vs_obs.py')
            variables['reference_data_path'] = config['diags']['e3sm_diags']['reference_data_path']
        else:
            template_input_path = os.path.join(
                config['global']['resource_path'],
                'e3sm_diags_template_vs_model.py')
            input_path, _ = os.path.split(self._input_file_paths[0])
            variables['reference_data_path'] = input_path
            variables['ref_name'] = self.comparison
            variables['reference_name'] = config['simulations'][self.comparison]['short_name']
        # remove previous run script if it exists
        if os.path.exists(param_template_out):
            os.remove(param_template_out)
        render(
            variables=variables,
            input_path=template_input_path,
            output_path=param_template_out)

        cmd = ['e3sm_diags', '-p', param_template_out]
        self._has_been_executed = True
        return self._submit_cmd_to_manager(config, cmd, event_list)
    # -----------------------------------------------

    def postvalidate(self, config, *args, **kwargs):
        """
        Check that all the links created by the diagnostic are correct

        Parameters
        ----------
            config (dict): the global config object
        Returns
        -------
            True if all links are found
            False otherwise
        """
        return self._check_links(config)
    # -----------------------------------------------

    def handle_completion(self, filemanager, event_list, config, *args, **kwargs):
        """
        Perform setup for webhosting

        Parameters
        ----------
            event_list (EventList): an event list to push user notifications into
            config (dict): the global config object
        """
        if self.status != JobStatus.COMPLETED:
            msg = '{prefix}: Job failed'.format(
                prefix=self.msg_prefix())
            print_line(msg, event_list)
            logging.info(msg)
        else:
            msg = '{prefix}: Job complete'.format(
                prefix=self.msg_prefix())
            print_line(msg, event_list)
            logging.info(msg)

        # if hosting is turned off, simply return
        if not config['global'].get('host'):
            return

        self.setup_hosting(
            always_copy=config['global'].get('always_copy', False),
            img_source=self._output_path,
            host_path=self._host_path,
            event_list=event_list)

        self._host_url = 'https://{server}/{prefix}/{case}/e3sm_diags/{start:04d}_{end:04d}_vs_{comp}/viewer/index.html'.format(
            server=config['img_hosting']['img_host_server'],
            prefix=config['img_hosting']['url_prefix'],
            case=self.short_name,
            start=self.start_year,
            end=self.end_year,
            comp=self._short_comp_name)
    # -----------------------------------------------

    def _check_links(self, config):

        viewer_path = os.path.join(self._output_path, 'viewer', 'index.html')
        if not os.path.exists(viewer_path):
            msg = '{}: could not find page index at {}'.format(
                self.msg_prefix(), viewer_path)
            logging.error(msg)
            return False
        viewer_head = os.path.join(self._output_path, 'viewer')
        if not os.path.exists(viewer_head):
            msg = '{}: could not find output viewer at {}'.format(
                self.msg_prefix(), viewer_head)
            logging.error(msg)
            return False
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
                                sublink_path = os.path.join(
                                    link_tail, sublink_preview)
                                if not os.path.exists(sublink_path):
                                    missing_links.append(sublink_path)
        if missing_links:
            msg = '{prefix}: missing the following links'.format(
                prefix=self.msg_prefix())
            logging.error(msg)
            logging.error(missing_links)
            return False
        else:
            msg = '{prefix}: all links found'.format(
                prefix=self.msg_prefix())
            logging.info(msg)
            return True
    # -----------------------------------------------
