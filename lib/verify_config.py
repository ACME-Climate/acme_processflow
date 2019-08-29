"""
A module to varify that the user config is valid
"""
import os


def verify_config(config):
    messages = list()
    # ------------------------------------------------------------------------
    # check that each mandatory section exists
    # ------------------------------------------------------------------------
    if not config.get('simulations'):
        msg = 'No simulations section found in config'
        messages.append(msg)
    if not config.get('global'):
        msg = 'No global section found in config'
        messages.append(msg)
    else:
        if not config['global'].get('project_path'):
            msg = 'no project_path in global options'
            messages.append(msg)
    if not config.get('data_types'):
        msg = 'No data_types section found in config'
        messages.append(msg)
    if messages:
        return messages
    # ------------------------------------------------------------------------
    # check simulations
    # ------------------------------------------------------------------------
    if not config['simulations'].get('start_year'):
        msg = 'no start_year set for simulations'
        messages.append(msg)
    else:
        config['simulations']['start_year'] = int(
            config['simulations']['start_year'])
    if not config['simulations'].get('end_year'):
        msg = 'no end_year set for simulations'
        messages.append(msg)
    else:
        config['simulations']['end_year'] = int(
            config['simulations']['end_year'])
    for sim in config.get('simulations'):
        if sim in ['start_year', 'end_year']:
            continue
        if config['simulations'][sim].get('comparisons'):
            if not isinstance(config['simulations'][sim]['comparisons'], list):
                config['simulations'][sim]['comparisons'] = [
                    config['simulations'][sim]['comparisons']]
        if not config['simulations'][sim].get('transfer_type'):
            msg = '{} is missing trasfer_type, if the data is local, set transfer_type to \'local\''.format(
                sim)
            messages.append(msg)
        else:
            if config['simulations'][sim]['transfer_type'] == 'globus' and not config['simulations'][sim].get('remote_uuid'):
                msg = 'case {} has transfer_type of globus, but is missing remote_uuid'.format(
                    sim)
                messages.append(msg)
            elif config['simulations'][sim]['transfer_type'] == 'sftp' and not config['simulations'][sim].get('remote_hostname'):
                msg = 'case {} has transfer_type of sftp, but is missing remote_hostname'.format(
                    sim)
                messages.append(msg)
            if config['simulations'][sim]['transfer_type'] == 'globus' and not config['global'].get('local_globus_uuid'):
                msg = 'case {} is set to use globus, but no local_globus_uuid was set in the global options'.format(
                    sim)
                messages.append(msg)
            if config['simulations'][sim]['transfer_type'] != 'local' and not config['simulations'][sim].get('remote_path'):
                msg = 'case {} has non-local data, but no remote_path given'.format(
                    sim)
                messages.append(msg)
            if config['simulations'][sim]['transfer_type'] == 'local' and not config['simulations'][sim].get('local_path'):
                msg = 'case {} is set for local data, but no local_path is set'.format(
                    sim)
                messages.append(msg)
        if not config['simulations'][sim].get('local_path'):
            config['simulations'][sim]['local_path'] = os.path.join(
                config['global']['project_path'],
                'input',
                sim)
        if int(config['simulations'].get('end_year', 0)) < int(config['simulations'].get('start_year', 0)):
            msg = 'simulation end_year is less then start_year, is time going backwards!?'
            messages.append(msg)
        if not config['simulations'][sim].get('data_types'):
            msg = 'no data_types found for {}, set to \'all\' to select all types, or list only data_types desired'.format(
                sim)
            messages.append(msg)
            continue
        if not isinstance(config['simulations'][sim]['data_types'], list):
            config['simulations'][sim]['data_types'] = [
                config['simulations'][sim]['data_types']]
        for data_type in config['simulations'][sim]['data_types']:
            if data_type == 'all':
                continue
            if data_type not in config['data_types']:
                msg = '{} is set to use data_type {}, but this data type is not in the data_types config option'.format(
                    sim, data_type)
                messages.append(msg)
        if config['simulations'][sim].get('job_types'):
            if not isinstance(config['simulations'][sim]['job_types'], list):
                config['simulations'][sim]['job_types'] = [
                    config['simulations'][sim]['job_types']]
            for job_type in config['simulations'][sim]['job_types']:
                if job_type == 'all':
                    continue
                if job_type not in config.get('post-processing', []) and job_type not in config.get('diags', []):
                    msg = '{} is set to run job {}, but this run type is not in either the post-processing or diags config sections'.format(
                        sim, job_type)
                    messages.append(msg)

    # ------------------------------------------------------------------------
    # check data_types
    # ------------------------------------------------------------------------
    for ftype in config.get('data_types'):
        if not config['data_types'][ftype].get('file_format'):
            msg = '{} has no file_format'.format(ftype)
            messages.append(msg)
        if not config['data_types'][ftype].get('remote_path'):
            all_local = True
            for sim in config['simulations']:
                if sim in ['start_year', 'end_year']:
                    continue
                if config['simulations'][sim]['transfer_type'] != 'local':
                    all_local = False
                    break
            if not all_local:
                msg = '{} has no remote_path'.format(ftype)
                messages.append(msg)
            config['data_types'][ftype]['remote_path'] = ''
        if not config['data_types'][ftype].get('local_path'):
            msg = '{} has no local_path'.format(ftype)
            messages.append(msg)
        if config['data_types'][ftype].get('monthly') == 'True':
            config['data_types'][ftype]['monthly'] = True
        if config['data_types'][ftype].get('monthly') == 'False':
            config['data_types'][ftype]['monthly'] = False
    # ------------------------------------------------------------------------
    # check img_hosting
    # ------------------------------------------------------------------------
    if config.get('img_hosting'):
        if not config['img_hosting'].get('img_host_server'):
            msg = 'image hosting is turned on, but no img_host_server specified'
            messages.append(msg)
        if not config['img_hosting'].get('host_directory'):
            msg = 'image hosting is turned on, but no host_directory specified'
            messages.append(msg)

    if config.get('post-processing'):
        # ------------------------------------------------------------------------
        # check regrid
        # ------------------------------------------------------------------------
        if config['post-processing'].get('regrid'):
            for item in config['post-processing']['regrid']:
                if item in ['destination_grid_name']:
                    continue
                if item == 'lnd':
                    if not config['post-processing']['regrid'][item].get('source_grid_path'):
                        msg = 'no source_grid_path given for {} regrid'.format(
                            item)
                        messages.append(msg)
                    if not config['post-processing']['regrid'][item].get('destination_grid_path'):
                        msg = 'no destination_grid_path given for {} regrid'.format(
                            item)
                        messages.append(msg)
                    if not config['post-processing']['regrid'][item].get('destination_grid_name'):
                        msg = 'no destination_grid_name given for {} regrid'.format(
                            item)
                        messages.append(msg)
                else:
                    if not config['post-processing']['regrid'][item].get('regrid_map_path'):
                        msg = 'no regrid_map_path given for {} regrid'.format(
                            item)
                        messages.append(msg)
                for sim in config['simulations']:
                    if sim in ['start_year', 'end_year']:
                        continue
                    if 'all' not in config['simulations'][sim].get('data_types'):
                        if item not in config['simulations'][sim].get('data_types') and ('regrid' in config['simulations'][sim]['job_types'] or 'all' in config['simulations'][sim]['job_types']):
                            msg = 'regrid is set to run on data_type {}, but this type is not set in simulation {}'.format(
                                item, sim)
                            messages.append(msg)
        # ------------------------------------------------------------------------
        # check ncclimo
        # ------------------------------------------------------------------------
        if config['post-processing'].get('climo'):
            if not config['post-processing']['climo'].get('regrid_map_path'):
                msg = 'no regrid_map_path given for climo'
                messages.append(msg)
            if not config['post-processing']['climo'].get('destination_grid_name'):
                msg = 'no destination_grid_name given for climo'
                messages.append(msg)
            if not config['post-processing']['climo'].get('run_frequency'):
                msg = 'no run_frequency given for ncclimo'
                messages.append(msg)
            else:
                if not isinstance(config['post-processing']['climo'].get('run_frequency'), list):
                    config['post-processing']['climo']['run_frequency'] = [
                        config['post-processing']['climo']['run_frequency']]
            for sim in config['simulations']:
                if sim in ['start_year', 'end_year']:
                    continue
                if sim == 'comparisons':
                    msg = 'You may be using an old config format, comparisons are now inside each case'
                    messages.append(msg)
                if 'all' not in config['simulations'][sim].get('data_types'):
                    if 'atm' not in config['simulations'][sim].get('data_types'):
                        msg = 'ncclimo is set to run for simulation {}, but this simulation does not have atm in its data_types'.format(
                            sim)
                        messages.append(msg)
        # ------------------------------------------------------------------------
        # check timeseries
        # ------------------------------------------------------------------------
        if config['post-processing'].get('timeseries'):
            if not config['post-processing']['timeseries'].get('run_frequency'):
                msg = 'no run_frequency given for timeseries'
                messages.append(msg)
            else:
                if not isinstance(config['post-processing']['timeseries'].get('run_frequency'), list):
                    config['post-processing']['timeseries']['run_frequency'] = [
                        config['post-processing']['timeseries']['run_frequency']]
            for item in config['post-processing']['timeseries']:
                if item in ['run_frequency', 'regrid_map_path', 'destination_grid_name', 'custom_args']:
                    continue
                if item not in ['atm', 'lnd', 'ocn']:
                    msg = '{} is an unsupported timeseries data type'.format(
                        item)
                    messages.append(msg)
                if config['simulations'][sim].get('job_types') and 'all' not in config['simulations'][sim].get('job_types'):
                    if 'timeseries' not in config['simulations'][sim].get('job_types'):
                        continue
                if not isinstance(config['post-processing']['timeseries'][item], list):
                    config['post-processing']['timeseries'][item] = [
                        config['post-processing']['timeseries'][item]]
                for sim in config['simulations']:
                    if sim in ['start_year', 'end_year']:
                        continue
                    if 'all' not in config['simulations'][sim].get('data_types'):
                        if item not in config['simulations'][sim].get('data_types') and ('timeseries' in config['simulations'][sim]['job_types'] or 'all' in config['simulations'][sim]['job_types']):
                            msg = 'timeseries-{} is set to run for simulation {}, but this simulation does not have {} in its data_types'.format(
                                item, sim, item)
                            messages.append(msg)
        # ------------------------------------------------------------------------
        # check cmor
        # ------------------------------------------------------------------------
        if config['post-processing'].get('cmor'):
            if not config['post-processing']['cmor'].get('run_frequency'):
                msg = 'no run_frequency given for cmor, make sure this matches the frequency for timeseries'
                messages.append(msg)
            else:
                if not isinstance(config['post-processing']['cmor'].get('run_frequency'), list):
                    config['post-processing']['cmor']['run_frequency'] = [
                        config['post-processing']['cmor']['run_frequency']]
            if not config['post-processing']['cmor'].get('variable_list'):
                msg = 'no variable list given for cmor, please provide a list of E3SM variables to convert to CMIP6 format'
                messages.append(msg)
            elif not config['post-processing'].get('timeseries'):
                msg = "the cmor job requires timeseries file generation, add a timeseries job to enable cmor"
                messages.append(msg)
            else:
                if not isinstance(config['post-processing']['cmor']['variable_list'], list):
                    config['post-processing']['cmor']['variable_list'] = [
                        config['post-processing']['cmor']['variable_list']]
                for variable in config['post-processing']['cmor']['variable_list']:
                    if variable not in config['post-processing']['timeseries'].get('atm', list()) and variable not in config['post-processing']['timeseries'].get('lnd', list()) and variable not in config['post-processing']['timeseries'].get('ocn', list()) and variable != 'all':
                        msg = 'variable {} is in the cmor variable_list but not present in the timeseries list, all cmor input variables must first be extracted as timeseries varibles'.format(
                            variable)
                        messages.append(msg)
            for sim in config['post-processing']['cmor']:
                if sim not in config['simulations']:
                    continue
                if not config['post-processing']['cmor'][sim].get('user_input_json_path'):
                    msg = 'simulation case {} is set to be cmorized, but no user_input json file path provided'.format(
                        sim)
                    messages.append(msg)
                else:
                    if not os.path.exists(config['post-processing']['cmor'][sim].get('user_input_json_path')):
                        msg = 'provided user_input_json_path {} doesnt exist.'
                        messages.append(msg)
            if not config['post-processing']['cmor'].get('cmor_tables_path'):
                msg = 'please provide a path to where to find the master cmor tables. A copy of the tables can be found here: https://github.com/PCMDI/cmor'
                messages.append(msg)
            else:
                if not os.path.exists(config['post-processing']['cmor']['cmor_tables_path']):
                    msg = 'provided cmor_tables_path {} points to a directory that doesnt exist. Download a copy from https://github.com/PCMDI/cmor'.format(
                        config['post-processing']['cmor']['cmor_tables_path'])
                    messages.append(msg)

    if config.get('diags'):
        # ------------------------------------------------------------------------
        # check e3sm_diags
        # ------------------------------------------------------------------------
        if config['diags'].get('e3sm_diags'):
            if not config['diags']['e3sm_diags'].get('backend'):
                msg = 'no backend given for e3sm_diags'
                messages.append(msg)
            if not config['diags']['e3sm_diags'].get('reference_data_path'):
                msg = 'no reference_data_path given for e3sm_diags'
                messages.append(msg)
            if not config['diags']['e3sm_diags'].get('run_frequency'):
                msg = 'no run_frequency given for e3sm_diags'
                messages.append(msg)
            else:
                if not isinstance(config['diags']['e3sm_diags'].get('run_frequency'), list):
                    config['diags']['e3sm_diags']['run_frequency'] = [
                        config['diags']['e3sm_diags']['run_frequency']]

                for freq in config['diags']['e3sm_diags']['run_frequency']:
                    for sim in config['simulations']:
                        if sim in ['start_year', 'end_year']:
                            continue
                        if 'e3sm_diags' in config['simulations'][sim].get('job_types') \
                                and 'climo' not in config['simulations'][sim].get('job_types'):
                            msg = 'e3sm_diags is set to run for case {case} at {freq}yr frequency, but no climo job is set in its config. Add "climo" to the cases job list, or set the jobs to "all" to run all defined jobs'.format(
                                case=sim,
                                freq=freq)
                            messages.append(msg)
                    if not config.get('post-processing') \
                            or not config['post-processing'].get('climo') \
                            or not freq in config['post-processing']['climo']['run_frequency']:
                        msg = 'e3sm_diags is set to run at frequency {} but no climo job for this frequency is set'.format(
                            freq)
                        messages.append(msg)
        # ------------------------------------------------------------------------
        # check amwg
        # ------------------------------------------------------------------------
        if config['diags'].get('amwg'):
            if not config['diags']['amwg'].get('diag_home'):
                msg = 'no diag_home given for amwg'
                messages.append(msg)
            if not config['diags']['amwg'].get('run_frequency'):
                msg = 'no diag_home given for amwg'
                messages.append(msg)
            else:
                if not isinstance(config['diags']['amwg'].get('run_frequency'), list):
                    config['diags']['amwg']['run_frequency'] = [
                        config['diags']['amwg']['run_frequency']]
                if 'amwg' in config['simulations'][sim].get('job_types') \
                        and 'climo' not in config['simulations'][sim].get('job_types'):
                    msg = 'amwg is set to run for case {case} but no climo job is set in its config. Add "climo" to the cases job list, or set the jobs to "all" to run all defined jobs'.format(
                        case=sim,
                        freq=freq)
                    messages.append(msg)
                for freq in config['diags']['amwg']['run_frequency']:
                    if not config.get('post-processing') \
                            or not config['post-processing'].get('climo') \
                            or not freq in config['post-processing']['climo']['run_frequency']:
                        msg = 'amwg is set to run at frequency {} but no climo job for this frequency is set'.format(
                            freq)
                        messages.append(msg)
            if not config['diags']['amwg'].get('sets'):
                msg = 'no sets given for amwg'
                messages.append(msg)
            else:
                allowed_sets = [str(x) for x in range(1, 17)] + ['all', '4a']
                if not isinstance(config['diags']['amwg']['sets'], list):
                    config['diags']['amwg']['sets'] = [
                        config['diags']['amwg']['sets']]
                for s in config['diags']['amwg']['sets']:
                    if s not in allowed_sets:
                        msg = '{} is not in the allowed sets for amwg, allowed sets are {}'.format(
                            s, allowed_sets)
                        messages.append(msg)
        # ------------------------------------------------------------------------
        # check aprime
        # ------------------------------------------------------------------------
        if config['diags'].get('aprime'):
            if not config['diags']['aprime'].get('run_frequency'):
                msg = 'no run_frequency given for aprime'
                messages.append(msg)
            else:
                if not isinstance(config['diags']['aprime']['run_frequency'], list):
                    config['diags']['aprime']['run_frequency'] = [
                        config['diags']['aprime']['run_frequency']]
            if not config['diags']['aprime'].get('aprime_code_path'):
                msg = 'no aprime_code_path given for aprime'
                messages.append(msg)
        # ------------------------------------------------------------------------
        # check MPAS-Analysis
        # ------------------------------------------------------------------------
        if config['diags'].get('mpas_analysis'):
            if not config['diags']['mpas_analysis'].get('run_frequency'):
                msg = 'no run_frequency given for MPAS-analysis'
                messages.append(msg)
            else:
                if not isinstance(config['diags']['mpas_analysis']['run_frequency'], list):
                    config['diags']['mpas_analysis']['run_frequency'] = [
                        config['diags']['mpas_analysis']['run_frequency']]
            required_parameters = ['mapping_directory', 'generate_plots', 'start_year_offset',
                                   'ocn_obs_data_path', 'seaice_obs_data_path', 'region_mask_path', 'run_MOC']
            for param in required_parameters:
                if not config['diags']['mpas_analysis'].get(param):
                    msg = 'Missing parameter {p} is required for MPAS-Analysis'.format(
                        p=param)
                    messages.append(msg)
            if not isinstance(config['diags']['mpas_analysis'].get('generate_plots', ''), list):
                config['diags']['mpas_analysis']['generate_plots'] = [
                    config['diags']['mpas_analysis'].get('generate_plots', '')]
        # ------------------------------------------------------------------------
        # check ILAMB
        # ------------------------------------------------------------------------
        if config['diags'].get('ilamb'):
            if not config['diags']['ilamb'].get('run_frequency'):
                msg = 'no run_frequency given for ILAMB'
                messages.append(msg)
            else:
                if not isinstance(
                        config['diags']['ilamb']['run_frequency'], list):
                    config['diags']['ilamb']['run_frequency'] = [
                        config['diags']['ilamb']['run_frequency']]
            if not config['diags']['ilamb'].get('ilamb_root'):
                msg = 'no ilamb_root given for ILAMB'
                messages.append(msg)
    return messages
# ------------------------------------------------------------------------


def check_config_white_space(filepath):
    line_index = 0
    found = False
    with open(filepath, 'r') as infile:
        for line in infile.readlines():
            line_index += 1
            index = line.find('=')
            if index == -1:
                found = False
                continue
            if line[index + 1] != ' ':
                found = True
                break
    if found:
        return line_index
    else:
        return 0
# ------------------------------------------------------------------------
