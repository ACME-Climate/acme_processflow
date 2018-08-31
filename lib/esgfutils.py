"""
Utilities for ESGF data handling
"""
import os
from subprocess import call
from models import DataFile
from shutil import move, copy

from lib.util import print_message


def structure_gen(basepath, casename, grids, atmos_res, ocean_res):
    """
    generate the esgf publication structure

    Parameters
    ----------
        casename (str): the name of the run
        grids (list(str)): any grids in addition to native that are being published
        atmos_res (str): the atmospheric resolution i.e. 1deg
        ocean_res (str): the ocean resolution i.e. 60-30km

    """
    data_types = ['atmos', 'land', 'ocean', 'sea-ice']
    res_dir = os.path.join(
        basepath,
        casename,
        '{atm_res}_atm_{ocn_res}_ocean'.format(
            atm_res=atmos_res,
            ocn_res=ocean_res))
    makedir(res_dir)
    for dtype in data_types:
        dtype_dir = os.path.join(res_dir, dtype)
        grid_dir = os.path.join(dtype_dir, 'native')
        makedir(grid_dir)
        makedir(
            os.path.join(
                grid_dir,
                'model-output',
                'mon',
                'ens1',
                'v1'))
        if dtype in ['atmos', 'land']:
            for grid in grids:
                grid_dir = os.path.join(dtype_dir, grid)
                makedir(grid_dir)
                makedir(os.path.join(
                    grid_dir,
                    'model-output',
                    'mon',
                    'ens1',
                    'v1'))
                if dtype == 'atmos' and grid != 'native':
                    makedir(
                        os.path.join(
                            grid_dir,
                            'climo',
                            'monClim',
                            'ens1',
                            'v1'))
                    makedir(
                        os.path.join(
                            grid_dir,
                            'climo',
                            'seasonClim',
                            'ens1',
                            'v1'))
                    makedir(
                        os.path.join(
                            grid_dir,
                            'time-series',
                            'mon',
                            'ens1',
                            'v1'))
        cmd = ['chmod', '-R',  'a+rx', os.path.join(basepath, casename)]
        call(cmd)


def move_or_copy(basepath, config, mode, case):
    """
    Move or copy data into the ESGF publication structure

    Parameters
    ----------
        basepath (str): the base of the ESGF publication structure
        config (dict): the global config object
        mode (str): either 'move' or 'copy'
        case (str): the full name of the case
    Returns
    -------
        True if all data is moved/copied successfuly
        False otherwise
    """
    if mode not in ['copy', 'move']:
        raise Exception('{} is not a supported mode'.format(mode))
    if mode == 'move':
        transfer = move
    else:
        transfer = copy

    res_dir = os.listdir(os.path.join(
        basepath,
        config['simulations'][case]['short_name']))[0]

    allowed_datatypes = [
        'atm', 'atm_regrid', 'atm_ts_regrid', 'climo_regrid',
        'lnd', 'lnd_regrid', 'ocn', 'ice']

    count = DataFile.select().where(DataFile.case == case).count()
    progress = 0.0
    query = DataFile.select().where(DataFile.case == case)
    for datafile in query.execute():
        progress += 1
        pct_complete = (progress / count) * 100
        datatype = datafile.datatype
        if pct_complete % 5 == 0:
            msg = '\t{pct:02f} file transfers complete'.format(
                pct=pct_complete)
            print_message(msg, 'ok')
        if datatype not in ['atm', 'lnd', 'ocn', 'ice']:
            if datatype in ['atm_ts_regrid', 'lnd_ts_regrid', 'ocn_ts_regrid']:
                grid = config['post-processing']['timeseries']['destination_grid_name']
            elif datatype in ['atm_regrid', 'lnd_regrid', 'ocn_regrid']:
                if datatype == 'atm_regrid':
                    grid = config['post-processing']['regrid']['atm']['destination_grid_name']
                elif datatype == 'lnd_regrid':
                    grid = config['post-processing']['regrid']['lnd']['destination_grid_name']
                elif datatype == 'ocn_regrid':
                    grid = config['post-processing']['regrid']['ocn']['destination_grid_name']
            elif datatype == 'climo_regrid':
                grid = config['post-processing']['climo']['destination_grid_name']
        else:
            grid = 'native'
        if datafile.datatype not in allowed_datatypes:
            continue
        src = datafile.local_path
        dst = _setup_dst(
            short_name=config['simulations'][case]['short_name'],
            basepath=basepath,
            res_dir=res_dir,
            grid=grid,
            datatype=datafile.datatype,
            filename=datafile.name)
        if not os.path.exists(dst):
            transfer(src, dst)


def mapfile_gen(datapath, inipath):
    pass


def _setup_dst(short_name, basepath, res_dir, grid, datatype, filename):
    """"""
    freq = 'mon'
    if datatype in ['atm', 'atm_regrid', 'atm_ts_regrid', 'climo_regrid']:
        type_dir = 'atmos'
        if datatype == 'atm':
            output_type = 'model-output'
        elif datatype == 'atm_ts_regrid':
            output_type = 'time-series'
        elif datatype == 'climo_regrid':
            output_type = 'climo'
            if 'ANN' in filename or 'DJF' in filename or 'MAM' in filename or 'JJA' in filename or 'SON' in filename:
                freq = 'seasonClim'
            else:
                freq = 'monClim'
    elif datatype in ['lnd', 'lnd_regrid']:
        type_dir = 'land'
        output_type = 'model-output'
    elif datatype == 'ocn':
        type_dir = 'ocean'
        output_type = 'model-output'
    elif datatype == 'ice':
        type_dir = 'sea-ice'
        output_type = 'model-output'
    else:
        raise Exception('{} is an invalid data type'.format(datatype))

    return os.path.join(
        basepath,
        short_name,
        res_dir,
        type_dir,
        grid,
        output_type,
        freq,
        'ens1',
        'v1',
        filename)


def makedir(directory):
    """
    Make a directory if it doesnt already exist
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
