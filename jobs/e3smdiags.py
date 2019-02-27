"""
A wrapper class around E3SM Diags
"""
import os
import logging

from bs4 import BeautifulSoup

from jobs.diag import Diag
from lib.util import render, print_line
from lib.jobstatus import JobStatus


class E3SMDiags(Diag):
    def __init__(self, *args, **kwargs):
        super(E3SMDiags, self).__init__(*args, **kwargs)
        self._job_type = 'e3sm_diags'
        self._requires = 'climo'
        self._data_required = ['climo_regrid']
        self._host_path = ''
        self._host_url = ''
        self._short_comp_name = ''
        custom_args = kwargs['config']['diags']['e3sm_diags'].get(
            'custom_args')
        if custom_args:
            self.set_custom_args(custom_args)
        if self.comparison == 'obs':
            self._short_comp_name = 'obs'
        else:
            self._short_comp_name = kwargs['config']['simulations'][self.comparison]['short_name']
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
            config (dict): the globus processflow config object
            dryrun (bool): a flag to denote that all the data should be set,
                and the scripts generated, but not actually submitted
        """
        self._dryrun = dryrun

        # setup the jobs output path, creating it if it doesnt already exist
        self._output_path = os.path.join(
            config['global']['project_path'],
            'output', 'diags', self.short_name, 'e3sm_diags',
            '{start:04d}_{end:04d}_vs_{comp}'.format(
                start=self.start_year,
                end=self.end_year,
                comp=self._short_comp_name))
        if not os.path.exists(self._output_path):
            os.makedirs(self._output_path)

        # render the parameter file from the template
        param_template_out = os.path.join(
            config['global']['run_scripts_path'],
            'e3sm_diags_{start:04d}_{end:04d}_{case}_vs_{comp}_params.py'.format(
                start=self.start_year,
                end=self.end_year,
                case=self.short_name,
                comp=self._short_comp_name))
        variables = dict()
        input_path, _ = os.path.split(self._input_file_paths[0])
        variables['short_test_name'] = self.short_name
        variables['test_data_path'] = input_path
        variables['test_name'] = self.case
        variables['backend'] = config['diags']['e3sm_diags']['backend']
        variables['results_dir'] = self._output_path

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
        render(
            variables=variables,
            input_path=template_input_path,
            output_path=param_template_out)

        cmd = ['acme_diags_driver.py', '-p', param_template_out]
        self._has_been_executed = True
        return self._submit_cmd_to_manager(config, cmd)
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

    def handle_completion(self, file_manager, event_list, config, *args):
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
        if not config['global']['host']:
            return

        # else setup the web hosting
        hostname = config['img_hosting']['img_host_server']
        self.host_path = os.path.join(
            config['img_hosting']['host_directory'],
            self.short_name,
            'e3sm_diags',
            '{start:04d}_{end:04d}_vs_{comp}'.format(
                start=self.start_year,
                end=self.end_year,
                comp=self._short_comp_name))

        self.setup_hosting(config, self._output_path,
                           self.host_path, event_list)

        self._host_url = 'https://{server}/{prefix}/{case}/e3sm_diags/{start:04d}_{end:04d}_vs_{comp}/viewer/index.html'.format(
            server=config['img_hosting']['img_host_server'],
            prefix=config['img_hosting']['url_prefix'],
            case=self.short_name,
            start=self.start_year,
            end=self.end_year,
            comp=self._short_comp_name)
    # -----------------------------------------------

    def _check_links(self, config):

        self._output_path = os.path.join(
            config['global']['project_path'],
            'output', 'diags', self.short_name, 'e3sm_diags',
            '{start:04d}_{end:04d}_vs_{comp}'.format(
                start=self.start_year,
                end=self.end_year,
                comp=self._short_comp_name))
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
