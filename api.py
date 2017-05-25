# -*- coding: utf-8 -*-
import sys
import ast
import pandas as pd
from flask import Flask, jsonify, request
from flasgger import Swagger
from flasgger.utils import swag_from
from string import capwords

from resources import constants
from utils import api_utils, data_utils


SWAGGER_CONFIG = {
    "headers": [
    ],
    "specs": [
        {
            "version": "0.1",
            "title": "Humanitarian Data Service",
            "description": "Consolidating fragmented raw sources of humanitarian data and serving up parsed and "
                           "cleaned data from a single API (financials in USD)",
            "endpoint": 'spec',
            "route": '/spec',
            "rule_filter": lambda rule: True  # all in
        }
    ],
    "static_url_path": "/apidocs",
    "static_folder": "swaggerui",
    "specs_route": "/specs"
}


app = Flask(__name__)
api = Swagger(app, config=SWAGGER_CONFIG)


@app.route('/')
def hello():
    # Background colors: https://uigradients.com/#GrapefruitSunset
    landing_page = """
      <!DOCTYPE html>
      <html>
      <head>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
        <style type="text/css">
        body {
            padding: 50px 200px;
            font-family: "Georgia";
            color: #EEEEEE;
            text-align: center;
            background: linear-gradient(to left, #E96443 , #904E95);
        }
        </style>
      </head>
      <body>
        <h1> Welcome to the Humanitarian Data Service</h1>
        <i class="fa fa-globe" style="font-size:48px;"></i>
        <p>See the interactive API docs <a href="/apidocs/index.html" style="color: #EEEEEE">here</a> </p>
        <p>See the open source repository <a href="https://github.com/onecampaign/humanitarian-data-service" style="color: #EEEEEE">here</a></p>
        <p>See a concept dashboard <a href="/dashboard" style="color: #EEEEEE">here</a></p>
      </body>
      </html>
    """
    return landing_page


@app.route('/dashboard')
def dashboard():
    landing_page = """
      <!DOCTYPE html>
      <html>
      <head>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
        <style type="text/css">
        body {
            padding: 50px 200px;
            font-family: "Georgia";
            color: #EEEEEE;
            text-align: center;
            background: linear-gradient(to left, #AA076B, #61045F);
        }
        </style>
      </head>
      <body>
        <h1> Concept Dashboard</h1>
        <i class="fa fa-bar-chart fa-lg"></i>
        <p>This is a sample dashboard built with Plotly. Some graphs here documents the refugee and asylum-seeking crisis in Kenya with a focus around the Dadaab region, host to the world's largest refugee camp. The Kenyan government plans to shut down refugee camps in Dadaab by mid-2017, which hosts around 250,000 Somalian refugees driven from drought-induced famine and Al-Shabaab terrorism.</p>
        <p>Go back to the main page <a href="/" style="color: #EEEEEE">here</a></p>
        <p></p>
        <iframe width="900" height="500" frameborder="0" scrolling="no" src="https://plot.ly/~shoshininsights/19.embed?logo=false"></iframe>
        <iframe width="900" height="800" frameborder="0" scrolling="no" src="https://plot.ly/~shoshininsights/13.embed?logo=false"></iframe>
        <iframe width="900" height="800" frameborder="0" scrolling="no" src="https://plot.ly/~shoshininsights/20.embed?logo=false"></iframe>
        <iframe width="900" height="800" frameborder="0" scrolling="no" src="https://plot.ly/~shoshininsights/22.embed?logo=false"></iframe>
        <iframe width="900" height="800" frameborder="0" scrolling="no" src="https://plot.ly/~shoshininsights/24.embed?logo=false"></iframe>
      </body>
      </html>
    """
    return landing_page


