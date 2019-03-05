import sys
import os
import logging
import paramiko

from getpass import getpass
from lib.util import print_debug

def get_ls(client, remote_path):
    """
    Return a list of the contents of the remote_path from the 
    host that the client is connected to
    """
    try:
        cmd = 'ls {}'.format(remote_path)
        stdin, stdout, stderr = client.exec_command(cmd)
    except Exception as e:
        print_debug(e)
        return None
    return stdout.read().split('\n')

def get_ll(client, remote_path):
    try:
        cmd = 'ls -la {}'.format(remote_path)
        stdin, stdout, stderr = client.exec_command(cmd)
    except Exception as e:
        print_debug(e)
        return None
    out = stdout.read().split('\n')
    ll = []
    for item in out:
        file_info = [x for x in item.split(' ') if x != '']
        if len(file_info) < 9: continue
        if file_info[0] == 'total': continue
        if file_info[-1] in ['.', '..']: continue
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
    else:
        msg = '{} transfer successful'.format(f_name)
        logging.info(msg)
    return True

def get_ssh_client(hostname):    
    """
    Get user credentials and use them to log in to the remote host

    Parameters:
        hostname (str): the hostname of the remote host
    Returns:
        Paramiko.Transport client if login successful,
        None otherwise
    """
    username = input("Username for {}: ".format(hostname))

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.WarningPolicy)
    connected = False
    for _ in range(3):
        try:
            password = getpass(prompt='Password for {}: '.format(hostname))
            client.connect(hostname, port=22, username=username, password=password)
        except Exception as e:
            print('Invalid password')
        else:
            connected = True
            break
    if not connected:
        print('Unable to open ssh connection for {}'.format(hostname))
        sys.exit(1)
    return client
