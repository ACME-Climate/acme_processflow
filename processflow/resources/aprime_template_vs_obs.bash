#!/bin/bash
#
# Copyright (c) 2017, UT-BATTELLE, LLC
# All rights reserved.
# 
# This software is released under the BSD license detailed
# in the LICENSE file in the top level a-prime directory
#
#
# Template driver script to generate A-Prime coupled diagnostics on E3SM machines
#  (Supported machines/HPC centers as of June 2018 are: Edison/Cori, Rhea/Titan,
#   Blues/Anvil, Theta, aims4/acme1, and LANL)
#
# Basic usage (also see README for specific instructions on running on different machines):
#       1. Clone a-prime repository from github.com:
#            git clone git@github.com:ACME-Climate/A-Prime a-prime
#            cd a-prime
#            git submodule update --init
#       2. Download analysis input files
#            If running on supported machines (see above) all necessary input
#            files (such as mapping and mask files, and observation files) have
#            already been saved in $projdir/diagnostics/. Therefore skip to step 3.
#            On unsupported machines, retrieve the input files by running the following
#            python script in the a-prime directory:
#              ./download_analysis_data.py -o path/to/input/data
#            Then replace every instance of $projdir/diagnostics with path/to/input/data
#            in step 4 below.
#       3. Copy this template to something like run_aprime_$user.bash
#       4. Open run_aprime_$user.bash and set user defined, case-specific variables
#          These are the main variables that the user will likely have to modify
#          (more documentation details can be found where variables are defined):
#            output_base_dir: the base location where all output will go
#            test_casename: name of model case to analyze
#            test_archive_dir: directory where test_casename data sits
#            test_atm_res: resolution of atm component
#            test_mpas_mesh_name: resolution of ocn/ice component
#            test_begin_yr_climo: first year to analyze climatology
#            test_end_yr_climo: last year to analyze climatology
#            test_begin_yr_ts: first year to create time series
#            test_end_yr_ts: last year to create time series
#            ref_case: baseline (E3SM v1 and beyond) model case to compare
#                      (or 'obs' for comparison with observation)
#            ref_case_v0: baseline E3SM v0 case for comparsion to POP/CICE ocn/ice
#                         (pre-processed diagnostics)
#            generate_atm_diags: flag to produce atm diagnostics
#            generate_atm_enso_diags: flag to produce additional, ENSO-related, atm diagnostics
#            generate_ocnice_diags: flag to produce ocn/ice diagnostics
#            run_batch_script: flag to submit to batch queue or not
#            mpas_analysis_tasks: number of processors to use on a single node to run
#                                 MPAS-Analysis diagnostics. A number different from 1
#                                 is typically used when running batch jobs (run_batch_script=true)
#                                 or on specific machines (like the workflow dedicated acme1/aims4
#                                 LLNL machines) where batch jobs cannot be submitted and
#                                 more intensive jobs are 'allowed' on the login nodes.
#       5. Execute: ./run_aprime_$user.bash 
#
# List of E3SM output files that are needed for A-Prime to work:
#       - atmosphere files:
#              *.cam.h0.*.nc
#       - mpas-o files:
#              *.mpaso.hist.am.timeSeriesStatsMonthly.*.nc (Note: since OHC
#                   anomalies are computed wrt the first year of the simulation,
#                   if OHC diagnostics is activated, the analysis will need the
#                   first full year of mpaso.hist.am.timeSeriesStatsMonthly.*.nc
#                   files, no matter what begin_yr_ts, end_yr_ts are. This is
#                   especially important to know if short term archiving is
#                   used in the run to analyze: in that case, set short_term_archive
#                   to 1 and choose begin_yr_ts, end_yr_ts to include only data
#                   that have been short-term-archived).
#               *.mpaso.rst.0002-01-01_00000.nc (or any other restart file)
#               streams.ocean
#               mpaso_in (or mpas-o_in)
#       - mpas-seaice files: (note the name change from mpas-cice. As of May 2018,
#                             we are supporting *both* mpas-cice and mpas-seaice
#                             names, since many E3SM-v1 simulations were run with the
#                             old name)
#               *.mpassi.hist.am.timeSeriesStatsMonthly.*.nc (or mpascice.hist.am.timeSeriesStatsMonthly.*.nc)
#               *.mpassi.rst.0002-01-01_00000.nc (or mpascice.rst.0002-01-01_00000.nc or any other mpas-seaice restart file)
#               streams.seaice (or streams.cice)
#               mpassi_in (or mpas-cice_in)
#
# Meaning of acronyms/words used in variable names below:
#	test:		 Test case
#	ref:		 Reference case or 'obs'
#	ts: 		 Time series; e.g. test_begin_yr_ts
#       climateIndex_ts: Time series for climate indexes such as Nino3.4
#	climo: 		 Climatology
#	begin_yr: 	 Model year to start analysis 
#	end_yr:		 Model year to end analysis
#       condense:        Create a new file for each variable with time series data
#                        for that variable. This is used to create climatology (if
#                        not pre-computed) and in generating time series plots
#	archive_dir:	 Location of model generated output directory
#	scratch_dir:	 Location of directory where the user wants to store 'scratch'
#                        files generated by the diagnostics. This includes climos, remapped
#                        climos, condensed files and data files used for plotting.
#	short_term_archive: If equal to 1, the script adds archive/(modelcomponent)/hist
#                           after 'casename' to 'archive_dir'.
#