@app.route('/funding/totals/<string:country>/', methods=['GET'])
@swag_from('api_configs/lake_chad_basin/funding_totals_by_country.yml')
def get_funding_totals(country):
    country = country.strip().capitalize()
    success, result, metadata = api_utils.safely_load_data('hno_funding_2016_2017.csv', 'funding', country, has_metadata=True)
    if not success:
        return result, 501
    result = result.iloc[0].to_dict()
    contact = api_utils.load_metadata('/funding/totals/:country', 'contact', literal=True)
    metadata['contact'] = contact
    return jsonify(metadata=metadata, data=result, params={"country": country})


@app.route('/funding/categories/<string:country>/', methods=['GET'])
@swag_from('api_configs/lake_chad_basin/funding_categories_by_country.yml')
def get_funding_categories(country):
    country = country.strip().capitalize()
    hno_funding_file = 'hno_funding_%s_2017.csv' % country.lower()
    success, result, metadata = api_utils.safely_load_data(hno_funding_file, 'category funding', has_metadata=True)
    if not success:
        return result, 501
    result = result.to_dict(orient='list')
    contact = api_utils.load_metadata('/funding/categories/:country', 'contact', literal=True)
    metadata['contact'] = contact
    return jsonify(metadata=metadata, data=result, params={"country": country})


def get_funding_by_fts_dimension(country, fts_dimension):
    """
    Helper function for FTS funding endpoints.
    Returns whether data retrieval was successful (or http errorcode if not), and the resulting json data (or error message if not).
    """
    country = country.strip().capitalize()
    fts_donors_file = 'fts-{}.csv'.format(fts_dimension)
    success, result, metadata = api_utils.safely_load_data(fts_donors_file, '{} funding'.format(fts_dimension), country, has_metadata=True)
    if not success:
        return 501, result
    result.drop(constants.COUNTRY_COL, axis=1, inplace=True)
    contact = api_utils.load_metadata('/funding/{}/:country'.format(fts_dimension), 'contact', literal=True)
    metadata['contact'] = contact
    return success, result.to_dict(orient='list'), metadata


@app.route('/funding/donors/<string:country>/', methods=['GET'])
@swag_from('api_configs/lake_chad_basin/funding_donors_by_country.yml')
def get_funding_donors(country):
    country = country.strip().capitalize()
    success, result, metadata = get_funding_by_fts_dimension(country, 'donors')
    if not success or success == 501:
        return result, 501
    return jsonify(metadata=metadata, data=result, params={"country": country})


@app.route('/funding/clusters/<string:country>/', methods=['GET'])
@swag_from('api_configs/lake_chad_basin/funding_clusters_by_country.yml')
def get_funding_clusters(country):
    country = country.strip().capitalize()
    success, result, metadata = get_funding_by_fts_dimension(country, 'clusters')
    if not success or success == 501:
        return result, 501
    return jsonify(metadata=metadata, data=result, params={"country": country})


@app.route('/funding/recipients/<string:country>/', methods=['GET'])
@swag_from('api_configs/lake_chad_basin/funding_recipients_by_country.yml')
def get_funding_recipients(country):
    country = country.strip().capitalize()
    success, result, metadata = get_funding_by_fts_dimension(country, 'recipients')
    if not success or success == 501:
        return result, 501
    return jsonify(metadata=metadata, data=result, params={"country": country})


@app.route('/needs/totals/<string:country>/', methods=['GET'])
@swag_from('api_configs/lake_chad_basin/needs_totals_by_country.yml')
def get_needs_totals(country):
    data_keys = ['HNO']
    country = country.strip().capitalize()

    success, result, hno_metadata = api_utils.safely_load_data('hno_needs_total_2017.csv', 'HNO needs', country, has_metadata=True)
    if not success:
        return result, 501
    result = result.iloc[0]
    result = result.to_dict()
    result['Additional Data'] = ast.literal_eval(result['Additional Data'])

    success, dtm, dtm_metadata = api_utils.safely_load_data('iom_dtm14_needs_feb2017.csv', 'IOM DTM needs', country, has_metadata=True)
    if success:
        dtm = dtm.iloc[0].to_dict()
        dtm['Percent Main Unmet Need'] = ast.literal_eval(dtm['Percent Main Unmet Need'])
        dtm['Percent Main Cause Of Displacement'] = ast.literal_eval(dtm['Percent Main Cause Of Displacement'])
        dtm['Regional Summary'] = ast.literal_eval(dtm['Regional Summary'])
        result['Additional Data'].update(dtm)
        data_keys.append('DTM')

    sources = [constants.DATA_SOURCES[data_key] for data_key in data_keys]
    metadata = {"HNO": hno_metadata, "DTM": dtm_metadata, "Merge Notes": "DTM data appended to HNO data under 'Additional Data'"}
    contact = api_utils.load_metadata('/needs/totals/:country', 'contact', literal=True)
    metadata['contact'] = contact
    return jsonify(metadata=metadata, data=result, params={"country": country})


