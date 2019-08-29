import argparse
import os
import sys

from Util import SUCCESS, FAILURE
from Util import run_cmd, run_in_conda_env, run_in_conda_env_capture_output


parser = argparse.ArgumentParser(description="install processflow",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("-w", "--workdir",
                    help="working directory -- where conda env was installed")
parser.add_argument("-v", "--version",
                    help="version -- 'nightly' or 'latest'")

args = parser.parse_args()
workdir = args.workdir

if not os.path.isdir(workdir):
    print("FAIL: {d} directory where conda should have been installed".format(d=workdir))
    sys.exit(FAILURE)


def check_version(version, conda_path, env):

    if version == 'nightly':
        version_str = 'acme/label/nightly'
    elif version == 'latest':
        version_str = 'acme'
    else:
        version_str = ''
        
    # print out whole version of processflow -- just for logging purpose
    cmds_list = []
    cmd = "conda list processflow | grep '^processflow'"
    cmds_list.append(cmd)
    ret_code = run_in_conda_env(conda_path, env, cmds_list)
    if ret_code != SUCCESS:
        return(ret_code)

    cmds_list = []
    cmd = "conda list processflow | grep '^processflow' | awk -F\\\" \\\" '{ print \$4 }'"
    cmds_list.append(cmd)

    (ret_code, output) = run_in_conda_env_capture_output(conda_path, env, cmds_list)
    if ret_code != SUCCESS:
        return(ret_code)    

    if version_str == output[0].rstrip():
        print("Version matched: {v}".format(v=version))
        ret_code = SUCCESS
    else:
        print("version: {v}, output: {o}, they do not match!!!".format(v=version_str,
                                                                       o=output[0]))
        ret_code = FAILURE
    return(ret_code)
 

def main():
    env_dir = os.path.join(workdir, 'miniconda2', 'envs', 'processflow')
    if os.path.isdir(env_dir) == True:
        print("INFO: {e} already exists".format(e=env_dir))
        print('INFO: please cleanup if you want to recreate the env')
        sys.exit(FAILURE)

    # get env.yml
    env_url = 'https://raw.githubusercontent.com/ACME-Climate/acme_processflow/master/env.yml'
    env_yml = os.path.join(workdir, 'env.yml')
    cmd = "wget {url} -O {env_file}".format(url=env_url, env_file=env_yml)
    ret_code = run_cmd(cmd, True, False, True)
    if ret_code != SUCCESS:
        sys.exit(FAILURE)

    # create processflow env from the env file
    conda_path = os.path.join(workdir, 'miniconda2', 'bin')
    conda_cmd = os.path.join(conda_path, 'conda')
    env = 'processflow'

    cmd = "{conda} create --name {env} --file {yml}".format(conda=conda_cmd,
                                                            env=env,
                                                            yml=env_yml)

    ret_code = run_cmd(cmd, True, False, True)
    if ret_code != SUCCESS:
        sys.exit(FAILURE)

    # update to version -- 'nightly' or 'latest'
    cmds_list = []
    cmd = 'conda config --set always_yes yes'
    cmds_list.append(cmd)
    if args.version == 'nightly':
        cmd = 'conda update -c acme/label/nightly -c acme -c conda-forge -c uvcdat processflow'
    else:
        cmd = 'conda update -c acme -c conda-forge -c uvcdat processflow'
    cmds_list.append(cmd)
    ret_code = run_in_conda_env(conda_path, env, cmds_list)

    # check that we can activate processflow env
    cmd = 'conda list processflow'
    cmds_list = []
    cmds_list.append(cmd)
    ret_code = run_in_conda_env(conda_path, env, cmds_list)

    # check version of processflow
    ret_code = check_version(args.version, conda_path, env)
    sys.exit(ret_code)


if __name__ == '__main__':
    main()
