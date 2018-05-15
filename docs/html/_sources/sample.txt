.. _sample:

******
Sample
******

This is a sample configuration file.

.. code-block:: bash

    [global]
    # The root local directory to store project data as
    # well as post processing output
    project_path = /PATH/TO/YOUR/NEW/PROJECT/DIRECTORY

    # The path on the remote machine to look for model output
    # This should be on the remote machine that ran the simulation
    source_path = /PATH/TO/YOUR/SIMULATION

    # The year to start the post processing, typically 1
    # If the first year of the simulation is 0001, use 1, but if
    #  it started later e.g. 1980, use 1980
    simulation_start_year =  51

    # The last year to run post processing jobs on
    # The highest number year, so if your simulation starts in 1980
    #   and you want to process 20 years, this should be 2000
    simulation_end_year = 60

    # The list of year lengths to run jobs on
    # If you want the diagnostics run every 5 years, add 5 to this list
    # If you want a single time series run, add the length of the simulation to the list
    #   and just add timeseries to that frequency
    set_frequency = 5, 10

    # The experiment name
    # for example 20170731.F20TR_ck10.ne30_ne30.edison
    experiment = YOUR.SIMULATION.NAME

    # A nice short name for the AMWG and e3sm diags plots
    short_name = 'MODEL_RUN_NAME'

    # The email address to send to when all processing is complete, leave commented out to turn off
    email = YOUREMAIL@INSTITUION.GOV

    # Turn on (1) if you've run short term archiving on your model data
    # Turn off (0) otherwise
    short_term_archive = 0

    # Should the native grid files be cleaned up on successful exit?
    native_grid_cleanup = 0

    # name of the native grid
    native_grid_name = 'ne30'

    # name of the remapped grid
    remap_grid_name = 'fv129x256'

    # The base URL for the server thats hosting image output
    img_host_server = https://acme-viewer.llnl.gov

    # the base path for web hosting
    host_directory = /var/www/acme/acme-diags/

    # Types of files to transfer
    file_types = 'atm', 'ice', 'ocn', 'rest', 'streams.ocean', 'streams.cice', 'mpas-o_in', 'mpas-cice_in', 'meridionalHeatTransport'

    # The jobs to run on each set, to turn off the job entirely leave its value blank
    [[set_jobs]]
        # this will run ncclimo for both 5 and 10
        ncclimo = 5, 10
        # this will run time series only at 10
        timeseries = 20
        # this will run amwg only at 5
        amwg = 5, 10
        # this will turn off the coupled diag
        aprime_diags =
        e3sm_diags = 10

    [e3sm_diags]
    host_directory = e3sm-diags
    backend = mpl
    seasons = DJF, MAM, JJA, SON, ANN
    reference_data_path = /p/cscratch/acme/data/obs_for_acme_diags
    sets = 3, 4, 5, 7, 13

    [transfer]
    # The Globus endpoint ID for the local host
    destination_endpoint = a871c6de-2acd-11e7-bc7c-22000b9a448b

    # The Globus endpoint ID for the remote host
    source_endpoint = 9d6d994a-6d04-11e5-ba46-22000b92c6ec

    [amwg]
    # The location of the amwg code
    diag_home = /p/cscratch/acme/amwg/amwg_diag

    # The directory to copy output to for hosting
    host_directory = amwg


    [ncclimo]
    # Path to the regird map
    regrid_map_path = /p/cscratch/acme/data/map_ne30np4_to_fv129x256_aave.20150901.nc

    # A list of variables to generate timeseries files for
    var_list = FSNTOA, FLUT, FSNT, FLNT, FSNS, FLNS, SHFLX, QFLX, PRECC, PRECL, PRECSC, PRECSL, TS, TREFHT


    [aprime_diags]
    # The directory to copy plots for hosting
    host_directory = aprime-diags

    # The code directory for coupled_diags
    aprime_code_path = /p/cscratch/acme/data/a-prime

    test_atm_res = ne30
    test_mpas_mesh_name = oEC60to30v3