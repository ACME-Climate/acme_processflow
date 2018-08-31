import os
import logging
import time

from shutil import rmtree
from threading import Event

from lib.jobstatus import JobStatus
from lib.mailer import Mailer
from lib.util import print_message, print_line, print_debug
from lib.esgfutils import structure_gen, move_or_copy, mapfile_gen

def finalize(config, event_list, status, runmanager, event=None):
    if status == 1 and config['global'].get('native_grid_cleanup') in [1, '1', 'true', 'True']:
        message = 'Performing post run cleanup'
        native_cleanup(config)
    else:
        message = 'Leaving native grid files in place'
    print_message(message, 'ok')

    esgf = config.get('esgf')
    if esgf:
        message = 'Starting file structure generation for ESGF publication'
        print_message(message, 'ok')
        grids = list()
        pp = config.get('post-processing')
        if pp:
            if pp.get('climo'):
                grids.append(pp['climo']['destination_grid_name'])
            if pp.get('timeseries'):
                if pp['timeseries']['destination_grid_name'] not in grids:
                    grids.append(pp['timeseries']['destination_grid_name'])
            if pp.get('regrid'):
                for datatype in ['atm', 'lnd']:
                    if pp['regrid'].get(datatype):
                        if pp['regrid'][datatype]['destination_grid_name'] not in grids:
                            grids.append(pp['regrid'][datatype]['destination_grid_name'])
        for case in runmanager.cases:
            case_name = config['simulations'][case['case']]['short_name']
            message = 'Setting up structure for {}'.format(case_name)
            print_message(message, 'ok')
            structure_gen(
                basepath=esgf['esgf_publication_path'],
                casename=case_name,
                grids=grids,
                atmos_res=esgf['atmos_res_name'],
                ocean_res=esgf['ocean_res_name'])
            message = 'Moving data into place'
            print_message(message, 'ok')
            move_or_copy(
                basepath=esgf['esgf_publication_path'],
                config=config,
                mode=esgf['move_or_copy'],
                case=case['case'])

        if esgf.get('generate_mapfiles') == True or esgf.get('generate_mapfiles') == 'True':
            for case in runmanager.cases:
                case_name = config['simulations'][case['case']]['short_name']
                mapfile_gen(
                    basepath=esgf['esgf_publication_path'],
                    casename=case_name,
                    inipath=esgf['ini_directory_path'],
                    maxprocesses=esgf['num_cores'])

    if status == 1:
        msg = 'All processing complete'
        code = 'ok'
    else:
        msg = 'The following jobs encountered an error and were marked as failed:'
        code = 'error'
        for case in runmanager.cases:
            for job in case['jobs']:
                if job.status != JobStatus.COMPLETED:
                    msg += '\n        {}'.format(job.msg_prefix())
    print_message(msg, code)
    emailaddr = config['global'].get('email')
    if emailaddr:
        message = 'Sending notification email to {}'.format(emailaddr)
        print_message(message, 'ok')
        try:
            if status == 1:
                msg = 'Your processflow run has completed successfully\n'
                status = msg
            else:
                msg = 'One or more processflow jobs failed\n'
                status = msg
                msg += 'See log for additional details\n{}\n'.format(config['global']['log_path'])

            for case in runmanager.cases:
                msg += '==' + '='*len(case['case']) + '==\n'
                msg += ' # ' + case['case'] + ' #\n'
                msg += '==' + '='*len(case['case']) + '==\n\n'
                for job in case['jobs']:
                    msg += '\t > ' + job.get_report_string() + '\n'
                msg += '\n'

            m = Mailer(src='processflowbot@llnl.gov', dst=emailaddr)
            m.send(
                status=status,
                msg=msg)
        except Exception as e:
            print_debug(e)


    logging.info("All processes complete")

def native_cleanup(config):
    """
    Remove non-regridded output files after processflow completion
    """
    for case in config['simulations']:
        if case in ['start_year', 'end_year', 'comparisons']: continue
        native_path = os.path.join(
            config['global']['project_path'],
            'output', 'pp',
            config['simulations'][case]['native_grid_name'])
        if os.path.exists(native_path):
            try:
                rmtree(native_path)
            except OSError:
                return False
    
    return True
