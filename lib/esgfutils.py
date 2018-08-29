"""
Utilities for ESGF data handling
"""
import os
from subprocess import call
from models import DataFile
from shutil import move, copy


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
    makedir(casename)
    res_dir = os.path.join(
        basepath,
        casename,
        '{atm_res}_atm_{ocn_res}_ocean'.format(
            atm_res=atmos_res,
            ocn_res=ocean_res))
    makedir(res_dir)
    for dtype in data_types:
        dtype_dir = os.path.join(res_dir, dtype)
        makedir(dtype_dir)
        grid_dir = os.path.join(dtype_dir, 'native')
        makedir(grid_dir)
        makedir(os.path.join(
            grid_dir, 'model-output', 'mon', 'ens1', 'v1'))
        if dtype in ['atmos', 'land']:
            for grid in grids:
                grid_dir = os.path.join(dtype_dir, grid)
                makedir(grid_dir)
                makedir(os.path.join(
                    grid_dir, 'model-output', 'mon', 'ens1', 'v1'))
                if dtype == 'atmos' and grid != 'native':
                    makedir(os.path.join(grid_dir, 'climo',
                                         'monClim', 'ens1', 'v1'))
                    makedir(os.path.join(grid_dir, 'climo',
                                         'seasonClim', 'ens1', 'v1'))
                    makedir(os.path.join(
                        grid_dir, 'time-series', 'mon', 'ens1', 'v1'))
        cmd = 'chmod -R a+rx {}'.format(casename)
        call(cmd)

def move_or_copy(basepath, config, mode, case):
    """
    Move or copy data into the ESGF publication structure

    Parameters
    ----------
        basepath (str): the base of the ESGF publication structure
        config (dict): the global config object
        mode (str): either 'move' or 'copy'
        database (str): the path to the file database
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
        config['simulations'][case]['short_name']))

    allowed_datatypes = [
        'atm', 'atm_regrid', 'atm_ts_regrid', 'climo_regrid',
        'lnd', 'lnd_regrid', 'ocn', 'ice']

    q = DataFile.select().where(DataFile.case == case)
    for datafile in q.execute():
        if datafile.datatype not in ['atm', 'lnd', 'ocn', 'ice']:
            if 'ts' in datafile.datatype:
                grid = config['post-processing']['timeseries']['destination_grid_name']
            else:
                grid = config['post-processing']['regrid']['destination_grid_name']
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
            datatype=datafile.datatype)
        transfer(
            src=src,
            dst=dst)

def _setup_dst(short_name, basepath, res_dir, grid, datatype):
    """"""
    if datatype in ['atm', 'atm_regrid', 'atm_ts_regrid', 'climo_regrid']:
        type_dir = 'atmos'
        if datatype == 'atm':
            output_type = 'model-output'
        elif datatype == 'atm_ts_regrid':
            output_type = 'time-series'
        elif datatype == 'climo_regrid':
            output_type = 'climo'
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
        'mon',
        'ens1',
        'v1')

def makedir(directory):
    """
    Make a directory if it doesnt already exist
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