########################################################################
# PART I
# USER DEFINED, CASE-SPECIFIC VARIABLES TO SPECIFY (REQUIRED)

# Turn of hdf5 file locking
export HDF5_USE_FILE_LOCKING=FALSE

# Root directory where all analysis output is stored
# (e.g., plots will go in a specific subdirectory of $output_base_dir,
# as will log files, generated climatologies, etc)
export output_base_dir={{ output_base_dir }}

# ** Variables relevant for main test case **
#  Case Name (NB: $test_casename will be appended to $test_archive_dir)
export test_casename={{ test_casename }}
#  Root directory pointing to model data. If test_short_term_archive=0,
#  $test_casename/run will be appended to test_archive_dir. If
#  test_short_term_archive=1, $test_casename/archive/modelcomponent/hist
#  will instead be appended.
export test_archive_dir={{ test_archive_dir }}
#  Short-term archive option
export test_short_term_archive=0

#  Atmosphere grid resolution name (e.g. ne30, ne60, ne120) 
export test_atm_res={{ test_atm_res }}
#  MPAS mesh name (e.g. oEC60to30v1, oEC60to30v3, oRRS18to6v3)
#  NB: test_atm_res and test_mpas_mesh_name may change with a different choice
#  of test_casename. For example, the MPAS meshes ending with 'v1' should be
#  used for beta0 and older runs, while those ending with 'v3' should be
#  used for beta1 and newer runs.
export test_mpas_mesh_name={{ test_mpas_mesh_name }}
#  Year start/end for climatologies
export test_begin_yr_climo={{ test_begin_yr_climo }}
export test_end_yr_climo={{ test_end_yr_climo }}
#  Year start/end for time series
export test_begin_yr_ts={{ test_begin_yr_climo }}
export test_end_yr_ts={{ test_end_yr_climo }}
#  Year start/end for ocean Nino3.4 index diagnostics (both ocn/ice and
#  atm diagnostics)
export test_begin_yr_climateIndex_ts={{ test_begin_yr_climo }}
export test_end_yr_climateIndex_ts={{ test_end_yr_climo }}

#  Atmosphere switches (True(1)/False(0)) to condense variables, compute climos, remap climos and condensed time series file
#  If no pre-processing is done (climatology, remapping), all the switches below should be 1
#  If a switch is 0, then the user should ensure that the needed files are in the scratch directory (defined below)
#  If a switch is 0 for climo, then the user should ensure that the files in the scratch directory correspond to the
#  intended begin and end years set above.
export test_compute_climo=1
export test_remap_climo=1
#  The following is ignored if test_compute_climo=0. If test_condense_field_climo=1
#  and test_compute_climo=0 the script will look for a condensed file
export test_condense_field_climo=1
export test_condense_field_ts=1
export test_remap_ts=1
export test_compute_climo_enso_atm=1
export test_condense_field_enso_atm=1
export test_remap_climo_enso_atm=1
export test_remap_ts_enso_atm=1

