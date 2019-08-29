import os
import shlex
import subprocess
import time


SUCCESS = 0
FAILURE = 1

def run_cmd(cmd, join_stderr=True, shell_cmd=False, verbose=True):

    print("CMD: {c}".format(c=cmd))
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)

    if join_stderr:
        stderr = subprocess.STDOUT
    else:
        stderr = subprocess.PIPE

    P = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=stderr,
        bufsize=0, cwd=os.getcwd(), shell=shell_cmd)
    out = []
    while P.poll() is None:
        read = P.stdout.readline().rstrip()
        out.append(read)
        if verbose == True:
            print(read)

    ret_code = P.returncode
    return(ret_code)


def git_clone_repo(workdir, repo_name):
    """ git clone https://github.com/UV-CDAT/<repo_name> and place it in
        <workdir>/<repo_name> directory                                              
    """
    if repo_name == 'pcmdi_metrics':
        url = 'https://github.com/pcmdi/' + repo_name
    else:
        url = 'https://github.com/UV-CDAT/' + repo_name

    repo_dir = os.path.join(workdir, repo_name)
    cmd = "git clone {url} {dest}".format(url=url, dest=repo_dir)
    ret_code = run_cmd(cmd)
    if ret_code != SUCCESS:
        print("FAIL...{c}".format(c=cmd))
        return ret_code

    return(ret_code)


def run_in_conda_env(conda_path, env, cmds_list):

    add_path_cmd = "export PATH={path}:$PATH".format(path=conda_path)
    activate_cmd = "source activate {env}".format(env=env)
    cmds = None
    for a_cmd in cmds_list:
        if cmds is None:
            cmds = a_cmd
        else:
            cmds = "{existing}; {new_cmd}".format(existing=cmds, new_cmd=a_cmd)

    print("xxx cmds: " + cmds)
    deactivate_cmd = 'source deactivate'

    cmd = "bash -c \"{add_path}; {act}; {cmds}; {deact}\"".format(add_path=add_path_cmd,
                                                                  act=activate_cmd,
                                                                  cmds=cmds,
                                                                  deact=deactivate_cmd)
    print("CMD: {c}".format(c=cmd))
    ret_code = os.system(cmd)
    print(ret_code)
    return(ret_code)


def run_in_conda_env_capture_output(conda_path, env, cmds_list):

    current_time = time.localtime(time.time())
    time_str = time.strftime("%b.%d.%Y.%H:%M:%S", current_time)
    tmp_file = "/tmp/processFlow.{curr_time}".format(curr_time=time_str)

    add_path_cmd = "export PATH={path}:$PATH".format(path=conda_path)
    activate_cmd = "source activate {env}".format(env=env)
    cmds = None
    for a_cmd in cmds_list:
        if cmds == None:
            cmds = a_cmd
        else:
            cmds = "{existing}; {new_cmd}".format(existing=cmds, new_cmd=a_cmd)

    deactivate_cmd = 'source deactivate'

    cmd = "bash -c \"{add_path}; {act}; {cmds}; {deact}\"".format(
        add_path=add_path_cmd,
        act=activate_cmd,
        cmds=cmds,
        deact=deactivate_cmd)

    cmd = "{the_cmd} > {output_file}".format(
        the_cmd=cmd,
        output_file=tmp_file)

    ret_code = os.system(cmd)
    print(ret_code)
    if ret_code != SUCCESS:
        return(FAILURE, None)

    with open(tmp_file) as f:
        output = f.readlines()
    #os.remove(tmp_file)
    return(ret_code, output)
