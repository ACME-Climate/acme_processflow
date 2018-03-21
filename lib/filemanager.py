import os
import re
import sys
import threading
import logging
import random

from time import sleep
from peewee import *
from globus_cli.commands.ls import _get_ls_res as get_ls

from models import DataFile
from jobs.Transfer import Transfer
from jobs.JobStatus import JobStatus
from lib.YearSet import SetStatus
from lib.util import (print_debug,
                      print_line,
                      transfer_directory)

filestatus = {
    'EXISTS': 0,
    'NOT_EXIST': 1,
    'IN_TRANSIT': 2
}

file_type_map = {
    'atm': 'EXPERIMENT.cam.h0.YEAR-MONTH.nc',
    'ice': 'mpascice.hist.am.timeSeriesStatsMonthly.YEAR-MONTH-01.nc',
    'ocn': 'mpaso.hist.am.timeSeriesStatsMonthly.YEAR-MONTH-01.nc',
    'rest': 'mpaso.rst.YEAR-01-01_00000.nc',
    'mpascice.rst': 'mpascice.rst.YEAR-01-01_00000.nc',
    'streams.ocean': 'streams.ocean',
    'streams.cice': 'streams.cice',
    'mpas-cice_in': 'mpas-cice_in',
    'mpas-o_in': 'mpas-o_in',
    'meridionalHeatTransport': 'mpaso.hist.am.meridionalHeatTransport.YEAR-MONTH-01.nc',
}