@app.route('/needs/regions/<string:country>/', methods=['GET'])
@swag_from('api_configs/lake_chad_basin/needs_regions_by_country.yml')
def get_needs_regions(country):
    country = country.strip().capitalize()
    success, result, metadata = api_utils.safely_load_data('lcb_displaced_2017.csv', 'regional needs', country, has_metadata=True)
    if not success:
        return result, 501
    result['PeriodDate'] = pd.to_datetime(result['Period'])
    result.sort_values(by=['ReportedLocation', 'PeriodDate'], inplace=True)
    dates = result['Period'].unique().tolist()
    regions = result['ReportedLocation'].unique().tolist()
    displacement_types = result['DisplType'].unique().tolist()
    # Construct a dict for region name -> displacement type -> list of totals where index corresponds to dates list
    values = {}
    region_groups = result.groupby('ReportedLocation')
    for region, group in region_groups:
        group_df = pd.DataFrame(group).reset_index()
        idp = group_df[group_df.DisplType == 'idp']['TotalTotal'].tolist()
        refugee = group_df[group_df.DisplType == 'refugee']['TotalTotal'].tolist()
        values[region] = {'IDP': idp, 'Refugee': refugee}
    data = {}
    data['dates'] = dates
    data['values'] = values
    contact = api_utils.load_metadata('/needs/regions/:country', 'contact', literal=True)
    metadata['contact'] = contact
    return jsonify(metadata=metadata, data=data, params={"country": country})


def get_needs_assessment_by_type(country='Nigeria', state='Borno', dtm_assessment_type='baseline'):
    """
    Helper function for DTM needs assessment endpoints.
    Returns whether data retrieval was successful (or http errorcode if not), and the resulting json data (or error message if not).
    """
    country = country.strip().capitalize()
    if country != 'Nigeria':
        return 501, 'This country [{}] is currently not supported for site assessment data'.format(country)
    dtm_file = constants.DTM_FILE_NAMES[dtm_assessment_type]
    state_col = constants.DTM_STATE_COLS[dtm_assessment_type]
    success, result, metadata = api_utils.safely_load_data(dtm_file, 'site assessment needs', state.upper(), state_col, has_metadata=True)
    if not success:
        return 501, result
    result.drop(state_col, axis=1, inplace=True)
    result = result.to_dict(orient='list')
    contact = api_utils.load_metadata('/needs/assessment/{}/:country'.format(dtm_assessment_type), 'contact', literal=True)
    metadata['contact'] = contact
    return success, result, metadata


@app.route('/needs/assessment/site/<string:country>/', methods=['GET'])
@swag_from('api_configs/lake_chad_basin/needs_assessment_site_by_state.yml')
def get_needs_assessment_site(country):
    # Note: this endpoint is only available for Nigeria for now, and assumes states in Nigeria
    country = country.strip().capitalize()
    dtm_assessment_type = 'site'
    state = str(request.args.get('state', 'Borno')).strip().capitalize()
    success, result, metadata = get_needs_assessment_by_type(country, state, dtm_assessment_type)
    if not success or success == 501:
        return result, 501
    return jsonify(metadata=metadata, data=result, params={"country": country, "state": state})