# In the following we define some machine specific variables (such as
# projdir or the location of observational data) that the user is 
# unlikely to have to modify in most cases
if [ ${HOSTNAME:0:6} == "edison" ]; then
  export machname="edison"
elif [ ${HOSTNAME:0:4} == "cori" ]; then
  export machname="cori"
elif [ ${HOSTNAME:0:4} == "rhea" ]; then
  export machname="rhea"
elif [ ${HOSTNAME:0:5} == "titan" ]; then
  export machname="titan"
elif [ ${HOSTNAME:0:5} == "aims4" ]; then
  export machname="aims4"
elif [ ${HOSTNAME:0:5} == "acme1" ]; then
  export machname="acme1"
elif [ ${HOSTNAME:0:4} == "wolf" ] || [ ${HOSTNAME:0:7} == "grizzly" ]; then
  export machname="lanl"
elif [ ${HOSTNAME:0:6} == "blogin" ] || ([ ${HOSTNAME:0:1} == "b" ] && [[ ${HOSTNAME:1:2} =~ [0-9] ]]); then
  export machname="anvil"
elif [ ${HOSTNAME:0:6} == "cooley" ] || ([ ${HOSTNAME:0:2} == "cc" ] && [[ ${HOSTNAME:2:3} =~ [0-9] ]]); then
  export machname="cooley"
else
  echo "Unsupported host $HOSTNAME. Exiting."
  exit 1
fi
# Define project and www directories
if [ $machname == "edison" ] || [ $machname == "cori" ]; then
  # Project directory
  projdir=/global/project/projectdirs/acme
  # Location of website directory to host the webpage
elif [ $machname == "rhea" ] || [ $machname == "titan" ]; then
  projdir=$PROJWORK/cli115
elif [ $machname == "aims4" ] || [ $machname == "acme1" ]; then
  projdir=/space2
elif [ $machname == "lanl" ]; then
  projdir=/usr/projects/climate/SHARED_CLIMATE
elif [ $machname == "anvil" ]; then
  projdir=/lcrc/group/acme
elif [ $machname == "cooley" ]; then
  projdir=/lus/theta-fs0/projects/ClimateEnergy_2
fi

export www_dir={{ www_dir }}

# ** Reference case variables (similar to test_case variables) **
export ref_case=obs
export ref_archive_dir=$projdir/diagnostics/observations/Atm
# Set begin_yr, end_yr of SST observations to be used to compute
# obs climatologies to compare with the model results. Choose
# 1870-1900 for pre-industrial runs, or 1950-2011 for present-day runs.
export sstObs_begin_yr=1870
export sstObs_end_yr=1900
#export ref_case=casename
#export ref_archive_dir=dir/to/refcase_data	# $ref_case will be appended to this
export ref_short_term_archive=0

# E3SMv0 ref_case info for ocn/ice diags
# ** IMPORTANT: the E3SMv0 model data MUST have been pre-processed.
# ** IF THIS PRE_PROCESSED DATA IS NOT AVAILABLE, SET ref_case_v0=None **
export ref_case_v0=B1850C5_ne30_v0.4
if [ $machname == "edison" ] || [ $machname == "cori" ]; then
  export ref_archive_v0_ocndir=$projdir/ACMEv0_lowres/${ref_case_v0}/ocn/postprocessing
  export ref_archive_v0_seaicedir=$projdir/ACMEv0_lowres/${ref_case_v0}/ice/postprocessing
elif [ $machname == "rhea" ] || [ $machname == "titan" ]; then
  export ref_archive_v0_ocndir=$projdir/milena/ACMEv0_lowres/${ref_case_v0}/ocn/postprocessing
  export ref_archive_v0_seaicedir=$projdir/milena/ACMEv0_lowres/${ref_case_v0}/ice/postprocessing
elif [ $machname == "aims4" ] || [ $machname == "acme1" ]; then
  export ref_archive_v0_ocndir=$projdir/ACMEv0_lowres/${ref_case_v0}/ocn/postprocessing
  export ref_archive_v0_seaicedir=$projdir/ACMEv0_lowres/${ref_case_v0}/ice/postprocessing