class FileManager(object):
    """
    Manage all files required by jobs
    """

    def __init__(self, database, types, sta=False, ui=False, **kwargs):
        """
        Parameters:
            mutex (theading.Lock) the mutext for accessing the database
            sta (bool) is this run short term archived or not (1) yes (0) no
            types (list(str)): A list of strings of datatypes
            database (str): the path to where to create the sqlite database file
            remote_endpoint (str): the Globus UUID for the remote endpoint
            remote_path (str): the base directory to search for this runs model output
            local_endpoint (str): The Globus UUID for the local endpoint
            local_path (str): the local project path
        """
        self.mutex = kwargs['mutex']
        self.event_list = kwargs['event_list']
        self.ui = ui
        self.sta = sta
        self.updated_rest = False
        self.types = types if isinstance(types, list) else [types]
        self.active_transfers = 0
        self.db_path = database
        if os.path.exists(database):
            os.remove(database)
        self.mutex.acquire()
        DataFile._meta.database.init(database)
        if DataFile.table_exists():
            DataFile.drop_table()
        DataFile.create_table()
        if self.mutex.locked():
            self.mutex.release()
        self.remote_endpoint = kwargs.get('remote_endpoint')
        self.local_path = kwargs.get('local_path')
        self.local_endpoint = kwargs.get('local_endpoint')
        self.move_everything = kwargs.get('move_everything', False)
        self.start_year = 0

        head, tail = os.path.split(kwargs.get('remote_path'))
        if not self.sta:
            if tail != 'run':
                self.remote_path = os.path.join(
                    kwargs.get('remote_path'), 'run')
            else:
                self.remote_path = kwargs.get('remote_path')
        else:
            if tail == 'run':
                self.remote_path = head
            else:
                self.remote_path = kwargs.get('remote_path')

    def __str__(self):
        return str({
            'short term archive': self.sta,
            'active_transfers': self.active_transfers,
            'remote_path': self.remote_path,
            'remote_endpoint': self.remote_endpoint,
            'local_path': self.local_path,
            'local_endpoint': self.local_endpoint,
            'db_path': self.db_path
        })
    
    def discovery(self, client, path, depth=0, maxdepth=4, ignore=None):
        """ 
        Recurse down remote directory until the whole structure is mapped
        
        Parameters:
            client (globus-sdk.TransferClient): an authorized globus client
            path (str): the remote path to map
            depth (int): the current recursive depth
            maxdepth (int): how far down the rabbit hole we should go
            ignore (list): a list of items to ignore
        Returns:
            A nested dictonary matching the structure of the remote directory
        """
        data = {}
        if depth >= maxdepth:
            return data
        res = self._get_ls(
                client=client,
                path=self.remote_path)
        for item in res:
            if ignore is not None:
                if item['name'] in ignore:
                    continue
            if item['type'] = 'dir':
                data[item['name']] = discovery(
                    self,
                    client=client,
                    path=os.path.join(path, item['name']),
                    depth=depth + 1,
                    maxdepth=maxdepth)
            else:
                data[item['name']] = None
        return data
    
    def move_everything(self, client, experiment):
        """
        A blocking call to move everything before starting the run
        
        Parameters:
            client (globus-sdk.TranferClient): an authorized globus transfer client
            experiment (str): the name of the experiment
        """
        archive_path = os.path.join(self.local_path, 'archive')
        if not os.oath.exists(archive_path):
            os.makedirs(archive_path)
        ignore_list = ['build', 'post', 'test01', 'zstash']
        transfer_list = list()
        res = self._get_ls(
                client=client,
                path=self.remote_path)
        
        # Move all the data, one directory at a time
        for item in res:
            if item['type'] == 'dir' and item['name'] not in ignore_list:
                msg = 'Starting directory transfer for {}'.format(item['name'])
                print_line(
                    ui=self.ui,
                    line=msg,
                    event_list=self.event_list)
                local_path = os.path.join(archive_path, item['name'])
                remote_path = os.path.join(self.remote_path, item['name'])
                transfer_directory(
                    source_endpoint=self.remote_endpoint,
                    destination_endpoint=self.local_endpoint,
                    src_path=remote_path,
                    dst_path=local_path,
                    client=client)
        
        # Link the data into the input directory where the rest of the filemanager is expecting it
        # First handle the atm files
        atm_path = os.path.join('archive', 'archive', 'atm', 'hist')
        atm_pattern = file_type_map['atm'].replace('EXPERIMENT', experiment)
        atm_pattern = atm_pattern.replace('YEAR', '[0-9]{4}')
        atm_pattern = atm_pattern.replace('MONTH', '[0-9]{2}')
        atm_pattern = atm_pattern.replace('.', '\.')
        atm_data = [x for x in os.listdir(atm_path) if re.match(string=x, pattern=atm_pattern)]
        for item in atm_data:
            os.symlink(
                src=os.path.join(atm_path, item),
                dst=os.path.join(os.getcwd(), 'input', 'atm', item))


    def populate_handle_rest(self, simstart, newfiles):
        """
        Add the restart files to the newfiles list to be added to the db
        """

        # First add the mpaso.rst
        name = file_type_map['rest'].replace(
            'YEAR', '{:04d}'.format(simstart + 1))
        local_path = os.path.join(
            self.local_path,
            'rest',
            name)
        head, tail = os.path.split(local_path)
        if not os.path.exists(head):
            os.makedirs(head)

        if self.sta:
            remote_path = os.path.join(
                self.remote_path,
                'archive',
                'rest',
                '{year:04d}-01-01-00000'.format(year=simstart + 1),
                name)
        else:
            remote_path = os.path.join(self.remote_path, name)
        newfiles = self._add_file(
            newfiles=newfiles,
            name=name,
            local_path=local_path,
            remote_path=remote_path,
            _type='rest')

        # Second add the mpascice.rst
        name = file_type_map['mpascice.rst'].replace(
            'YEAR', '{:04d}'.format(simstart + 1))
        local_path = os.path.join(
            self.local_path,
            'rest',
            name)

        if self.sta:
            remote_path = os.path.join(
                self.remote_path,
                'archive',
                'rest',
                '{year:04d}-01-01-00000'.format(year=simstart + 1),
                name)
        else:
            remote_path = os.path.join(self.remote_path, name)
        newfiles = self._add_file(
            newfiles=newfiles,
            name=name,
            local_path=local_path,
            remote_path=remote_path,
            _type='mpascice.rst')

    def populate_handle_mpas(self, _type, newfiles):
        local_path = os.path.join(
            self.local_path,
            'mpas',
            _type)
        head, tail = os.path.split(local_path)
        if not os.path.exists(head):
            os.makedirs(head)
        if self.sta:
            remote_path = os.path.join(self.remote_path, 'run', _type)
        else:
            remote_path = os.path.join(self.remote_path, _type)
        newfiles = self._add_file(
            newfiles=newfiles,
            name=_type,
            local_path=local_path,
            remote_path=remote_path,
            _type=_type)

    def populate_heat_transport(self, newfiles):
        name = 'mpaso.hist.am.meridionalHeatTransport.{year:04d}-02-01.nc'.format(
            year=self.start_year)
        local_path = os.path.join(
            self.local_path,
            'mpas',
            name)
        head, tail = os.path.split(local_path)
        if not os.path.exists(head):
            os.makedirs(head)
        if self.sta:
            remote_path = os.path.join(
                self.remote_path,
                'archive',
                'ocn',
                'hist',
                name)
        else:
            remote_path = os.path.join(
                self.remote_path,
                name)
        newfiles = self._add_file(
            newfiles=newfiles,
            name=name,
            local_path=local_path,
            remote_path=remote_path,
            _type='meridionalHeatTransport')

    def populate_monthly(self, _type, newfiles, simstart, simend, experiment):
        local_base = os.path.join(
            self.local_path, _type)
        if not os.path.exists(local_base):
            os.makedirs(local_base)

        for year in xrange(simstart, simend + 1):
            for month in xrange(1, 13):
                if _type == 'atm':
                    name = file_type_map[_type].replace(
                        'EXPERIMENT', experiment)
                else:
                    name = file_type_map[_type]
                yearstr = '{0:04d}'.format(year)
                monthstr = '{0:02d}'.format(month)
                name = name.replace('YEAR', yearstr)
                name = name.replace('MONTH', monthstr)
                local_path = os.path.join(
                    local_base, name)
                if self.sta:
                    remote_path = os.path.join(
                        self.remote_path,
                        'archive',
                        _type,
                        'hist',
                        name)
                else:
                    remote_path = os.path.join(
                        self.remote_path,
                        name)
                newfiles = self._add_file(
                    newfiles=newfiles,
                    name=name,
                    local_path=local_path,
                    remote_path=remote_path,
                    _type=_type,
                    year=year,
                    month=month)

    def populate_file_list(self, simstart, simend, experiment):
        """
        Populate the database with the required DataFile entries

        Parameters:
            simstart (int): the start year of the simulation,
            simend (int): the end year of the simulation,
            experiment (str): the name of the experiment
                ex: 20170915.beta2.A_WCYCL1850S.ne30_oECv3_ICG.edison
        """
        msg = 'Creating file table'
        print_line(
            ui=False,
            line=msg,
            event_list=self.event_list)
        if self.sta:
            msg = 'Using short term archive'
        else:
            msg = 'Short term archive turned off'
        print_line(
            ui=self.ui,
            line=msg,
            event_list=self.event_list)
        if not self.start_year:
            self.start_year = simstart
        newfiles = []
        with DataFile._meta.database.atomic():
            for _type in self.types:
                if _type not in file_type_map:
                    continue
                if _type == 'rest':
                    self.populate_handle_rest(simstart, newfiles)
                elif _type in ['streams.ocean', 'streams.cice', 'mpas-o_in', 'mpas-cice_in']:
                    self.populate_handle_mpas(_type, newfiles)
                elif _type == 'meridionalHeatTransport':
                    self.populate_heat_transport(newfiles)
                else:
                    self.populate_monthly(
                        _type, newfiles, simstart, simend, experiment)
            msg = 'Inserting file data into the table'
            print_line(
                ui=self.ui,
                line=msg,
                event_list=self.event_list)
            self.mutex.acquire()
            try:
                step = 50
                for idx in range(0, len(newfiles), step):
                    DataFile.insert_many(newfiles[idx: idx + step]).execute()
            except Exception as e:
                print_debug(e)
            finally:
                if self.mutex.locked():
                    self.mutex.release()
            msg = 'Database update complete'
            print_line(
                ui=self.ui,
                line=msg,
                event_list=self.event_list)

    def _add_file(self, newfiles, **kwargs):
        local_status = filestatus['EXISTS'] \
            if os.path.exists(kwargs['local_path']) \
            else filestatus['NOT_EXIST']
        local_size = os.path.getsize(kwargs['local_path']) \
            if local_status == filestatus['EXISTS'] \
            else 0
        newfiles.append({
            'name': kwargs['name'],
            'local_path': kwargs['local_path'],
            'local_status': local_status,
            'remote_path': kwargs['remote_path'],
            'remote_status': filestatus['NOT_EXIST'],
            'year': kwargs.get('year', 0),
            'month': kwargs.get('month', 0),
            'datatype': kwargs['_type'],
            'local_size': local_size,
            'remote_size': 0
        })
        return newfiles

    def print_db(self):
        self.mutex.acquire()
        for df in DataFile.select():
            print {
                'name': df.name,
                'local_path': df.local_path,
                'remote_path': df.remote_path
            }
    
    def _get_names(self, res, _type):
        names = list()
        names_res = [x['name'] for x in res]
        names_not_found = list()
        names_tmp = [x.name for x in DataFile.select().where(
                     DataFile.datatype == _type)]
        for name in names_tmp:
            if name in names_res:
                names.append(name)
            else:
                names_not_found.append(name)
        if names_not_found:
            msg = 'WARNING: {} remote files not found'.format(len(names_not_found))
            print_line(
                ui=self.ui,
                line=msg,
                event_list=self.event_list,
                current_state=True)
        return names            

    def update_remote_status(self, client):
        """
        Check remote location for existance of the files on our list
        If they exist, update their status in the DB

        Parameters:
            client (globus_sdk.client): the globus client to use for remote query
        """
        result = client.endpoint_autoactivate(
            self.remote_endpoint, if_expires_in=2880)
        if result['code'] == "AutoActivationFailed":
            return False

        # First handle the short term archive case
        if self.sta:
            for _type in self.types:
                # if the type is restart, handle the special cases
                if _type == 'rest':
                    if not self.updated_rest:
                        self.mutex.acquire()
                        name, path, size = self.update_remote_rest_sta_path(
                            client)
                        try:
                            DataFile.update(
                                remote_status=filestatus['EXISTS'],
                                remote_size=size,
                                remote_path=path,
                                name=name
                            ).where(
                                DataFile.datatype == 'rest'
                            ).execute()
                        except OperationalError as operror:
                            line = 'Error writing to database, database is locked by another process'
                            print_line(
                                ui=self.ui,
                                line=line,
                                event_list=self.event_list)
                            logging.error(line)

                        name, path, size = self.update_remote_rest_sta_path(
                            client, pattern='mpascice.rst')
                        try:
                            DataFile.update(
                                remote_status=filestatus['EXISTS'],
                                remote_size=size,
                                remote_path=path,
                                name=name
                            ).where(
                                DataFile.datatype == 'mpascice.rst'
                            ).execute()
                        except OperationalError as operror:
                            line = 'Error writing to database, database is locked by another process'
                            print_line(
                                ui=self.ui,
                                line=line,
                                event_list=self.event_list)
                            logging.error(line)

                        if self.mutex.locked():
                            self.mutex.release()
                        self.updated_rest = True
                    continue
                elif _type in ['streams.ocean', 'streams.cice', 'mpas-o_in', 'mpas-cice_in']:
                    remote_path = os.path.join(self.remote_path, 'run')
                elif _type == 'meridionalHeatTransport':
                    remote_path = os.path.join(
                        self.remote_path, 'archive', 'ocn', 'hist')
                else:
                    remote_path = os.path.join(
                        self.remote_path, 'archive', _type, 'hist')

                if _type not in ['rest', 'mpascice.rst']:
                    msg = 'Querying globus for {}'.format(_type)
                    print_line(
                        ui=self.ui,
                        line=msg,
                        event_list=self.event_list,
                        current_state=True)
                    res = self._get_ls(
                        client=client,
                        path=remote_path)

                    self.mutex.acquire()
                    try:
                        names = self._get_names(res, _type)
                        step = 100
                        for idx in range(0, len(names), step):
                            batch_names = names[idx: idx + step]
                            to_update_name = [x['name']
                                              for x in res if x['name'] in batch_names]
                            to_update_size = [x['size']
                                              for x in res if x['name'] in batch_names]
                            q = DataFile.update(
                                remote_status=filestatus['EXISTS'],
                                remote_size=to_update_size[to_update_name.index(
                                    DataFile.name)]
                            ).where(
                                (DataFile.name << to_update_name) &
                                (DataFile.datatype == _type))
                            n = q.execute()
                    except Exception as e:
                        print_debug(e)
                        print "Do you have the correct start and end dates and experiment name?"
                    except OperationalError as operror:
                        line = 'Error writing to database, database is locked by another process'
                        print_line(
                            ui=self.ui,
                            line=line,
                            event_list=self.event_list)
                        logging.error(line)
                    finally:
                        if self.mutex.locked():
                            self.mutex.release()
        else:
            remote_path = self.remote_path
            res = self._get_ls(
                client=client,
                path=remote_path)
            self.mutex.acquire()
            try:
                for _type in self.types:
                    names = self._get_names(res, _type)
                    step = 100
                    for idx in range(0, len(names), step):
                        batch_names = names[idx: idx + step]
                        to_update_name = [x['name']
                                          for x in res if x['name'] in batch_names]
                        to_update_size = [x['size']
                                          for x in res if x['name'] in batch_names]
                        q = DataFile.update(
                            remote_status=filestatus['EXISTS'],
                            remote_size=to_update_size[to_update_name.index(
                                DataFile.name)]
                        ).where(
                            (DataFile.name << to_update_name) &
                            (DataFile.datatype == _type))
                        n = q.execute()
            except Exception as e:
                print_debug(e)
            except OperationalError as operror:
                line = 'Error writing to database, database is locked by another process'
                print_line(
                    ui=self.ui,
                    line=line,
                    event_list=self.event_list)
                logging.error(line)
            finally:
                if self.mutex.locked():
                    self.mutex.release()

    def _get_ls(self, client, path):
        for fail_count in xrange(10):
            try:
                res = get_ls(
                    client,
                    path,
                    self.remote_endpoint,
                    False, 0, False)
            except Exception as e:
                sleep(fail_count)
                if fail_count >= 9:
                    print_debug(e)
                    sys.exit()
            else:
                return res

    def update_remote_rest_sta_path(self, client, pattern='mpaso.rst'):
        if not self.sta:
            return
        path = os.path.join(
            self.remote_path,
            'archive',
            'rest')
        res = self._get_ls(
            client=client,
            path=path)
        contents = res['DATA']
        subdir = contents[1]['name']
        path = os.path.join(path, subdir)
        contents = self._get_ls(
            client=client,
            path=path)
        remote_name = ''
        remote_path = ''
        size = 0
        for remote_file in contents:
            if re.search(pattern=pattern, string=remote_file['name']):
                remote_name = remote_file['name']
                remote_path = os.path.join(
                    self.remote_path,
                    'archive',
                    'rest',
                    subdir,
                    remote_file['name'])
                size = remote_file['size']
                break
        return remote_name, remote_path, size

    def update_local_status(self):
        """
        Update the database with the local status of the expected files

        Parameters:
            types (list(str)): the list of files types to expect, must be members of file_type_map
        """

        self.mutex.acquire()
        try:
            query = (DataFile
                        .select()
                        .where(
                            (DataFile.local_status == filestatus['NOT_EXIST']) |
                            (DataFile.local_status == filestatus['IN_TRANSIT'])))
            for datafile in query.execute():
                should_save = False
                if os.path.exists(datafile.local_path):
                    local_size = os.path.getsize(datafile.local_path)
                    if local_size == datafile.remote_size:
                        datafile.local_status = filestatus['EXISTS']
                        datafile.local_size = local_size
                        datafile.save()
        except OperationalError as operror:
            line = 'Error writing to database, database is locked by another process'
            print_line(
                ui=self.ui,
                line=line,
                event_list=self.event_list)
            logging.error(line)
        finally:
            if self.mutex.locked():
                self.mutex.release()

    def all_data_local(self):
        self.mutex.acquire()
        try:
            query = (DataFile
                        .select()
                        .where(
                            DataFile.local_status == filestatus['NOT_EXIST']))
            missing_data = query.execute()
            # if any of the data is missing, not all data is local
            if missing_data is None or len(missing_data) != 0:
                return False
        except Exception as e:
            print_debug(e)
        finally:
            if self.mutex.locked():
                self.mutex.release()
        return True

    def all_data_remote(self):
        self.mutex.acquire()
        try:
            for data in DataFile.select():
                if data.remote_status != filestatus['EXISTS']:
                    return False
        except Exception as e:
            print_debug(e)
        finally:
            if self.mutex.locked():
                self.mutex.release()
        return True

    def transfer_needed(self, event_list, event, remote_endpoint, ui, display_event, emailaddr, thread_list):
        """
        Start a transfer job for any files that arent local, but do exist remotely

        Globus user must already be logged in

        Parameters:
            event_list (EventList): the list to push information into
            event (threadding.event): the thread event to trigger a cancel
        """
        if self.active_transfers >= 2:
            msg = 'Currently have {} transfers active, not starting any new ones'.format(self.active_transfers)
            logging.info(msg)
            return False
        # required files dont exist locally, do exist remotely
        # or if they do exist locally have a different local and remote size
        self.mutex.acquire()
        try:
            required_files = [x for x in DataFile.select().where(
                (DataFile.remote_status == filestatus['EXISTS']) &
                (DataFile.local_status != filestatus['IN_TRANSIT']) &
                ((DataFile.local_status == filestatus['NOT_EXIST']) |
                 (DataFile.local_size != DataFile.remote_size))
            ).execute()]
            if len(required_files) == 0:
                msg = 'No new files needed'
                logging.info(msg)
                return False
            target_files = []
            transfer_names = []
            target_size = 1e11  # 100 GB
            total_size = 0
            for file in required_files:
                if total_size + file.remote_size < target_size:
                    target_files.append({
                        'name': file.name,
                        'local_size': file.local_size,
                        'local_path': file.local_path,
                        'local_status': file.local_status,
                        'remote_size': file.remote_size,
                        'remote_path': file.remote_path,
                        'remote_status': file.remote_status
                    })
                    transfer_names.append(file.name)
                    total_size += file.remote_size
                else:
                    break
        except Exception as e:
            print_debug(e)
            return False
        finally:
            if self.mutex.locked():
                self.mutex.release()

        logging.info('Transfering required files')
        msg = 'total transfer size {size} gigabytes for {nfiles} files'.format(
            size=(total_size / 1e9),
            nfiles=len(target_files))
        print_line(
            ui=self.ui,
            line=msg,
            event_list=self.event_list)
        transfer_config = {
            'file_list': target_files,
            'source_endpoint': self.remote_endpoint,
            'destination_endpoint': self.local_endpoint,
            'source_path': self.remote_path,
            'destination_path': self.local_path,
            'source_email': emailaddr,
            'display_event': display_event,
            'ui': ui,
        }
        transfer = Transfer(
            config=transfer_config,
            event_list=event_list)
        self.mutex.acquire()
        try:
            DataFile.update(
                local_status=filestatus['IN_TRANSIT']
            ).where(
                DataFile.name << transfer_names
            ).execute()
        except Exception as e:
            print_debug(e)
            return False
        except OperationalError as operror:
            line = 'Error writing to database, database is locked by another process'
            print_line(
                ui=self.ui,
                line=line,
                event_list=self.event_list)
            logging.error(line)
            return False
        finally:
            if self.mutex.locked():
                self.mutex.release()

        msg = 'Starting file transfer'
        print_line(
            ui=self.ui,
            line=msg,
            event_list=self.event_list)
        args = (transfer, event, event_list)
        thread = threading.Thread(
            target=self._handle_transfer,
            name='filemanager_transfer',
            args=args)
        thread_list.append(thread)
        thread.start()
        return True

    def _handle_transfer(self, transfer, event, event_list):
        # this is to stop the simultanious print issue
        sleep(random.uniform(0.01, 0.1))
        
        self.active_transfers += 1
        transfer.execute(event)
        self.active_transfers -= 1

        if transfer.status == JobStatus.FAILED:
            msg = "Transfer has failed"
            print_line(
                ui=self.ui,
                line=msg,
                event_list=self.event_list)
            logging.error(msg)
            return
        else:
            self.transfer_cleanup(transfer)

    def transfer_cleanup(self, transfer):
        try:
            self.mutex.acquire()
            names = [x['name'] for x in transfer.file_list]
            query = (DataFile
                        .select()
                        .where(DataFile.name << names))
            for datafile in query.execute():
                if os.path.exists(datafile.local_path) \
                        and os.path.getsize(datafile.local_path) == datafile.remote_size:
                    datafile.local_status = filestatus['EXISTS']
                    datafile.local_size = os.path.getsize(datafile.local_path)
                else:
                    msg = 'file transfer error on {}'.format(datafile.name)
                    print_line(
                        ui=self.ui,
                        line=msg,
                        event_list=self.event_list)
                    datafile.local_status = filestatus['NOT_EXIST']
                    datafile.local_size = 0
                datafile.save()
            total_files = DataFile.select().count()
            local_files = DataFile.select().where(
                DataFile.local_status == filestatus['EXISTS']
            ).count()
            msg = 'Transfer complete: {local}/{total} files local'.format(
                local=local_files,
                total=total_files)
            print_line(
                ui=self.ui,
                line=msg,
                event_list=self.event_list)
        except OperationalError as operror:
            line = 'Error writing to database, database is locked by another process'
            print_line(
                ui=self.ui,
                line=line,
                event_list=self.event_list)
            logging.error(line)
        if self.mutex.locked():
            self.mutex.release()


    def years_ready(self, start_year, end_year):
        """
        Checks if atm files exist from start year to end of endyear

        Parameters:
            start_year (int): the first year to start checking
            end_year (int): the last year to check for
        Returns:
            -1 if no data present
            0 if partial data present
            1 if all data present
        """
        data_ready = True
        non_zero_data = False

        self.mutex.acquire()
        try:
            query = (DataFile
                        .select()
                        .where(
                            (DataFile.datatype == 'atm') &
                            (DataFile.year >= start_year) &
                            (DataFile.year <= end_year)))
            for datafile in query.execute():
                if datafile.local_status != filestatus['EXISTS']:
                    data_ready = False
                else:
                    non_zero_data = True
        except Exception as e:
            print_debug(e)
        finally:
            if self.mutex.locked():
                self.mutex.release()

        if data_ready:
            return 1
        elif not data_ready and non_zero_data:
            return 0
        elif not data_ready and not non_zero_data:
            return -1

    def get_file_paths_by_year(self, start_year, end_year, _type):
        monthly = ['atm', 'ocn', 'ice']
        self.mutex.acquire()
        try:
            if _type not in monthly:
                query = (DataFile
                            .select()
                            .where(
                                (DataFile.datatype == _type) &
                                (DataFile.local_status == filestatus['EXISTS'])))
            else:
                query = (DataFile
                            .select()
                            .where(
                                (DataFile.datatype == _type) &
                                (DataFile.year >= start_year) &
                                (DataFile.year <= end_year) &
                                (DataFile.local_status == filestatus['EXISTS'])))
            datafiles = query.execute()
            if datafiles is None or len(datafiles) == 0:
                files = []
            else:
                files = [x.local_path for x in datafiles]
        except Exception as e:
            print_debug(e)
            files = []
        finally:
            if self.mutex.locked():
                self.mutex.release()
        return files

    def check_year_sets(self, job_sets):
        """
        Checks the file_list, and sets the year_set status to ready if all the files are in place,
        otherwise, checks if there is partial data, or zero data
        """
        incomplete_job_sets = [s for s in job_sets
                               if s.status != SetStatus.COMPLETED
                               and s.status != SetStatus.RUNNING
                               and s.status != SetStatus.FAILED]

        for job_set in incomplete_job_sets:
            data_ready = self.years_ready(
                start_year=job_set.set_start_year,
                end_year=job_set.set_end_year)

            if data_ready == 1:
                if job_set.status != SetStatus.DATA_READY:
                    job_set.status = SetStatus.DATA_READY
                    msg = "{start:04d}-{end:04d} is ready".format(
                        start=job_set.set_start_year,
                        end=job_set.set_end_year)
                    print_line(
                        ui=self.ui,
                        line=msg,
                        event_list=self.event_list)
            elif data_ready == 0:
                if job_set.status != SetStatus.PARTIAL_DATA:
                    job_set.status = SetStatus.PARTIAL_DATA
                    msg = "{start:04d}-{end:04d} has partial data".format(
                        start=job_set.set_start_year,
                        end=job_set.set_end_year)
                    print_line(
                        ui=self.ui,
                        line=msg,
                        event_list=self.event_list)
            elif data_ready == -1:
                if job_set.status != SetStatus.NO_DATA:
                    job_set.status = SetStatus.NO_DATA
                    msg = "{start:04d}-{end:04d} has no data".format(
                        start=job_set.set_start_year,
                        end=job_set.set_end_year)
                    print_line(
                        ui=self.ui,
                        line=msg,
                        event_list=self.event_list)