@app.route('/needs/assessment/location/<string:country>/', methods=['GET'])
@swag_from('api_configs/lake_chad_basin/needs_assessment_location_by_state.yml')
def get_needs_assessment_location(country):
    # Note: this endpoint is only available for Nigeria for now, and assumes states in Nigeria
    country = country.strip().capitalize()
    dtm_assessment_type = 'location'
    state = str(request.args.get('state', 'Borno')).strip().capitalize()
    success, result, metadata = get_needs_assessment_by_type(country, state, dtm_assessment_type)
    if not success or success == 501:
        return result, 501
    return jsonify(metadata=metadata, data=result, params={"country": country, "state": state})


@app.route('/needs/assessment/baseline/<string:country>/', methods=['GET'])
@swag_from('api_configs/lake_chad_basin/needs_assessment_baseline_by_state.yml')
def get_needs_assessment_baseline(country):
    # Note: this endpoint is only available for Nigeria for now, and assumes states in Nigeria
    country = country.strip().capitalize()
    dtm_assessment_type = 'baseline'
    state = str(request.args.get('state', 'Borno')).strip().capitalize()
    success, result, metadata = get_needs_assessment_by_type(country, state, dtm_assessment_type)
    if not success or success == 501:
        return result, 501
    return jsonify(metadata=metadata, data=result, params={"country": country, "state": state})


@app.route('/indicators/gni/<string:orientation>', methods=['GET'])
@swag_from('api_configs/world/indicators_gni.yml')
def get_indicators_gni(orientation):
    params = None
    success, result, metadata = api_utils.safely_load_data('gni_per_capita.csv', 'GNI PPP indicator', has_metadata=True)
    if not success:
        return result, 501
    country = request.args.get('country', None)
    country_code = request.args.get('country_code', None)
    if country_code:
        params = {"country_code": country_code}
        country_code = capwords(str(country_code).strip())
        result = data_utils.fuzzy_filter(result, 'Country Code', country_code)
    elif country:
        params = {"country": country}
        country = str(country).strip().capitalize()
        result = data_utils.fuzzy_filter(result, 'Country Name', country)
    result = result[['Country Name', 'Country Code', '2011', '2012', '2013', '2014', '2015']]  # No data after 2015
    if orientation == 'index':
        result = result.set_index('Country Code')
    result = result.to_dict(orient=orientation)
    return jsonify(metadata=metadata, data=result)


@app.route('/populations/refugeelike/asylum/<string:orientation>', methods=['GET'])
@swag_from('api_configs/world/populations_refugeelike_asylum.yml')
def get_populations_refugeelike_asylum(orientation):
    params = None
    data_path = constants.UNHCR_FILE_NAMES['asylum_country']
    success, result, metadata = api_utils.safely_load_data(data_path, 'UNHCR refugee-like populations by asylum country', has_metadata=True)
    if not success:
        return result, 501
    country = request.args.get('country', None)
    if country:
        params = {"country": country}
        country = str(country).strip().capitalize()
        result = data_utils.fuzzy_filter(result, constants.COUNTRY_COL, country)
    if orientation == 'index':
        result = result.set_index('countryCode')
    result = result.to_dict(orient=orientation)
    contact = api_utils.load_metadata('/populations/refugeelike/asylum', 'contact', literal=True)
    metadata['contact'] = contact
    return jsonify(metadata=metadata, data=result, params=params)


@app.route('/populations/refugeelike/origin/<string:orientation>', methods=['GET'])
@swag_from('api_configs/world/populations_refugeelike_origin.yml')
def get_populations_refugeelike_origin(orientation):
    params = None
    data_path = constants.UNHCR_FILE_NAMES['origin_country']
    success, result, metadata = api_utils.safely_load_data(data_path, 'UNHCR refugee-like populations by origin country', has_metadata=True)
    if not success:
        return result, 501
    country = request.args.get('country', None)
    if country:
        params = {"country": country}
        country = str(country).strip().capitalize()
        result = data_utils.fuzzy_filter(result, constants.COUNTRY_COL, country)
    if orientation == 'index':
        result = result.set_index('countryCode')
    result = result.to_dict(orient=orientation)
    contact = api_utils.load_metadata('/populations/refugeelike/origin', 'contact', literal=True)
    metadata['contact'] = contact
    return jsonify(metadata=metadata, data=result, params=params)


