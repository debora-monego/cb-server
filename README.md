# Colbuilder2 Webserver
![](static/images/pyd_crosslink_logo.png)

## Installation of all dependencies (to run locally)
1. Create environment with `conda env create -f environment.yaml`
    - If conda does not read the `KEY_MODELLER` variable while installing **modeller**, update the key manually in `~/<conda_path>/envs/colbuilder_server/lib/modeller-10.5/modlib/modeller/config.py` manually for `MODELIRANJE`
    - If installation of **muscle** fails, install it manually with `conda install -c bioconda muscle`
2. Clone [colbuilder](https://github.com/graeter-group/colbuilder) repo separately from this repo and install it as a package with `pip install .` **IMPORTANT** do not try to install the dependencies from the colbuilder repo! Everything has been already installed in the step 1.
3. Install chimera as described in the colbuilder repo

## Running the server locally

This branch is an implementation of the server via task queuing package [*celery*](https://docs.celeryq.dev/en/stable/getting-started/introduction.html). Every job submitted by a user will be executed as a background task. Celery allows to monitor or to "listen" to the job, which is used for dynamic job status update, for instance. 

To run the server, do the **following**:

1. Open two terminals 
2. In both activate the environment with `conda activate server_env`
3. In one start the celery application by typing `celery -A app.celery worker --loglevel=info`
4. In the second terminal run the server `flask run`
5. In the browser of your choise (benchmarked with Chrome) type in the development https

## Known problems:
- ~~Form selection bugs (should be properly benchmarked)~~
- Download link not properly generated after the job has finished. Second time the user wants to download the results it works

## To implement: 
- [ ] gmx topology -> not implemented at all at the moment
- [ ] Remove abspath from the job submission -> can be seen in .yaml config
- [ ] ~~All arguments in colbuilder execution script on job_submit page~~
- [ ] flask.migrate to update the existing DB
- [ ] ~~Celery background application~~
- [ ] Mix ratio in job_submission page: change formatting
- [ ] ~~.tar re-implement generation~~
- [ ] ~~Pooling job status fix bugs~~
- [ ] Implement daily server restart (?)
- [ ] Number of submissions per user within 30 mins?
- [ ] ~~Exceptions in colbuilder_task~~
- [ ] ~~Upd environment to install dependenices~~
- [ ] ~~Clear implementation of form; now messy~~
- [ ] ~~Documentation and clean up~~
- [ ] ~~Env installation logics is bad -> make a colbuilder branch simply which co-installs dependencies for the server~~
- [ ] Disallowed countries (?)

## For the paper submission:
- [ ] https link
- [ ] working examples -> default fasta / pdb? 
- [ ] anononymized github repo with the stable release?
