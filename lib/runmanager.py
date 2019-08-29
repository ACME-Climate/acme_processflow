import os
import logging
import time
from datetime import datetime
from shutil import copytree, move, rmtree, copy2
from subprocess import Popen
from time import sleep

from lib.slurm import Slurm
from lib.pbs import PBS
from lib.util import get_climo_output_files
from lib.util import create_symlink_dir
from lib.util import print_line
from lib.util import render
from lib.util import format_debug

from jobs.job import Job
from jobs.diag import Diag
from jobs.climo import Climo
from jobs.regrid import Regrid
from jobs.timeseries import Timeseries
from jobs.amwg import AMWG
from jobs.e3smdiags import E3SMDiags
from jobs.aprime import Aprime
from jobs.cmor import Cmor
from jobs.mpasanalysis import MPASAnalysis
from jobs.ilamb import ILAMB
from lib.jobstatus import JobStatus, StatusMap, ReverseMap
from lib.jobinfo import JobInfo

job_map = {
    'climo': Climo,
    'timeseries': Timeseries,
    'regrid': Regrid,
    'e3sm_diags': E3SMDiags,
    'amwg': AMWG,
    'aprime': Aprime,
    'cmor': Cmor,
    'mpas_analysis': MPASAnalysis,
    'ilamb': ILAMB
}