@app.route('/populations/totals/<string:orientation>', methods=['GET'])
@swag_from('api_configs/world/populations_totals.yml')
def get_populations_totals(orientation):
    params = None
    data_path = constants.ESA_FILE_NAMES['wpp_overall']
    success, result, metadata = api_utils.safely_load_data(data_path, 'UN ESA WPP world populations', has_metadata=True)
    if not success:
        return result, 501
    result = result[result['Year'] > 2014]  # The latest official statistics are from 2015, followed by projections into 2017
    country = request.args.get('country', None)
    if country:
        params = {"country": country}
        country = str(country).strip().capitalize()
        result = data_utils.fuzzy_filter(result, constants.COUNTRY_COL, country)
    if orientation == 'index':
        result = result.set_index('Country')
    result = result.to_dict(orient=orientation)
    contact = api_utils.load_metadata('/populations/totals', 'contact', literal=True)
    metadata['contact'] = contact
    return jsonify(metadata=metadata, data=result, params=params)


@app.route('/funding/plans/progress/<string:orientation>', methods=['GET'])
@swag_from('api_configs/world/funding_progress.yml')
def get_funding_progress(orientation):
    params = None
    success, result, metadata = api_utils.safely_load_data('funding_progress.csv', 'FTS funding progress by country appeal', has_metadata=False)
    if not success:
        return result, 501
    countryCode = request.args.get('countryCode', None)
    if countryCode:
        params = {"countryCode": countryCode}
        countryCode = str(countryCode).strip().upper()
        result = result[result.countryCode == countryCode]
    if orientation == 'index':
        result = result.set_index('countryCode')
    result = result.to_dict(orient=orientation)
    return jsonify(data=result, params=params)


@app.route('/funding/plans/donors', methods=['GET'])
@swag_from('api_configs/world/funding_donors.yml')
def get_funding_plan_donors():
    params = None
    success, result, metadata = api_utils.safely_load_data('funding_donors.csv', 'FTS funding donors to each appeal', has_metadata=False)
    if not success:
        return result, 501
    planID = request.args.get('planID', None)
    if planID:
        params = {"planID": planID}
        planID = int(planID)
        result = result[result.plan_id == planID]
    result = result.to_dict(orient='list')
    return jsonify(data=result, params=params)


@app.route('/events/acled', methods=['GET'])
@swag_from('api_configs/world/events_acled.yml')
def get_events_acled():
    success, result, metadata = api_utils.safely_load_data('acled.csv', 'ACLED events', has_metadata=False)
    if not success:
        return result, 501
    return jsonify(data=result.to_dict(orient='list'))


@app.route('/events/acled-africa', methods=['GET'])
@swag_from('api_configs/world/events_acled_africa.yml')
def get_events_acled_africa():
    success, result, metadata = api_utils.safely_load_data('acled_all_africa.csv', 'ACLED Africa events', has_metadata=False)
    if not success:
        return result, 501
    return jsonify(data=result.to_dict(orient='list'))


@app.route('/metadata/all/<string:orientation>', methods=['GET'])
@swag_from('api_configs/metadata/all.yml')
def get_metadata_all(orientation):
    metadata = api_utils.format_metadata(orientation)
    return jsonify(metadata=metadata)


def main():
    env_type = 'local'
    if len(sys.argv) == 2:
        env_type = sys.argv[1]
    if env_type == 'remote':
        app.run(debug=False, port=80, host='0.0.0.0')
    else:
        app.run(debug=True)


if __name__ == '__main__':
    main()

