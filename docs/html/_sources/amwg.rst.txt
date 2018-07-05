***************
AMWG Diagnostic
***************

The `AMWG Diagsnostic <http://www.cesm.ucar.edu/working_groups/Atmosphere/amwg-diagnostics-package/>`_ is the standard atmospheric diagnostic package.

Prerequsite jobs and data
-------------------------

AMWG requires the 'atm' data type, and the 'climo' job type.


Sample Configuration
--------------------

These are all the config options needed to run an amwg processflow job. Note that many of the options would be identical if running
a whole set of jobs at different years, or on many cases.

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
    
    [post-processing]
        [[climo]]
            run_frequency = 2
            destination_grid_name = fv129x256
            regrid_map_path = /p/cscratch/acme/data/map_ne30np4_to_fv129x256_aave.20150901.nc

    [diags]
        [[amwg]]
            run_frequency = 2
            diag_home = /p/cscratch/acme/amwg/amwg_diag
    
    [data_types]
        [[atm]]
            remote_path = 'REMOTE_PATH/archive/atm/hist'
            file_format = 'CASEID.cam.h0.YEAR-MONTH.nc'
            local_path = 'PROJECT_PATH/input/CASEID/atm'
            monthly = True

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

Dependencies
------------

For each year set that AMWG is configured to run, it requires regridded climatologies created by ncclimo. This means any case running an amwg job
just also have a climo job for each frequency that amwg is running.