elif [ $machname == "lanl" ]; then
  export ref_archive_v0_ocndir=$projdir/ACMEv0_lowres/${ref_case_v0}/ocn/postprocessing
  export ref_archive_v0_seaicedir=$projdir/ACMEv0_lowres/${ref_case_v0}/ice/postprocessing
elif [ $machname == "anvil" ]; then
  export ref_archive_v0_ocndir=$projdir/lvanroe/APrime_Files/ACMEv0_lowres/${ref_case_v0}/ocn/postprocessing
  export ref_archive_v0_seaicedir=$projdir/lvanroe/APrime_Files/ACMEv0_lowres/${ref_case_v0}/ice/postprocessing
elif [ $machname == "cooley" ]; then
  export ref_archive_v0_ocndir=$projdir/ACMEv0_lowres/${ref_case_v0}/ocn/postprocessing
  export ref_archive_v0_seaicedir=$projdir/ACMEv0_lowres/${ref_case_v0}/ice/postprocessing
fi

# The following are ignored if ref_case=obs
export ref_atm_res=ne30
export ref_mpas_mesh_name=oEC60to30v3
export ref_begin_yr_climo=95
export ref_end_yr_climo=100
export ref_begin_yr_ts=95
export ref_end_yr_ts=100
# NB: if ref_case=obs then the ENSO obs analysis begin year and end year should be set to 1979 and 2006:
export ref_begin_yr_climateIndex_ts=1979
export ref_end_yr_climateIndex_ts=2006
export ref_compute_climo=1
export ref_remap_climo=1
export ref_condense_field_climo=1
export ref_condense_field_ts=1
export ref_remap_ts=1
export ref_compute_climo_enso_atm=1
export ref_remap_climo_enso_atm=1
export ref_condense_field_enso_atm=1
export ref_remap_ts_enso_atm=1

# Select sets of diagnostics to generate (False = 0, True = 1)
export generate_atm_diags=1
export generate_atm_enso_diags=1
export generate_ocnice_diags=1

# The following ocn/ice diagnostic switches are ignored if generate_ocnice_diags is set to 0
export generate_ohc_trends=1
export generate_sst_trends=1
export generate_sst_climo=1
export generate_sss_climo=1
export generate_mld_climo=1
export generate_ArgoTemperature_climo=1
export generate_ArgoSalinity_climo=1
export generate_mht=1
export generate_moc=1
export generate_seaice_trends=1
export generate_seaice_climo=1
export generate_nino34=1

# Generate standalone html file to view plots on a browser, if required
export generate_html=1

# Set options to run a-prime in parallel
#   If run_batch_script=false, aprime_atm_diags.bash and aprime_ocnice_diags.bash are called directly.
#   If run_batch_script=true, aprime_atm_diags.bash and aprime_ocnice_diags.bash are called within
#     a machine-specific batch script (one script for atm and one for ocn/ice diags). In this case,
#     both atmosphere and ocn/ice diagnostics are run in background mode onto a single compute node
#     each, using a number of tasks equal to 'mpas_analysis_tasks'. We have determined that
#     mpas_analysis_tasks=12 is a good choice for most systems, and therefore the user should
#     NOT change this setting. Parameters that could be set by the user are instead:
#     -) the walltime (default is 1hr for atm and 1hr for ocn/ice diags)
#     -) whether to run ncclimo in parallel mode. In that case, set ncclimoParallelMode to
#        "bck", and nclimo will launch 12 parallel tasks on a single node to compute 12 monthly
#        climatologies. Otherwise, leave ncclimoParallelMode="serial".
export run_batch_script=false
export batch_walltime="02:00:00" # HH:MM:SS
export ncclimoParallelMode="bck"
if $run_batch_script || [ $machname == "acme1" ] || [ $machname == "aims4" ]; then
  export mpas_analysis_tasks=12
else
  export mpas_analysis_tasks=1
fi
###############################################################################################

########################################################################
# PART II
# OTHER VARIABLES (NOT REQUIRED TO BE CHANGED BY THE USER - DEFAULTS SHOULD
# WORK, USER PREFERENCE BASED CHANGES)

# Choose whether to use MOC postprocessing script instead of reading in
# online computed MOC (do the former for low resolution MPAS meshes that
# use GM to parameterize eddies)
if [ ${test_mpas_mesh_name} == "oEC60to30v3" ]; then
  export useMOCpostprocessing=True
