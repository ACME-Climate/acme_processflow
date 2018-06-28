.. _configuration:

*****************
Run Configuration
*****************


Run configuration is broken into 6 major sections:

    * global: options used by all components
    * img_hosting: options used for hosting diagnostic output
    * simulations: options related to each case being run, and how case-vs-case comparisons should be configured
    * post-processing: all options related to post processing jobs
    * diags: all options related to diagnostic runs
    * data_types: definitions of which data types are required, and how to find data files


global
------

The global section has the following keys: 
    * project_path: This is the base of the project directory tree. All input and output will be stored here under /input/ and /output/
    * email: This is an email address to send notification emails to
    * native_grid_cleanup: This is a boolean flag to denoting if the native grid files produced by post processing jobs should be deleted after all jobs successfully complete
    * local_globus_uuid: The local globus transfer nodes unique id. This is optional and only required if using globus for file transfers

img_hosting
-----------

This is an optional section, only needed if the user would like to turn on web hosting for diagnostic plot output. To turn this off, simply remove this section from the configuration.
    * img_host_server: The base url of the webserver, used for constructing the notification email links.
    * host_directory: The base directory for where to put output for web hosting, the user must have write permission here. Directories will be created for each simulation case, with jobs for the case stored below it.
    * url_prefix: Notification urls are constructed as https://{img_host_server}/{url_prefix}/{case}/{diagnostic} 

simulations
-----------

This section is used for configuring each case. As many cases can be placed here as the user would like. 
The cases can be very different from each other, use different naming conventions (see data_types), and have their data stored in different file structures. 
The one thing they must all share in common is the start_year and end_year.
    * start_year: the first year of data to be used. For example, if start_year is set to 5, then files with years >= 5 && <= end_year will be concidered as part of the data set.
    * end_year: the last year of data. For example if end_year is 10, then files with years >= start_year && <= 10 will be concidered as part of the dataset.

    Each case must exist in its own config section, denoted by [[CASEID]] the double brackets are important.
    * [[CASEID]] this should be the full case name e.g. 20180129.DECKv1b_piControl.ne30_oEC.edison
    * transfer_type: this can be any of three values, 'local', 'globus', or 'sftp'
    * ---> if transfer_type == 'globus' then remote_uuid and remote_path must be included
    * ---> if transfer_type == 'sftp' then remote_hostname and remote_path must be included
    * ---> if transfer_type == 'local' then local_path must be included
    * short_name: a nice short name for the case
    * native_grid_name: the name of the native grid used in the land and atmospheric components
    * native_mpas_grid_name: the name of the mpas grid
    * data_types: which data types should be copied for this case, this must include all data_types needed for jobs this case will be running
    * job_types: which of the job types should be run on this case. Use the keyword 'all' to run all defined jobs on this case

    If running diagnostic jobs, the following section must be included
    * [[comparisons]] this is the list of comparisons between for each case. Each case should have an entry here, followed by which other cases it should be compared to
    
    example:
    * case_1: obs (a key word denoting model-vs-obs comparison), case_2
    * case_2: case_3
    * case_3: all

    In this example the following comparison diagnostics jobs will be generated:
    * case_1-vs-obs, case_1-vs-case_2
    * case_2-vs-case_3
    * case_3-vs-case_1, case_3-vs-case_2, case_3-vs-obs
    * note how case_2-vs-case_3 and case_3-vs-case_2 were both created


