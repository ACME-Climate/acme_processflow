import logging

from time import sleep

from globus_cli.commands.login import check_logged_in
from globus_cli.commands.ls import _get_ls_res as globus_ls
from globus_cli.services.transfer import get_client
from globus_sdk import TransferData

from processflow.lib.util import print_debug, print_line, print_message
from processflow.lib.util import format_debug


def get_ls(client, path, endpoint):
    for fail_count in range(10):
        try:
            res = globus_ls(
                client,
                path,
                endpoint,
                False, 0, False)
        except Exception as e:
            sleep(fail_count)
            print_message("Globus server error, retrying")
            print_debug(e)
        else:
            return res


def transfer(client, remote_uuid, local_uuid, file_list, event=None):
    """
    Setup a file transfer between two endpoints

    Parameters:
        remote_uuid (str): the globus uuid of the source endpoint
        local_uuid (str): the globus uuid of the destination endpoint
        file_list (list): a list of dictionaries with keys remote_path, local_path
        event (Threadding.Event): a kill event for running inside a thread
    """

    # create the transfer object
    try:
        task_label = 'Processflow auto transfer'
        transfer_task = TransferData(
            client,
            remote_uuid,
            local_uuid,
            sync_level='checksum',
            label=task_label)
    except Exception as e:
        logging.error('Error creating transfer task')
        logging.error(format_debug(e))
        return

    # add in our transfer items
    for datafile in file_list:
        transfer_task.add_item(
            source_path=datafile['remote_path'],
            destination_path=datafile['local_path'],
            recursive=False)

    # Start the transfer
    task_id = None
    result = None
    try:
        result = client.submit_transfer(transfer_task)
        task_id = result["task_id"]
        logging.info('starting transfer with task id %s', task_id)
    except Exception as e:
        if result:
            logging.error("result: %s", str(result))
        logging.error("Could not submit the transfer")
        logging.error(format_debug(e))
        return

    # loop until transfer is complete
    while True:
        status = client.get_task(task_id)
        if status['status'] == 'SUCCEEDED':
            return True, None
        elif status['status'] == 'FAILED':
            return False, status.get('nice_status_details')
        if event and event.is_set():
            client.cancel_task(task_id)
            return None, None
        sleep(10)


def transfer_directory(src_uuid, dst_uuid, src_path, dst_path, event_list=None, killevent=None):
    """
    Transfer all the contents from source_endpoint:src_path to destination_endpoint:dst_path

    parameters:
        src_uuid (str): the globus UUID for the source files
        dst_uuid (str) the globus UUID for the destination
        src_path (str) the path to the source directory to copy
        dst_path (str) the path on the destination directory
        event_list (EventList): an eventlist to push user notifications into
        killevent (Threadding.Event): an event to listen for if running inside a thread to terminate
    """

    client = get_client()
    transfer = TransferData(
        client,
        src_uuid,
        dst_uuid,
        sync_level='checksum')
    transfer.add_item(
        source_path=src_path,
        destination_path=dst_path,
        recursive=True)

    try:
        msg = 'Starting globus directory transfer from {src} to {dst}'.format(
            src=src_path, dst=dst_path)
        print_line(msg, event_list)
        logging.info(msg)

        result = client.submit_transfer(transfer)
        task_id = result['task_id']
    except:
        msg = 'Transfer setup for {src_uuid}:{src_path} tp {dst_uuid}:{dst_path} failed'.format(
            src_uuid=src_uuid, src_path=src_path, dst_uuid=dst_uuid, dst_path=dst_path)
        logging.error(msg)
        return False

    while True:
        status = client.get_task(task_id).get('status')
        if status == 'SUCCEEDED':
            return True
        elif status == 'FAILED':
            return False
        else:
            msg = 'Unexpected globus code: {}'.format(status)
            print_line(msg, event_list)
        if killevent and killevent.is_set():
            client.cancel_task(task_id)
            return False
        sleep(10)


def setup_globus(endpoints, event_list):
    """
    Check globus login status and login as nessisary, then
    iterate over a list of endpoints and activate them all

    Parameters:
        endpoints: list of strings containing globus endpoint UUIDs
        event_list: the event list to push user notifications into
    return:
       True if successful, False otherwise
    """

    # First go through the globus login process
    if not check_logged_in():
        import sys
        message = 'Globus login required. Please run {cmd}\n\n'.format(
            cmd='"globus login"')
        print_message(message)
        print('================================================')
        sys.exit(1)

    if isinstance(endpoints, str):
        endpoints = [endpoints]

    activated = False
    client = get_client()
    while not activated:
        activated = True
        message = ''
        for endpoint in endpoints:
            msg = 'activating endpoint {}'.format(endpoint)
            logging.info(msg)
            try:
                r = client.endpoint_autoactivate(endpoint, if_expires_in=3600)
                logging.info(r['code'])
            except Exception as e:
                print_debug(e)
                if e.code == 'ClientError.NotFound':
                    return False
                else:
                    continue

            if r["code"] == "AutoActivationFailed":
                activated = False
                logging.info('endpoint autoactivation failed')
                server_document = client.endpoint_server_list(endpoint)
                for server in server_document['DATA']:
                    hostname = server["hostname"]
                    break
                message += """
Data transfer server {server} requires manual activation.
Please open the following URL in a browser to activate the endpoint:
https://app.globus.org/file-manager/collections/{endpoint}/

""".format(endpoint=endpoint, server=hostname)

        if not activated:
            print(message)
            input('Press ENTER once endpoints have been activated\n')

    return True


def check_globus(src_uuid, dst_uuid, src_path, dst_path):
    """
    Check that the globus endpoints are not only active but will return information
    about the paths we're interested in.

    Im assuming that the endpoints have already been activated
    """
    try:
        endpoints = [{
            'type': 'source',
            'id': src_uuid,
            'path': src_path
        }, {
            'type': 'destination',
            'id': dst_uuid,
            'path': dst_path
        }]
    except Exception as e:
        print_debug(e)

    client = get_client()
    try:
        for endpoint in endpoints:
            _ = get_ls(
                client,
                endpoint['path'],
                endpoint['id'])
            hostname = client.endpoint_server_list(
                endpoint)['DATA']['hostname']
            print("Access confirmed for {}".format(hostname))
    except Exception as e:
        print_debug(e)
        return False, endpoint
    else:
        return True, None