else
  export useMOCpostprocessing=False
fi

# Set paths to scratch, plots and logs directories
export test_scratch_dir=$output_base_dir/coupled_diagnostics/$test_casename.scratch
export ref_scratch_dir=$output_base_dir/coupled_diagnostics/$ref_case.scratch
export plots_base_dir=$output_base_dir/coupled_diagnostics/${test_casename}_vs_${ref_case}
if [ $ref_case == "obs" ]; then
  export plots_dir_name=${test_casename}_years${test_begin_yr_climo}-${test_end_yr_climo}_vs_${ref_case}
else
  export plots_dir_name=${test_casename}_years${test_begin_yr_climo}-${test_end_yr_climo}_vs_${ref_case}_years${ref_begin_yr_climo}-${ref_end_yr_climo}
fi
# User can set a custom name for the $plots_dir_name here, if the default (above) is not ideal 
#export plots_dir_name=XXXX
export plots_dir=$plots_base_dir/$plots_dir_name
export log_dir=$plots_dir.logs

# Set atm specific paths to mapping and data files locations
export remap_files_dir=$projdir/diagnostics/a-prime/maps
export GPCP_regrid_wgt_file=$projdir/diagnostics/a-prime/maps/$test_atm_res-to-GPCP.conservative.wgts.nc
export CERES_EBAF_regrid_wgt_file=$projdir/diagnostics/a-prime/maps/$test_atm_res-to-CERES-EBAF.conservative.wgts.nc
export ERS_regrid_wgt_file=$projdir/diagnostics/a-prime/maps/$test_atm_res-to-ERS.conservative.wgts.nc

# Set ocn/ice specific paths to region mask and mapping files, and to observation files
export mpas_mappingDirectory=$projdir/diagnostics/mpas_analysis/maps
export mpas_regionMaskDirectory=$projdir/diagnostics/mpas_analysis/region_masks
export obs_ocndir=$projdir/diagnostics/observations/Ocean
export obs_seaicedir=$projdir/diagnostics/observations/SeaIce
export obs_sstdir=$obs_ocndir/SST
export obs_sssdir=$obs_ocndir/SSS
export obs_mlddir=$obs_ocndir/MLD
export obs_ninodir=$obs_ocndir/Nino
export obs_mhtdir=$obs_ocndir/MHT
export obs_argodir=$obs_ocndir/ARGO
export obs_iceareaNH=$obs_seaicedir/IceArea_timeseries/iceAreaNH_climo.nc
export obs_iceareaSH=$obs_seaicedir/IceArea_timeseries/iceAreaSH_climo.nc
export obs_icevolNH=$obs_seaicedir/PIOMAS/PIOMASvolume_monthly_climo.nc
export obs_icevolSH=none
##############################################################################

########################################################################
# PART III
# USER SHOULD NOT NEED TO CHANGE ANYTHING HERE ONWARDS

export coupled_diags_home=$PWD
# unique ID to be used to name unique MPAS-Analysis confg files
# and batch scripts
export uniqueID=`date +%Y-%m-%d_%H%M%S`

# Check on www_dir: create it if it does not exist, purge it if it does
if [ ! -d $www_dir/$plots_dir_name ]; then
  mkdir -p $www_dir/$plots_dir_name
