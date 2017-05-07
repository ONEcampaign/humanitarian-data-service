# Humanitarian Data Service
An interactively documented REST API serving data about the refugee crisis from a variety of sources.
The aspirational goal is to consolidate the various fragmented raw data sources, whether it be APIs, libraries, raw urls, or PDFs, behind a single REST API and exposed via Swagger UI.
This is the initial effort to lay the groundwork for this to be possible.
Also see the [Humanitarian Data Report](https://docs.google.com/document/d/1ycCChgZPXP7u-QLzN1I3ShOYaEZrCgQtRuDWVa1ezuY/edit#heading=h.5p00tomd6q5c) that was a result of this effort along with conversations and independent research.

# Local Setup
Not needed for remote server, since it's already set up in the AMI for this instance.
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

# Raw data sources and data scripts
To pull data from HDX (the Humanitarian Data Exchange), run the following:
```sh
python3 run_hdx.py
```
This data script can be configured to run every Monday at 2:30am (system time) for the latest data, see `data_update_cron` for reference.

Other examples of data scripts are of the form `run_*.py` and use Python 2.

# Derived data sources
See `resources/data/derived` - this cleaned and formatted data with metadata is what the API is ultimately serving.

# Dev notes
- Gunicorn logs: `/var/log/gunicorn/*.log`
- logrotate: `/etc/logrotate.conf`, gunicorn logs configured to start a new file weekly, compress old files, and keep 4 weeks of history
