import json
import logging
import os
import sys

from getpass import getpass
import paramiko

from processflow.lib.util import print_debug


def get_ls(client, remote_path):
    """
    Return a list of the contents of the remote_path from the 
    host that the client is connected to
    """
    try:
        cmd = 'ls {}'.format(remote_path)
        _, stdout, _ = client.exec_command(cmd)
    except Exception as e:
        print_debug(e)
        return None
    return stdout.read().split('\n')


def get_ll(client, remote_path):
    try:
        cmd = 'ls -la {}'.format(remote_path)
        _, stdout, _ = client.exec_command(cmd)
    except Exception as e:
        print_debug(e)
        return None
    out = stdout.read().split('\n')
    ll = []
    for item in out:
        file_info = filter(lambda x: x != '', item.split(' '))
        if len(file_info) < 9:
            continue
        if file_info[0] == 'total':
            continue
        if file_info[-1] in ['.', '..']:
            continue
        ll.append({
            'permissions': file_info[0],
            'num_links': file_info[1],
            'owner': file_info[2],
            'group': file_info[3],
            'size': file_info[4],
            'creation': ' '.join(file_info[5: 7]),
            'name': ' '.join(file_info[8:])
        })
    return ll


def transfer(sftp_client, file):
    """
    Use a paramiko ssh client to transfer the files in 
    file_list one at a time

    Parameters:
        sftp_client (paramiko.SFTPClient): the client to use for transport
        file (dict): a dict with keys remote_path, and local_path
    """

    _, f_name = os.path.split(file['remote_path'])
    try:
        sftp_client.get(file['remote_path'], file['local_path'])
    except Exception as e:
        print_debug(e)
        msg = '{} transfer failed'.format(f_name)
        logging.error(msg)
        return False

    if os.path.getsize(file['local_path']) == 0:
        msg = '{} transfer failed to copy the file correctly'.format(f_name)
        logging.error(msg)
        os.remove(file['local_path'])
        return False
    else:
        msg = '{} transfer successful'.format(f_name)
        logging.info(msg)
        return True


def get_ssh_client(hostname, credential_path=False):
    """
    Get user credentials and use them to log in to the remote host

    Parameters:
        hostname (str): the hostname of the remote host
        credential_path (str): the optional path to a json file containing user credentials
    Returns:
        Paramiko.Transport client if login successful,
        None otherwise
    """
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.WarningPolicy)
    connected = False

    if credential_path:
        with open(credential_path, 'r') as infile:
            creds = json.load(infile)
        username = creds.get('username')
        password = creds.get('password')
        one_time = creds.get('one_time_code')
        if one_time:
            password = '{}{}'.format(password, one_time)
        try:
            client.connect(hostname, port=22,
                           username=username, password=password)
        except Exception as error:
            print_debug(error)
            connected = False
        else:
            connected = True
    else:
        username = raw_input('Username for {}: '.format(hostname))
        for _ in range(3):
            try:
                password = getpass(prompt='Password for {}: '.format(hostname))
                client.connect(hostname, port=22,
                               username=username, password=password)
            except Exception as error:
                print 'Invalid password'
            else:
                connected = True
                break
    if not connected:
        print('Unable to open ssh connection for {}'.format(hostname))
        sys.exit(1)
    return client
