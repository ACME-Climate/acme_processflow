# E3SM Automated Workflow

The processflow performs post processing and diagnostics jobs automatically, removing many of the difficulties of performing 
post-run analysis on model data. 

[Documentation can be found here](https://e3sm-project.github.io/processflow/docs/html/index.html)

## Installation<a name="installation"></a>

Latest stable build from the master branch:
```
conda create --name <YOUR_NEW_ENVIRONMENT> -c e3sm -c conda-forge -c cdat processflow
```

Latest (potentially unstable but with the latest bug fixes) build from the nightly branch:
```
conda create --name <YOUR_NEW_ENVIRONMENT> -c conda-forge -c e3sm/label/nightly -c e3sm -c cdat -c pcmdi processflow
```

Update your environment to the newest version
```
conda update -c e3sm -c conda-forge -c cdat processflow
```


# Usage<a name="usage"></a>

        usage: processflow.py [-h] [-c CONFIG] [-v] [-l LOG] [-s] [-f]
                      [-r RESOURCE_PATH] [-a] [-d] [--dryrun] [-m MAX_JOBS]

        optional arguments:
        -h, --help            show this help message and exit
        -c CONFIG, --config CONFIG
                                Path to configuration file.
        -v, --version         Print version informat and exit.
        -l LOG, --log LOG     Path to logging output file.
        -r RESOURCE_PATH, --resource-path RESOURCE_PATH
                                Path to custom resource directory
        -a, --always-copy     Always copy diagnostic output, even if the output
                                already exists in the host directory. This is much
                                slower but ensures old output will be overwritten
        -d, --debug           Set log level to debug
        --dryrun              Do everything up to starting the jobs, but dont start
                                any jobs
        -m MAX_JOBS, --max-jobs MAX_JOBS
                                maximum number of running jobs