else
  rm -f $www_dir/$plots_dir_name/*.png
fi
# Check on MPAS-Analysis www_dir: create it if it does not exist, purge it if it does
export mpas_www_link=./mpas-analysis
export mpas_www_dir=$www_dir/$plots_dir_name/$mpas_www_link
if [ ! -d $mpas_www_dir ]; then
  mkdir -p $mpas_www_dir
else
  rm -rf $mpas_www_dir/*
fi

# LOAD THE MACHINE-SPECIFIC ANACONDA-2.7 ENVIRONMENT
source $MODULESHOME/init/bash  
if [ ${HOSTNAME:0:3} == "nid" ]; then
  module unload python
  module unload python_base
  source /global/project/projectdirs/acme/software/anaconda_envs/edison/base/etc/profile.d/conda.sh
  conda activate e3sm_unified_1.2.3_py2.7_nox
  export NCO_PATH_OVERRIDE=No
elif [ ${HOSTNAME:0:4} == "cori" ]; then
  module unload python
  module unload python_base
  source /global/project/projectdirs/acme/software/anaconda_envs/cori/base/etc/profile.d/conda.sh
  conda activate e3sm_unified_1.2.3_py2.7_nox
  export NCO_PATH_OVERRIDE=No
elif [ ${HOSTNAME:0:4} == "rhea" ] || [ ${HOSTNAME:0:5} == "titan" ]; then
  module unload python
  source /ccs/proj/cli900/sw/rhea/e3sm-unified/base/etc/profile.d/conda.sh
  conda activate e3sm_unified_1.2.3_py2.7_nox
  export NCO_PATH_OVERRIDE=No
elif [ ${HOSTNAME:0:5} == "aims4" ] || [ ${HOSTNAME:0:5} == "acme1" ]; then
  source /usr/local/e3sm_unified/envs/base/etc/profile.d/conda.sh
  conda activate e3sm_unified_1.2.3_py2.7_nox
  export NCO_PATH_OVERRIDE=No
elif [ ${HOSTNAME:0:4} == "wolf" ] || [ ${HOSTNAME:0:7} == "grizzly" ]; then
  module unload python
  source /usr/projects/climate/SHARED_CLIMATE/anaconda_envs/base/etc/profile.d/conda.sh
  conda activate e3sm_unified_1.2.3_py2.7_nox
elif [ ${HOSTNAME:0:6} == "blogin" ] || ([ ${HOSTNAME:0:1} == "b" ] && [[ ${HOSTNAME:1:2} =~ [0-9] ]]); then
  source /lcrc/soft/climate/e3sm-unified/base/etc/profile.d/conda.sh
  conda activate e3sm_unified_1.2.3_py2.7_nox
  unset LD_LIBRARY_PATH
elif [ ${HOSTNAME:0:6} == "cooley" ] || ([ ${HOSTNAME:0:2} == "cc" ] && [[ ${HOSTNAME:2:3} =~ [0-9] ]]); then
  source /lus/theta-fs0/projects/ClimateEnergy_2/software/e3sm_unified/base/etc/profile.d/conda.sh
  conda activate e3sm_unified_1.2.3_py2.7_nox
else
  echo "Running on an unsupported machine. Sourcing users anaconda environment from {{ user_env_path }}"
  source activate {{ user_env_path }}
fi

# The following is needed to avoid the too-many-open-files problem
# in xarray. Since we are mostly using ncrcat in MPAS-Analysis v0.6
# and beyond, this will eventually become outdated (as per v0.6, we
# are still using xarray 'open_mfdataset' to open pre-processed
# model data).
if [ $machname == "aims4" ] || [ $machname == "acme1" ] || [ $machname == "rhea" ]; then
  export mpasAutocloseFileLimitFraction=0.02
else
  export mpasAutocloseFileLimitFraction=0.2 # default value
fi

# Take into account changes in mpas namelist and streams file names
# (Note: this will eventually be removed, but for now, May 2018, we
#  need to remain backward compatible).
if [ -f $test_archive_dir/$test_casename/run/mpaso_in ]; then
  export ocean_namelist_file=mpaso_in
else
  export ocean_namelist_file=mpas-o_in
fi
if [ -f $test_archive_dir/$test_casename/run/mpassi_in ]; then
  export seaIce_namelist_file=mpassi_in
else
  export seaIce_namelist_file=mpas-cice_in
fi
if [ -f $test_archive_dir/$test_casename/run/streams.seaice ]; then
  export seaIce_streams_file=streams.seaice
else
  export seaIce_streams_file=streams.cice
fi

# PUT THE PROVIDED CASE INFORMATION IN CSH ARRAYS TO FACILITATE READING BY OTHER SCRIPTS
./bash_scripts/setup.bash

# RUN DIAGNOSTICS
if [ $generate_atm_diags -eq 1 ]; then
  if ! $run_batch_script; then
    ./bash_scripts/aprime_atm_diags.bash
    atm_status=$?
    if [ $atm_status -eq 0 ]; then
      # Update www/plots directory with newly generated plots
      cp -u $plots_dir/* $www_dir/$plots_dir_name

      echo
      echo "Updated atm plots in website directory: $www_dir/$plots_dir_name"
      echo
    fi
  else
    batch_script="$log_dir/batch_atm.$machname.$uniqueID.bash"
    if [ $machname == "edison" ]; then
      sed 's@SBATCH --time=.*@SBATCH --time='$batch_walltime'@' ./bash_scripts/batch_atm.$machname.bash > $batch_script
      sed -i 's@SBATCH --output=.*@SBATCH --output='$log_dir'/aprime_atm_diags.o'$uniqueID'@' $batch_script
      sed -i 's@SBATCH --error=.*@SBATCH --error='$log_dir'/aprime_atm_diags.e'$uniqueID'@' $batch_script
      echo
      echo "**** Submitting atm batch script: batch_atm.$machname.$uniqueID.bash"
      echo "**** $batch_script"
      echo "**** jobID:"
      sbatch $batch_script
    elif [ $machname == "titan" ] || [ $machname == "anvil" ]; then
      update_wwwdir_script="$log_dir/batch_update_wwwdir.$machname.$uniqueID.bash"
      sed 's@PBS -l walltime=.*@PBS -l walltime='$batch_walltime'@' ./bash_scripts/batch_atm.$machname.bash > $batch_script
      sed -i 's@PBS -o .*@PBS -o '$log_dir'/aprime_atm_diags.o'$uniqueID'@' $batch_script
      sed -i 's@PBS -e .*@PBS -e '$log_dir'/aprime_atm_diags.e'$uniqueID'@' $batch_script
      sed -i 's@batch_script=.*@batch_script='$update_wwwdir_script'@' $batch_script
      sed 's@PBS -o .*@PBS -o '$log_dir'/aprime_update_wwwdir.o'$uniqueID'@' \
       ./bash_scripts/batch_update_wwwdir.$machname.bash > $update_wwwdir_script
      sed -i 's@PBS -e .*@PBS -e '$log_dir'/aprime_update_wwwdir.e'$uniqueID'@' $update_wwwdir_script
      echo
      echo "**** Submitting atm batch script: batch_atm.$machname.$uniqueID.bash"
      echo "**** jobID:"
      qsub $batch_script
    elif [ $machname == "cooley" ]; then
      sed 's@COBALT -t .*@COBALT -t '$batch_walltime'@' ./bash_scripts/batch_atm.$machname.bash > $batch_script
      sed -i 's@COBALT -O .*@COBALT -O '$log_dir'/aprime_atm_diags.o'$uniqueID'@' $batch_script
      echo
      echo "**** Submitting atm batch script: batch_atm.$machname.$uniqueID.bash"
      echo "**** jobID:"
      unset LD_PRELOAD
      declare -xp > $log_dir/env4cooley
      chmod +x $log_dir/env4cooley $batch_script
      qsub --env log_dir=$log_dir $batch_script sargs
    else
      echo
      echo "Batch jobs not supported on current machine"
      echo "Please set 'run_batch_script' to false"
      echo
      exit
    fi
    echo "**** Batch job output/error files aprime_atm_diags.o*/aprime_atm_diags.e* will be available in log directory:"
    echo "**** $log_dir"
    atm_status=-2
  fi