class RunManager(object):

    def __init__(self, event_list, event, config, filemanager):

        self.config = config
        self.account = config['global'].get('account', '')
        self.event_list = event_list
        self.filemanager = filemanager
        self.dryrun = True if config['global']['dryrun'] == True else False
        self.debug = True if config['global']['debug'] == True else False
        self._resource_path = config['global']['resource_path']
        """
        A list of cases, dictionaries structured as:
            case (str): the full case name
            jobs (list): a list of job.Jobs
            short_name (str): the short name of the case
        """
        self.cases = list()

        self.running_jobs = list()
        self.kill_event = event
        self._job_total = 0
        self._job_complete = 0

        try:
            self.manager = Slurm()
        except:
            try:
                self.manager = PBS()
            except:
                raise Exception(
                    "Couldnt find either a slurm or PBS resource manager")

        max_jobs = config['global']['max_jobs']
        self.max_running_jobs = max_jobs if max_jobs else self.manager.get_node_number() * 3
        while self.max_running_jobs == 0:
            sleep(1)
            msg = 'Unable to communication with scontrol, checking again'
            print_line(msg, event_list)
            logging.error(msg)
            self.max_running_jobs = self.manager.get_node_number() * 3

    def _duplicate_check(self, job):
        """
        iterate over all the jobs and check if the input job is already in the list

        Parameters
        ----------
            job (Job): The job to check for duplicates
        Returns
        -------
            True if there is a duplicate
            False if there is NO duplicate
        """
        case = [x for x in self.cases if x['case'] == job.case].pop()
        if case:
            for other_job in case['jobs']:
                if job.job_type == other_job.job_type \
                        and job.start_year == other_job.start_year \
                        and job.end_year == other_job.end_year:
                    if job.run_type:
                        if job.run_type == other_job.run_type:
                            return True
                    else:
                        if job.comparison:
                            if job.comparison == other_job.comparison:
                                return True
        return False

    def add_pp_type_to_cases(self, freqs, job_type, start, end, case, run_type=None):
        """
        Add post processing jobs to the case.jobs list

        Parameters:
            freqs (list, int, None): the year length frequency to add this job
            job_type (str): what type of job to add
            start (int): the first year of simulated data
            end (int): the last year of simulated data
            data_type (str): what type of data to run this job on (regrid atm or lnd only)
            case (dict): the case to add this job to
            """
        if not freqs:
            freqs = end - start + 1
        if not isinstance(freqs, list):
            freqs = [freqs]

        for year in range(start, end + 1):
            for freq in freqs:
                freq = int(freq)
                if (year - start) % freq == 0:
                    job_end = year + freq - 1
                    if job_end > end:
                        job_end = end
                    new_job = job_map[job_type](
                        short_name=case['short_name'],
                        case=case['case'],
                        start=year,
                        end=job_end,
                        run_type=run_type,
                        config=self.config)
                    if not self._duplicate_check(new_job):
                        case['jobs'].append(new_job)

    def add_diag_type_to_cases(self, freqs, job_type, start, end, case):
        """
        Add diagnostic jobs to the case.jobs list

        Parameters:
            freqs (list): a list of year lengths to add this job for
            job_type (str): the name of the job type to add
            start (int): the first year of simulated data
            end (int): the last year of simulated data
            case (dict): the case to add this job to
        """
        if not isinstance(freqs, list):
            freqs = [freqs]
        for year in range(start, end + 1):
            for freq in freqs:
                freq = int(freq)
                if (year - start) % freq == 0:
                    # get the comparisons from the config
                    comparisons = self.config['simulations'][case['case']].get(
                        'comparisons')
                    # if this case has no comparisons move on
                    if not comparisons:
                        return
                    if job_type == 'aprime':
                        comparisons = ['obs']
                    job_end = year + freq - 1
                    if job_end > end:
                        job_end = end
                    # for each comparison, add a job to this case
                    for item in comparisons:
                        if item == 'all':
                            for other_case in self.config['simulations']:
                                if other_case in ['start_year', 'end_year', case['case']]:
                                    continue
                                new_diag = job_map[job_type](
                                    short_name=case['short_name'],
                                    case=case['case'],
                                    start=year,
                                    end=job_end,
                                    comparison=other_case,
                                    config=self.config)
                                if not self._duplicate_check(new_diag):
                                    case['jobs'].append(new_diag)
                            new_diag = job_map[job_type](
                                short_name=case['short_name'],
                                case=case['case'],
                                start=year,
                                end=job_end,
                                comparison='obs',
                                config=self.config)
                            if not self._duplicate_check(new_diag):
                                case['jobs'].append(new_diag)
                        else:
                            new_diag = job_map[job_type](
                                short_name=case['short_name'],
                                case=case['case'],
                                start=year,
                                end=job_end,
                                comparison=item,
                                config=self.config)
                            if not self._duplicate_check(new_diag):
                                case['jobs'].append(new_diag)

    def setup_cases(self):
        """
        Setup each case with all the jobs it will need
        """
        start = self.config['simulations']['start_year']
        end = self.config['simulations']['end_year']
        for case in self.config['simulations']:
            if case in ['start_year', 'end_year']:
                continue
            self.cases.append({
                'case': case,
                'short_name': self.config['simulations'][case]['short_name'],
                'jobs': list()
            })

        pp = self.config.get('post-processing')
        if pp:
            for key, val in pp.items():
                cases_to_add = list()
                for case in self.cases:
                    if not self.config['simulations'][case['case']].get('job_types'):
                        continue
                    if 'all' in self.config['simulations'][case['case']]['job_types'] or key in self.config['simulations'][case['case']]['job_types']:
                        cases_to_add.append(case)
                if key in ['regrid', 'timeseries']:
                    for dtype in val:
                        if dtype not in self.config['data_types']:
                            continue
                        for case in cases_to_add:
                            if 'all' in self.config['simulations'][case['case']]['data_types'] or dtype in self.config['simulations'][case['case']]['data_types']:
                                self.add_pp_type_to_cases(
                                    freqs=val.get('run_frequency'),
                                    job_type=key,
                                    start=start,
                                    end=end,
                                    run_type=dtype,
                                    case=case)
                else:
                    for case in cases_to_add:
                        self.add_pp_type_to_cases(
                            freqs=val.get('run_frequency'),
                            job_type=key,
                            start=start,
                            end=end,
                            case=case)
        diags = self.config.get('diags')
        if diags:
            for key, val in diags.items():
                # cases_to_add = list()
                for case in self.cases:
                    if not self.config['simulations'][case['case']].get('job_types'):
                        continue
                    if 'all' in self.config['simulations'][case['case']]['job_types'] or key in self.config['simulations'][case['case']]['job_types']:
                        self.add_diag_type_to_cases(
                            freqs=diags[key]['run_frequency'],
                            job_type=key,
                            start=start,
                            end=end,
                            case=case)

        self._job_total = 0
        for case in self.cases:
            self._job_total += len(case['jobs'])

    def setup_jobs(self):
        """
        Setup the dependencies for each job in each case
        """
        for case in self.cases:
            for job in case['jobs']:
                if job.comparison != 'obs':
                    other_case, = filter(
                        lambda case: case['case'] == job.comparison, self.cases)
                    job.setup_dependencies(
                        jobs=case['jobs'],
                        comparison_jobs=other_case['jobs'])
                else:
                    job.setup_dependencies(
                        jobs=case['jobs'])

    def check_data_ready(self):
        """
        Loop over all jobs, checking if their data is ready, and setting
        the internal job.data_ready variable
        """
        for case in self.cases:
            for job in case['jobs']:
                job.check_data_ready(self.filemanager)

    def start_ready_jobs(self):
        """
        Loop over the list of jobs for each case, first setting up the data for, and then
        submitting each job to the queue
        """
        for case in self.cases:
            for job in case['jobs']:
                if job.status != JobStatus.VALID:
                    continue
                if len(self.running_jobs) >= self.max_running_jobs:
                    msg = 'running {} of {} jobs, waiting for queue to shrink'.format(
                        len(self.running_jobs), self.max_running_jobs)
                    if self.debug:
                        print_line(msg, self.event_list)
                    return
                deps_ready = True
                for depjobid in job.depends_on:
                    depjob = self.get_job_by_id(depjobid)
                    if depjob.status != JobStatus.COMPLETED:
                        deps_ready = False
                        break
                if deps_ready and job.data_ready:

                    # if the job was finished by a previous run of the processflow
                    valid = job.postvalidate(
                        self.config, event_list=self.event_list)
                    if valid:
                        job.status = JobStatus.COMPLETED
                        self._job_complete += 1
                        job.handle_completion(
                            filemanager=self.filemanager,
                            event_list=self.event_list,
                            config=self.config)
                        self.report_completed_job()
                        msg = '{}: Job previously computed, skipping'.format(
                            job.msg_prefix())
                        print_line(msg, self.event_list)
                        continue

                    # the job is ready for submission
                    if job.run_type is not None:
                        msg = '{}: Job ready, submitting to queue'.format(
                            job.msg_prefix())
                    elif isinstance(job, Diag):
                        msg = '{}: Job ready, submitting to queue'.format(
                            job.msg_prefix())
                    else:
                        msg = '{}: Job ready, submitting to queue'.format(
                            job.msg_prefix())
                    print_line(msg, self.event_list)

                    # set to pending before data setup so we dont double submit
                    job.status = JobStatus.PENDING

                    # setup the data needed for the job
                    job.setup_data(
                        config=self.config,
                        filemanager=self.filemanager,
                        case=job.case)
                    # if this job needs data from another case, set that up too
                    if job.comparison != 'obs':
                        job.setup_data(
                            config=self.config,
                            filemanager=self.filemanager,
                            case=job.comparison)
                    if not job.prevalidate():
                        msg = '{}: Prevalidation FAILED'.format(
                            job.msg_prefix())
                        print_line(msg, self.event_list)
                        job.status = JobStatus.FAILED
                    else:
                        run_id = job.execute(
                            config=self.config,
                            dryrun=self.dryrun,
                            event_list=self.event_list)
                        if run_id == 0:
                            job.status = JobStatus.COMPLETED
                        else:
                            self.running_jobs.append({
                                'manager_id': run_id,
                                'job_id': job.id
                            })
                        

    def get_job_by_id(self, jobid):
        for case in self.cases:
            for job in case['jobs']:
                if job.id == jobid:
                    return job
        raise Exception("no job with id {} found".format(jobid))

    def write_job_sets(self, path):
        out_str = ''
        with open(path, 'w') as fp:
            for case in self.cases:
                out_str += '\n==' + '='*len(case['case']) + '==\n'
                out_str += '# {} #\n'.format(case['case'])
                out_str += '==' + '='*len(case['case']) + '==\n'
                for job in case['jobs']:
                    out_str += '\n\tname: ' + job.job_type
                    out_str += '\n\tperiod: {:04d}-{:04d}'.format(
                        job.start_year, job.end_year)
                    if job._run_type:
                        out_str += '\n\trun_type: ' + job._run_type
                    out_str += '\n\tstatus: ' + job.status.name
                    deps_jobs = [self.get_job_by_id(x) for x in job.depends_on]
                    if deps_jobs:
                        out_str += '\n\tdependent_on: ' + str(
                            ['{}'.format(x.msg_prefix()) for x in deps_jobs])
                    out_str += '\n\tdata_ready: ' + str(job.data_ready)
                    out_str += '\n\tprocessflow_id: ' + job.id
                    out_str += '\n\tmanager_id: ' + str(job.job_id)
                    if case['jobs'].index(job) != len(case['jobs']) - 1:
                        out_str += '\n------------------------------------'
                    else:
                        out_str += '\n'
            fp.write(out_str)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    def _precheck(self, year_set, jobtype, data_type=None):
        """
        Check that the jobtype for that given yearset isnt
        already in the job_list

        Parameters:
            set_number (int): the yearset number to check
            jobtype (str): the type of job to check for
        Returns:
            1 if the job/yearset combo are NOT in the job_list
            0 if they are
        """
        for job in year_set.jobs:
            if job.type == jobtype:
                if job.type != 'regrid':
                    return False
                else:  # regrid is the only job type that can have multiple instances in a year_set
                    if job.data_type == data_type:  # but only one instance per data type
                        return False
        return True

    def report_completed_job(self):
        msg = '{complete}/{total} jobs complete or {percent:.2f}%'.format(
            complete=self._job_complete,
            total=self._job_total,
            percent=(((self._job_complete * 1.0)/self._job_total)*100))
        print_line(msg, self.event_list)

    def monitor_running_jobs(self):
        """
        Lookup job status for all current jobs, 
        start jobs that are ready, 
        run post-completion handlers for any jobs that have failed or completed.

        Any new jobs that are started are added to the self.running_jobs list
        """
        for_removal = list()
        for item in self.running_jobs:
            # each item is a mapping of job UUIDs to the id given by the resource manager
            job = self.get_job_by_id(item['job_id'])
            if item['manager_id'] == 0:
                self._job_complete += 1
                for_removal.append(item)
                job.handle_completion(
                    filemanager=self.filemanager,
                    event_list=self.event_list,
                    config=self.config)
                self.report_completed_job()
                continue
            try:
                job_info = self.manager.showjob(item['manager_id'])
                if job_info.state is None:
                    continue
            except Exception as e:
                # if the job is old enough it wont be in the slurm list anymore
                # which will throw an exception
                self._job_complete += 1
                for_removal.append(item)

                valid = job.postvalidate(
                    self.config, event_list=self.event_list)
                if valid:
                    job.status = JobStatus.COMPLETED
                    job.handle_completion(
                        filemanager=self.filemanager,
                        event_list=self.event_list,
                        config=self.config)
                    self.report_completed_job()
                else:
                    job.status = JobStatus.FAILED
                    line = "{job}: resource manager lookup error for jobid {id}. The job may have failed, check the error output".format(
                        job=job.msg_prefix(),
                        id=item['manager_id'])
                    print_line(
                        line=line,
                        event_list=self.event_list)
                continue
            status = StatusMap[job_info.state]
            if status != job.status:
                msg = '{prefix}: Job changed from {s1} to {s2}'.format(
                    prefix=job.msg_prefix(),
                    s1=ReverseMap[job.status],
                    s2=ReverseMap[status])
                print_line(msg, self.event_list)
                job.status = status

                if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    self._job_complete += 1
                    valid = job.postvalidate(
                        self.config, event_list=self.event_list)
                    if not valid:
                        job.status = JobStatus.FAILED
                    job.handle_completion(
                        filemanager=self.filemanager,
                        event_list=self.event_list,
                        config=self.config)
                    for_removal.append(item)
                    self.report_completed_job()
                    if status in [JobStatus.FAILED, JobStatus.CANCELLED]:
                        for depjob in self.get_jobs_that_depend(job.id):
                            depjob.status = JobStatus.FAILED
        if for_removal:
            self.running_jobs = [
                x for x in self.running_jobs if x not in for_removal]
        return

    def get_jobs_that_depend(self, job_id):
        """
        returns a list of all jobs that depend on the give job
        """
        jobs = list()
        for case in self.cases:
            for job in case['jobs']:
                for depid in job.depends_on:
                    if depid == job_id:
                        jobs.append(job)
        return jobs

    def is_all_done(self):
        """
        Check if all jobs are done, and all processing has been completed

        return -1 if still running
        return 0 if a job failed
        return 1 if all complete
        """
        if len(self.running_jobs) > 0:
            return -1

        failed = False
        for case in self.cases:
            for job in case['jobs']:
                if job.status in [JobStatus.VALID, JobStatus.PENDING, JobStatus.RUNNING]:
                    return -1
                if job.status in [JobStatus.FAILED, JobStatus.CANCELLED]:
                    failed = True
        if failed:
            return 0
        return 1
