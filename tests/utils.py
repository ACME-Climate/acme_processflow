import os
import json
from configobj import ConfigObj

from processflow.lib.filemanager import FileStatus

def touch(fname):

    if os.path.exists(fname):
        return
    tail, _ = os.path.split(fname)
    if not os.path.exists(tail):
        os.makedirs(tail)
    with open(fname, 'w') as fp:
        fp.write('\n')

# generate mock files that match the expected ncclimo output
def mock_climos(output_path, regrid_path, config, filemanager, case):
    climo_files = list()
    regrid_files = list()
    for month in range(1, 13):
        name = '{case}_{month:02d}_0001{month:02d}_0002{month:02d}_climo.nc'.format(
            case=case,
            month=month)
        outpath = os.path.join(output_path, name)
        touch(outpath)
        climo_files.append(outpath)

        outpath = os.path.join(regrid_path, name)
        touch(outpath)
        regrid_files.append(outpath)
    
    for season in ['ANN_000101_000212', 'DJF_000101_000212', 'JJA_000106_000208', 'MAM_000103_000205', 'SON_000109_000211']:
        name = '{case}_{season}_climo.nc'.format(
            case=case,
            season=season)
        outpath = os.path.join(output_path, name)

        touch(outpath)
        climo_files.append(outpath)

        outpath = os.path.join(regrid_path, name)
        touch(outpath)
        regrid_files.append(outpath)
    
    new_files = list()
    for fname in climo_files:
        new_files.append({
            'name': fname,
            'local_path': os.path.join(regrid_path, fname),
            'case': case,
            'year': 1,
            'month': 2,
            'local_status': FileStatus.PRESENT.value
        })
    filemanager.add_files(
        data_type='climo_native',
        file_list=new_files,
        super_type='derived')
    
    new_files = list()
    for fname in regrid_files:
        new_files.append({
            'name': fname,
            'local_path': os.path.join(output_path, fname),
            'case': case,
            'year': 1,
            'month': 2,
            'local_status': FileStatus.PRESENT.value
        })
    filemanager.add_files(
        data_type='climo_regrid',
        file_list=new_files,
        super_type='derived')

    config['data_types']['climo_regrid'] = {
        'monthly': True
    }
    config['data_types']['climo_native'] = {
        'monthly': True
    }

def mock_ts(variables, output_path, regrid_path, start_year, end_year):
    # create some dummy files for the post validator
    for var in variables:
        file_name = "{var}_{start:04d}01_{end:04d}12.nc".format(
            var=var,
            start=start_year,
            end=end_year)
        file_path = os.path.join(output_path, file_name)
        touch(file_path)
        file_path = os.path.join(regrid_path, file_name)
        touch(file_path)

def mock_atm(start_year, end_year, caseid, path):

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            name = '{caseid}.cam.h0.{year:04d}-{month:02d}.nc'.format(
                caseid=caseid,
                year=year,
                month=month)
            touch(
                os.path.join(
                    path, name))

def json_to_conf(input, output, variables):

    with open(input, 'r') as infile:
        data = json.load(infile)
    
    for key, value in variables.items():
        data[key] = value

    conf = ConfigObj(data)

    with open(output, 'w') as outfile:
        conf.write(outfile)
