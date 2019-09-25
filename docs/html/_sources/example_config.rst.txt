.. _example_config:

**************
Example Config
**************


This is an example configuration used on acme1 with three cases.
This config will run climatology generation, regrid output, create
timeseries, as well as run the e3sm_diag, AMWG, and aprime diagnostics
suits.

::

    [global]
    project_path = /p/user_pub/e3sm/baldwin32/model_v_model
    email = baldwin32@llnl.gov

    [img_hosting]
        img_host_server = acme-viewer.llnl.gov
        host_directory = /var/www/acme/acme-diags/baldwin32/
        url_prefix = 'baldwin32'

    [simulations]
        start_year = 1
        end_year = 2
        [[20180129.DECKv1b_piControl.ne30_oEC.edison]]
            short_name = piControl
            native_grid_name = ne30
            native_mpas_grid_name = oEC60to30v3
            data_types = all
            job_types = all
            comparisons = obs
        [[20180215.DECKv1b_1pctCO2.ne30_oEC.edison]]
            short_name = 1pctCO2
            native_grid_name = ne30
            native_mpas_grid_name = oEC60to30v3
            data_types = all
            job_types = all
            comparisons = 20180129.DECKv1b_piControl.ne30_oEC.edison
        [[20180215.DECKv1b_abrupt4xCO2.ne30_oEC.edison]]
            short_name = abrupt4xCO2
            native_grid_name = ne30
            native_mpas_grid_name = oEC60to30v3
            data_types = atm, lnd
            job_types = e3sm_diags, amwg, climo
            comparisons = all

    [post-processing]
        [[climo]]
            run_frequency = 2
            destination_grid_name = fv129x256
            regrid_map_path = /p/cscratch/acme/data/map_ne30np4_to_fv129x256_aave.20150901.nc

        [[timeseries]]
            run_frequency = 2
            destination_grid_name = fv129x256
            regrid_map_path = /p/cscratch/acme/data/map_ne30np4_to_fv129x256_aave.20150901.nc
            atm = FSNTOA, FLUT, FSNT, FLNT, FSNS, FLNS, SHFLX, QFLX, PRECC, PRECL, PRECSC, PRECSL, TS, TREFHT
            lnd = SOILICE, SOILLIQ, SOILWATER_10CM, QINTR, QOVER, QRUNOFF, QSOIL, QVEGT, TSOI

        [[regrid]]
            [[[lnd]]]
                source_grid_path = /export/zender1/data/grids/ne30np4_pentagons.091226.nc
                destination_grid_path = /export/zender1/data/grids/129x256_SCRIP.20150901.nc
                destination_grid_name = fv129x256
            [[[atm]]]
                regrid_map_path = /p/cscratch/acme/data/map_ne30np4_to_fv129x256_aave.20150901.nc
                destination_grid_name = fv129x256
            [[[ocn]]]
                regrid_map_path = ~/grids/map_oEC60to30v3_to_0.5x0.5degree_bilinear.nc
                destination_grid_name = 0.5x0.5degree_bilinear


    [diags]
        [[e3sm_diags]]
            run_frequency = 2
            backend = mpl
            reference_data_path = /p/cscratch/acme/data/obs_for_acme_diags

        [[amwg]]
            run_frequency = 2
            diag_home = /p/cscratch/acme/amwg/amwg_diag
            sets = all

        [[aprime]]
            run_frequency = 2
            host_directory = aprime-diags
            aprime_code_path = /p/cscratch/acme/data/a-prime

        [[mpas_analysis]]
            mapping_directory = /space2/diagnostics/mpas_analysis/maps
            generate_plots = all_publicObs
            start_year_offset = True
            ocn_obs_data_path = /space2/diagnostics/observations/Ocean/
            seaice_obs_data_path = /space2/diagnostics/observations/SeaIce/
            region_mask_path = /space2/diagnostics/mpas_analysis/region_masks
            run_MOC = True
            ocean_namelist_name = mpaso_in
            seaice_namelist_name = mpassi_in

    [data_types]
        [[atm]]
            file_format = CASEID.cam.h0.YEAR-MONTH.nc
            local_path = PROJECT_PATH/input/CASEID/atm
            monthly = True
            [[[20180215.DECKv1b_abrupt4xCO2.ne30_oEC.edison]]]
                local_path = LOCAL_PATH/atm
        [[lnd]]
            file_format = CASEID.clm2.h0.YEAR-MONTH.nc
            local_path = PROJECT_PATH/input/CASEID/lnd
            monthly = True
            [[[20180215.DECKv1b_abrupt4xCO2.ne30_oEC.edison]]]
                local_path = LOCAL_PATH/lnd
        [[cice]]
            file_format = mpascice.hist.am.timeSeriesStatsMonthly.YEAR-MONTH-01.nc
            local_path = PROJECT_PATH/input/CASEID/ice
            monthly = True
        [[ocn]]
            file_format = mpaso.hist.am.timeSeriesStatsMonthly.YEAR-MONTH-01.nc
            local_path = PROJECT_PATH/input/CASEID/ocn
            monthly = True
        [[ocn_restart]]
            file_format = mpaso.rst.REST_YR-01-01_00000.nc
            local_path = PROJECT_PATH/input/CASEID/rest
            monthly = False
        [[cice_restart]]
            file_format = mpascice.rst.REST_YR-01-01_00000.nc
            local_path = PROJECT_PATH/input/CASEID/rest
            monthly = False
        [[ocn_streams]]
            file_format = streams.ocean
            local_path = PROJECT_PATH/input/CASEID/mpas
            monthly = False
        [[cice_streams]]
            file_format = streams.cice
            local_path = PROJECT_PATH/input/CASEID/mpas
            monthly = False
        [[ocn_in]]
            file_format = mpas-o_in
            local_path = PROJECT_PATH/input/CASEID/mpas
            monthly = False
        [[cice_in]]
            file_format = mpas-cice_in
            local_path = PROJECT_PATH/input/CASEID/mpas
            monthly = False
        [[meridionalHeatTransport]]
            file_format = mpaso.hist.am.meridionalHeatTransport.START_YR-02-01.nc
            local_path = PROJECT_PATH/input/CASEID/mpas
            monthly = False
