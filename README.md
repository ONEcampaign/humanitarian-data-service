# Humanitarian Data Service
An interactively documented REST API serving data about the refugee crisis from a variety of sources.
The aspirational goal is to consolidate the various fragmented raw data sources, whether it be APIs, libraries, raw urls, or PDFs, behind a single REST API and exposed via Swagger UI.
This is the initial effort to lay the groundwork for this to be possible. For additional technical notes, see the "Humanitarian Data Service: Technical Handoff" document.
Also see the [Humanitarian Data Report](https://docs.google.com/document/d/1ycCChgZPXP7u-QLzN1I3ShOYaEZrCgQtRuDWVa1ezuY/edit#heading=h.5p00tomd6q5c) that was a result of this effort along with conversations and independent research.

# Local Setup
No dependency setup needed for the remote server, since it's already set up in the AMI for this instance.
Hence these are just the setup instructions for your local computer.
## Virtualenv
```sh
pip install virtualenv
virtualenv humdata-service
source humdata-service/bin/activate  # run `deactivate` when done
```
## Install dependencies
```sh
python -r requirements.txt
```
## Secrets
For sensitive information like passwords and keys, please make a local copy of `resources/secrets_template.py` called `resources/secrets.py`.
This local `secrets.py` file under `resources/` is where you can fill in the sensitive values.
This file will be automatically loaded into `resources/constants.py` but will not be tracked as part of git (as configured in `.gitignore`).
This has already been set up on the remote machine as well, so there's nothing to do there.
Currently, this is just used to access the UNOCHA FTS API via the `run_fts.py` script.

# Run 
## Local
```sh
python api.py
```
## Remote
This should happen automatically via `/etc/init/gunicorn.conf` (copied in this repo as `gunicorn.conf`). 
However, if you would like to manually restart:
```sh
sudo start gunicorn
```

# Swagger UI
See the local [site](http://127.0.0.1:5000) with interactive API documentation [here](http://127.0.0.1:5000/apidocs/index.html). 
YAML configurations to generate the interactive UI for each endpoint in the API are in `api_configs`.

# Raw data sources and data scripts
To pull data from HDX (the Humanitarian Data Exchange), run the following:
```sh
python3 run_hdx.py
```
This data script can be configured to run every Monday at 2:30am (system time) for the latest data, see `data_update_cron` for reference.
If you would like this script to download additional Datasets, just add/modify the HDX_DATASETS list of dataset names in `resources/constants.py`.

Other examples of data scripts are of the form `run_*.py` and use Python 2 (e.g. `run_fts.py`).

# Derived data sources
See `resources/data/derived/example` - this directory of cleaned and formatted csv data with metadata is what the API is ultimately serving.

# Dev notes
- Gunicorn logs: `/var/log/gunicorn/*.log`
- logrotate: `/etc/logrotate.conf`, gunicorn logs configured to start a new file weekly, compress old files, and keep 4 weeks of history
- See the Technical Handoff document for more details
