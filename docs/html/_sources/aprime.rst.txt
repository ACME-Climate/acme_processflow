******************
APrime Diagnostics
******************

`APrime <https://github.com/ACME-Climate/a-prime>`_ runs a subset of atmospheric plots, as well
as the MPAS ocean analysis, including ENSO diagnostics.

Prerequsite jobs and data
-------------------------

Aprime diagnostics requires the following data types, and has no job type prerequsites:

    * atm
    * cice
    * cice_restart
    * cice_streams
    * cice_in
    * ocn
    * ocn_restart
    * ocn_streams
    * ocn_in
    * meridionalHeatTransport


Sample Configuration
--------------------

See :doc:`configuration` for an explanation of each config option.

.. code-block:: python

    [global]
        project_path = /p/user_pub/e3sm/baldwin32/testing/
        email = baldwin32@llnl.gov

    [img_hosting]
        img_host_server = acme-viewer.llnl.gov
        host_directory = /var/www/acme/acme-diags/baldwin32/
        url_prefix = 'baldwin32'
    
    [simulations]
        start_year = 1
        end_year = 2
        [[20180129.DECKv1b_piControl.ne30_oEC.edison]]
            transfer_type = globus
            remote_uuid = 9d6d994a-6d04-11e5-ba46-22000b92c6ec
            remote_path = /global/homes/r/renata/ACME_simulations/20180129.DECKv1b_piControl.ne30_oEC.edison
            short_name = piControl
            native_grid_name = ne30
            native_mpas_grid_name = oEC60to30v3
            data_types = all
            job_types = climo, amwg
        [[comparisons]]
            20180129.DECKv1b_piControl.ne30_oEC.edison = obs

    [diags]
        [[aprime]]
            run_frequency = 2
            aprime_code_path = /p/cscratch/acme/data/a-prime
    
    [data_types]
        [[atm]]
            remote_path = 'REMOTE_PATH/archive/atm/hist'
            file_format = 'CASEID.cam.h0.YEAR-MONTH.nc'
            local_path = 'PROJECT_PATH/input/CASEID/atm'
            monthly = True
        [[cice]]
            remote_path = 'REMOTE_PATH/archive/ice/hist'
            file_format = 'mpascice.hist.am.timeSeriesStatsMonthly.YEAR-MONTH-01.nc'
            local_path = 'PROJECT_PATH/input/CASEID/ice'
            monthly = True
        [[ocn]]
            remote_path = 'REMOTE_PATH/archive/ocn/hist'
            file_format = 'mpaso.hist.am.timeSeriesStatsMonthly.YEAR-MONTH-01.nc'
            local_path = 'PROJECT_PATH/input/CASEID/ocn'
            monthly = True
        [[ocn_restart]]
            remote_path = 'REMOTE_PATH/archive/rest/REST_YR-01-01-00000/'
            file_format = 'mpaso.rst.REST_YR-01-01_00000.nc'
            local_path = 'PROJECT_PATH/input/CASEID/rest'
            monthly = False
        [[cice_restart]]
            remote_path = 'REMOTE_PATH/archive/rest/REST_YR-01-01-00000/'
            file_format = 'mpascice.rst.REST_YR-01-01_00000.nc'
            local_path = 'PROJECT_PATH/input/CASEID/rest'
            monthly = False
        [[ocn_streams]]
            remote_path = 'REMOTE_PATH/run'
            file_format = 'streams.ocean'
            local_path = 'PROJECT_PATH/input/CASEID/mpas'
            monthly = False
        [[cice_streams]]
            remote_path = 'REMOTE_PATH/run'
            file_format = 'streams.cice'
            local_path = 'PROJECT_PATH/input/CASEID/mpas'
            monthly = False
        [[ocn_in]]
            remote_path = 'REMOTE_PATH/run'
            file_format = 'mpas-o_in'
            local_path = 'PROJECT_PATH/input/CASEID/mpas'
            monthly = False
        [[cice_in]]
            remote_path = 'REMOTE_PATH/run'
            file_format = 'mpas-cice_in'
            local_path = 'PROJECT_PATH/input/CASEID/mpas'
            monthly = False
        [[meridionalHeatTransport]]
            remote_path = 'REMOTE_PATH/archive/ocn/hist'
            file_format = 'mpaso.hist.am.meridionalHeatTransport.START_YR-02-01.nc'
            local_path = 'PROJECT_PATH/input/CASEID/mpas'
            monthly = False

* [global]: These are mandatory global config options used by all jobs
* project_path: This is the root path to where to store all project data on the local machine
* email: The email address to send notification emails

* [img_hosting]: This are optional config keys for hosting diagnotsic output, simply remove this section to turn off web hosting
* img_host_server: The base url of the webserver, used for constructing the notification email links.
* host_directory: The base directory for where to put output for web hosting, the user must have write permission here. Directories will be created for each simulation case, with jobs for the case stored below it.
* url_prefix: Notification urls are constructed as https://{img_host_server}/{url_prefix}/{case}/{diagnostic}

* [simulations]: The config group for the simulation cases
* [[20180129.DECKv1b_piControl.ne30_oEC.edison]]: This both is the full name of the simulation case, and creates a new config group for all options relating to this case
* transfer_type: This can be either 'globus' for file transfers using globus, 'sftp' for using an ssh client, or 'local' if the data is already on the local machine
* remote_uuid: This is the unique identifier for the remote globus node, only needed if transfer_type is set to 'globus'
* remote_path: The base path of the remote case, should not include /run or /archive
* short_name: A nice short name for this case, can be any string
* native_grid_name: The name of the native grid, can be any string
* native_mpas_grid_name: The name of the native mpas grid for this case, can be any string
* data_types: Which of the data types should be transfered for this case, names should match the types declared in the data_types section
* job_types: Which job types should be run for this case. Note here how amwg requires climo.

* [post-processing]: the config group for all post processing jobs
* [[climo]]: The config group for generating climatologies
* run_frequency: This can be a single integer or a list of integers. It denotes the frequencies that the amwg job should be run. For example if set to 5, 10, 50, then climatology jobs will be generated for each 5 years, 10 years, and 50 year set. For 100 years of data there would be 20 sets of 5 yeas, 10 sets of 10 years, and 2 sets of 50 years.
* regrid_map_path: The path a the appropriate regrid map file.
* destination_grid_name: name of the destination grid, used to create the directory the regridded output is stored in, this can be any string.

* [diags]: The config group for all diagnostic jobs
* [[amwg]]: The config group for amwg jobs
* run_frequency: This can be a single integer or a list of integers. It denotes the frequencies that the amwg job should be run. For example if set to 5, 10, 50, then amwg jobs will be generated for each 5 years, 10 years, and 50 year set. For 100 years of data there would be 20 sets of 5 yeas, 10 sets of 10 years, and 2 sets of 50 years.

* [data_types]: The config group to declare and define data types. For more detail see the data_types doc page.
* [[atm]]: This is a special data type for atmospheric data. 
* remote_path: This is a string that will be rendered at run time for each data file, for where to find the file on the remote machine.
* file_format: This is the format for how to render the file name.
* local_path: This denotes where to store the file on the local machine.
* monthly: A boolean flag (should be either True or False) for if this is monthly output or a one-off file.