else
  atm_status=-1
fi

if [ $generate_ocnice_diags -eq 1 ]; then
  if ! $run_batch_script; then
    ./bash_scripts/aprime_ocnice_diags.bash
    ocnice_status=$?
    if [ $ocnice_status -eq 0 ]; then
      # Update www/plots directory with newly generated plots
      cp -u $plots_dir/* $www_dir/$plots_dir_name

      echo
      echo "Updated ocn/ice plots in website directory: $www_dir/$plots_dir_name"
      echo
    fi
  else
    batch_script="$log_dir/batch_ocnice.$machname.$uniqueID.bash"
    if [ $machname == "edison" ]; then
      sed 's@SBATCH --time=.*@SBATCH --time='$batch_walltime'@' ./bash_scripts/batch_ocnice.$machname.bash > $batch_script
      sed -i 's@SBATCH --output=.*@SBATCH --output='$log_dir'/aprime_ocnice_diags.o'$uniqueID'@' $batch_script
      sed -i 's@SBATCH --error=.*@SBATCH --error='$log_dir'/aprime_ocnice_diags.e'$uniqueID'@' $batch_script
      echo
      echo "**** Submitting ocn/ice batch script: batch_ocnice.$machname.$uniqueID.bash"
      echo "**** jobID:"
      sbatch $batch_script
    elif [ $machname == "titan" ] || [ $machname == "anvil" ]; then
      update_wwwdir_script="$log_dir/batch_update_wwwdir.$machname.$uniqueID.bash"
      sed 's@PBS -l walltime=.*@PBS -l walltime='$batch_walltime'@' ./bash_scripts/batch_ocnice.$machname.bash > $batch_script
      sed -i 's@PBS -o .*@PBS -o '$log_dir'/aprime_ocnice_diags.o'$uniqueID'@' $batch_script
      sed -i 's@PBS -e .*@PBS -e '$log_dir'/aprime_ocnice_diags.e'$uniqueID'@' $batch_script
      sed -i 's@batch_script=.*@batch_script='$update_wwwdir_script'@' $batch_script
      sed 's@PBS -o .*@PBS -o '$log_dir'/aprime_update_wwwdir.o'$uniqueID'@' \
       ./bash_scripts/batch_update_wwwdir.$machname.bash > $update_wwwdir_script
      sed -i 's@PBS -e .*@PBS -e '$log_dir'/aprime_update_wwwdir.e'$uniqueID'@' $update_wwwdir_script
      echo
      echo "**** Submitting ocn/ice batch script: batch_ocnice.$machname.$uniqueID.bash"
      echo "**** jobID:"
      qsub $batch_script
    elif [ $machname == "cooley" ]; then
      sed 's@COBALT -t .*@COBALT -t '$batch_walltime'@' ./bash_scripts/batch_ocnice.$machname.bash > $batch_script
      sed -i 's@COBALT -O .*@COBALT -O '$log_dir'/aprime_ocnice_diags.o'$uniqueID'@' $batch_script
      echo
      echo "**** Submitting ocn/ice batch script: batch_ocnice.$machname.$uniqueID.bash"
      echo "**** jobID:"
      unset LD_PRELOAD
      declare -xp > $log_dir/env4cooley
      chmod +x $log_dir/env4cooley $batch_script
      qsub --env log_dir=$log_dir $batch_script sargs
    else
      echo
      echo "Batch jobs not supported on current machine"
      echo "Please set 'run_batch_script' to false"
      echo
      exit
    fi
    echo "**** Batch job output/error files aprime_ocnice_diags.o*/aprime_ocnice_diags.e* will be available in log directory:"
    echo "**** $log_dir"
    ocnice_status=-2
  fi
