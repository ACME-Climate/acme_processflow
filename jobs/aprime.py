import os
import re
import logging

from bs4 import BeautifulSoup
from shutil import move

from jobs.diag import Diag
from lib.util import render, print_line
from lib.jobstatus import JobStatus

class Aprime(Diag):
    def __init__(self, *args, **kwargs):
        super(Aprime, self).__init__(*args, **kwargs)
        self._job_type = 'aprime'
        self._requires = ''
        self._host_path = ''
        self._host_url = ''
        self._input_base_path = ''
        self._data_required = ['atm', 'cice', 'ocn', 
                               'ocn_restart', 'cice_restart', 
                               'ocn_streams', 'cice_streams', 
                               'ocn_in', 'cice_in', 
                               'meridionalHeatTransport']
        custom_args = kwargs['config']['diags']['aprime'].get('custom_args')
        if custom_args:
            self.set_custom_args(custom_args)
        if self.comparison == 'obs':
            self._short_comp_name = 'obs'
        else:
            self._short_comp_name = kwargs['config']['simulations'][self.comparison]['short_name']
    # -----------------------------------------------
    def setup_dependencies(self, *args, **kwargs):
        """
        aprime doesnt depend on any other jobs
        """
        return
    # -----------------------------------------------
    def execute(self, config, event_list, dryrun=False):
        """
        Generates and submits a run script for ncremap to regrid model output
        
        Parameters
        ----------
            config (dict): the globus processflow config object
            dryrun (bool): a flag to denote that all the data should be set, and the scripts generated, but not actually submitted
        """

        # sets up the output path, creating it if it doesnt already exist
        self._output_path = os.path.join(
            config['global']['project_path'],
            'output', 'diags', self.short_name, 'aprime',
            '{start:04d}_{end:04d}_vs_{comp}'.format(
                start=self.start_year,
                end=self.end_year,
                comp=self._short_comp_name))
        if not os.path.exists(self._output_path):
            os.makedirs(self._output_path)

        
        # fix the input paths
        self._fix_input_paths()
        
        self._host_path = os.path.join(
            config['img_hosting']['host_directory'],
            self.short_name,
            'aprime')
        
        # setup template
        template_out = os.path.join(
            config['global']['run_scripts_path'],
            'aprime_{start:04d}_{end:04d}_{case}_vs_{comp}.bash'.format(
                start=self.start_year,
                end=self.end_year,
                case=self.short_name,
                comp=self._short_comp_name))
        variables = dict()
        variables['test_casename'] = self.case
        variables['output_base_dir'] = self._output_path
        variables['test_archive_dir'] = self._input_base_path + os.sep
        variables['test_atm_res'] = config['simulations'][self.case]['native_grid_name']
        variables['test_mpas_mesh_name'] = config['simulations'][self.case]['native_mpas_grid_name']
        variables['test_begin_yr_climo'] = self.start_year
        variables['test_end_yr_climo'] = self.end_year
        variables['www_dir'] = self._host_path

        template_input_path = os.path.join(
            config['global']['resource_path'],
            'aprime_template_vs_obs.bash')
        
        render(
            variables=variables,
            input_path=template_input_path,
            output_path=template_out)

        aprime_code_path = config['diags']['aprime']['aprime_code_path']
        cmd = [
            'cd {}\n'.format(aprime_code_path),
            'bash', template_out]
        self._has_been_executed = True
        return self._submit_cmd_to_manager(config, cmd)
    # -----------------------------------------------
    def postvalidate(self, config, *args, **kwargs):
        
        if not self._output_path:
            self._output_path = os.path.join(
            config['global']['project_path'],
            'output', 'diags', self.short_name, 'aprime',
            '{start:04d}_{end:04d}_vs_{comp}'.format(
                start=self.start_year,
                end=self.end_year,
                comp=self._short_comp_name))
            if not os.path.exists(self._output_path):
                os.makedirs(self._output_path)

        self._host_path = os.path.join(
            config['img_hosting']['host_directory'],
            self.short_name,
            'aprime')
        num_missing = self._check_links(config)

        if num_missing is not None and num_missing == 0:
            return True
        else:
            if self._has_been_executed:
                msg = '{prefix}: Job completed but missing {num_missing} plots'.format(
                    prefix=self.msg_prefix(),
                    num_missing=num_missing)
                logging.error(msg)
            return False
    # -----------------------------------------------
    def handle_completion(self, filemanager, event_list, config):
        
        if self.status != JobStatus.COMPLETED:
            msg = '{prefix}: Job failed'.format(
                prefix=self.msg_prefix(),
                case=self._short_name)
            print_line(msg, event_list)
            logging.info(msg)
        else:
            msg = '{prefix}: Job complete'.format(
                prefix=self.msg_prefix(),
                case=self._short_name)
            print_line(msg, event_list)
            logging.info(msg)
        
        # if hosting is turned off, simply return
        if not config['global']['host']:
            return

        img_source = os.path.join(
            self._output_path,
            'coupled_diagnostics',
            '{case}_vs_{comp}'.format(case=self.case, comp=self._short_comp_name),
            '{case}_years{start}-{end}_vs_{comp}'.format(
                case=self.case,
                start=self.start_year,
                end=self.end_year,
                comp=self._short_comp_name))

        # setup the web hosting
        self._host_path = os.path.join(
            config['img_hosting']['host_directory'],
            self.short_name,
            'aprime')
        
        self._host_url = 'https://{server}/{prefix}/{short_name}/aprime/{case}_years{start}-{end}_vs_{comp}/index.html'.format(
            server=config['img_hosting']['img_host_server'],
            prefix=config['img_hosting']['url_prefix'],
            short_name=self.short_name,
            case=self.case,
            start=self.start_year,
            end=self.end_year,
            comp=self._short_comp_name)
    # -----------------------------------------------
    def _check_links(self, config):
        """
        Check that all the links exist in the output page
        returns True if all the links are found, False otherwise
        """
        found = False
        host_directory = "{case}_years{start}-{end}_vs_{comp}".format(
            case=self.case,
            start=self.start_year,
            end=self.end_year,
            comp=self._short_comp_name)

        web_dir = os.path.join(
            self._host_path,
            host_directory)

        page_path = os.path.join(web_dir, 'index.html')

        if not os.path.exists(page_path):
            msg = '{prefix}: No output page found at {outpath}'.format(
                prefix=self.msg_prefix(),
                outpath=page_path)
            logging.error(msg)
            return None
        else:
            msg = '{prefix}: found output index.html at {outpath}'.format(
                prefix=self.msg_prefix(),
                outpath=page_path)
            logging.info(msg)

        missing_pages = list()
        with open(page_path, 'r') as fp:
            page = BeautifulSoup(fp, 'lxml')
            links = page.findAll('a')
            for link in links:
                link_path = os.path.join(web_dir, link.attrs['href'])
                if not os.path.exists(link_path):
                    missing_pages.append(link.attrs['href'])

        if missing_pages:
            msg = '{prefix}: missing some output images'.format(
                prefix=self.msg_prefix())
            logging.error(msg)
            logging.error(missing_pages)
            return len(missing_pages)
        else:
            msg = '{prefix}: all links found'.format(
                prefix=self.msg_prefix())
            logging.info(msg)
            return 0
    # -----------------------------------------------
    def _fix_input_paths(self):
        """
        Aprime has some hardcoded paths setup that have to be fixed or it will crash
        """
        tail, head = os.path.split(self._input_file_paths[0])
        self._input_base_path = tail
        fixed_input_path = os.path.join(
            tail, self.case, 'run')

        if not os.path.exists(fixed_input_path):
            os.makedirs(fixed_input_path)

        for idx, item in enumerate(self._input_file_paths):
            # move the input file, then update the pointer
            path, name = os.path.split(item)
            new_path = os.path.join(
                fixed_input_path, name)
            if os.path.exists(new_path):
                self._input_file_paths[idx] = new_path
                continue
            move(item, fixed_input_path)
            self._input_file_paths[idx] = new_path
    # -----------------------------------------------