else
  ocnice_status=-1
fi

echo
echo "Status of atmospheric diagnostics: $atm_status"
echo " (0-->success, -1-->diags not invoked, -2-->batch_script, 3-->init error)"
echo "Status of ocean/ice diagnostics: $ocnice_status"
echo " (0-->success, -1-->diags not invoked, -2-->batch_script, 3-->init error)"
echo
echo "All log files, batch scripts, MPAS-Analysis config files available in log directory:"
echo $log_dir
echo "All climo and remapping files for this a-prime run available in scratch directory:"
echo $test_scratch_dir

# GENERATE HTML PAGE IF ASKED
if [ $atm_status -eq 0 ]    || [ $atm_status -eq -2 ]   ||
   [ $ocnice_status -eq 0 ] || [ $ocnice_status -eq -2 ]; then
  source $log_dir/case_info.temp
  {% raw %}
  
  n_cases=${#case_set[@]} #}
  n_test_cases=$((n_cases - 1))
  
  {% endraw %}
  for j in `seq 1 $n_test_cases`; do
     if [ $generate_html -eq 1 ]; then
	./bash_scripts/generate_html_index_file.bash	$j \
							$plots_dir
     fi
  done
  chmod ga+rX $www_dir
  chmod -R ga+rX $www_dir/$plots_dir_name
else
  echo
  echo "Neither atmospheric nor ocn/ice diagnostics were generated. HTML page also not generated!"
  echo
fi

# COPY THIS RUN SCRIPT TO THE $log_dir FOR PROVENANCE
cp $0 $log_dir/run_aprime_$uniqueID.bash
