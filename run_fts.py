import os.path
import pandas as pd
from datetime import date
from distutils import dir_util

import requests
from pandas.io.json import json_normalize

from resources import constants
from utils import data_utils, api_utils
import time
import json

"""
This script currently updates the committed and paid funding for appeals, and replaces the old `funding_progress.csv` file.
Scheduling this script to run on a nightly or weekly basis is sufficient to automatically update the /world/funding_progress endpoint.

Functions to query raw funding data from the UNOCHA FTS API, perform transformations, and save the data.
See API docs here: https://fts.unocha.org/sites/default/files/publicftsapidocumentation.pdf
"""


def getPlans(year, country_mapping):
    # Get all plans from the FTS API
    data = api_utils.get_fts_endpoint('/public/plan/year/{}'.format(year))

    def extract_adminLevel0(dict):
        iso3 = None
        for x in dict:
            if x['adminLevel'] == 0:
                iso3 = x['iso3']
        return iso3

    # Extract names from objects
    data['categoryName'] = data.categories.apply(lambda x: x[0]['name'])
    data['emergencies'] = data.emergencies.apply(lambda x: x[0]['name'] if x else None)
    data['countryCode'] = data.locations.apply(extract_adminLevel0)

    # Merge in country codes based on country Name
    #data = data.merge(country_mapping, how='left', on=['name'])

    #Tidy the dataset
    data.drop(['origRequirements', 'startDate', 'endDate', 'years', 'categories', 'emergencies', 'locations'], axis=1, inplace=True)
    data = data.where((pd.notnull(data)), None).sort_values('name')

    return data


def getCountries():
    # Get all plans from the FTS API
    data = api_utils.get_fts_endpoint('/public/location')

    return data


def updateCommittedAndPaidFunding(year=constants.FTS_APPEAL_YEAR):
    data = pd.read_csv('resources/data/derived/example/funding_progress.csv', encoding='utf-8')

    # Get committed and paid funding from the FTS API
    def pull_committed_funding_for_plan(plan_id):
        plan_funds = api_utils.get_fts_endpoint('/public/fts/flow?planId={}'.format(plan_id), 'flows')
        funded = plan_funds[(plan_funds.boundary == 'incoming') & (plan_funds.status != 'pledge')]
        return funded['amountUSD'].sum()

    data['appealFunded'] = data['id'].apply(pull_committed_funding_for_plan)
    data['percentFunded'] = data.appealFunded / data.revisedRequirements

    return data


def getInitialRequiredAndCommittedFunding(data):

    # Get committed and paid funding from the FTS API
    def pull_committed_funding_for_plan(plan_id):
        plan_funds = api_utils.get_fts_endpoint('/public/fts/flow?planId={}'.format(plan_id), 'incoming')
        funded = plan_funds['fundingTotal']
        return funded

    data['appealFunded'] = data['id'].apply(pull_committed_funding_for_plan)
    
    # Calculate percent funded
    data['percentFunded'] = data.appealFunded / data.revisedRequirements

    data['neededFunding'] = data.revisedRequirements - data.appealFunded

    return data


def getDonorPlanFundingAmounts(plans):
    """
    For each plan, pull the amount funded by each donor.
    Since the path to the right data in the json is very long, I couldn't sort out how to keep the path in a variable.

    """
    # TODO: make a helper function like api_utils.get_fts_endpoint() that can take a very long key chain
    # TODO: make column indexes of final output a constant
    # TODO: add metadata! With update date.
    def getFundingByDonorOrg(plan_id):
        url = None
        endpoint_str = '/public/fts/flow?planId={}&groupby=Organization'.format(plan_id)
        url = constants.FTS_API_BASE_URL + endpoint_str
        result = requests.get(url, auth=(constants.FTS_CLIENT_ID, constants.FTS_CLIENT_PASSWORD))
        result.raise_for_status()
        if len(result.json()['data']['report1']['fundingTotals']['objects']) > 0:
            result = json_normalize(result.json()['data']['report1']['fundingTotals']['objects'][0]['singleFundingObjects'])
            result['plan_id'] = plan_id
        else:
            print 'Empty data from this endpoint: {}'.format(url)
            result = None
        return result

    plan_ids = plans['id']

    data = pd.DataFrame([])

    #loop through each plan and append the donor data for it to a combined data set
    for plan in plan_ids:
        funding = getFundingByDonorOrg(plan)
        data = data.append(funding)

    data = data.merge(plans, how='left', left_on='plan_id', right_on='id')
    data.drop(['behavior','id_y', 'direction', 'type'], axis=1,inplace=True)
    data.columns = (['organization_id', 'organization_name', 'totalFunding', 'plan_id', 'plan_code', 'plan_name','countryCode'])

    return data


def getTopDonorCountryFundingAmounts(countries, year, top=False, top_n=5):
    """
    For each plan, pull the amount funded by each donor.
    Since the path to the right data in the json is very long, I couldn't sort out how to keep the path in a variable.

    """
    # TODO: add metadata! With update date.
    def getDonorByCountry(country, year, top, top_n):
        endpoint_str = '/public/fts/flow?locationid={}&year={}&groupBy=organization'.format(country, year)
        url = 'https://api.hpc.tools/v1' + endpoint_str
        result = requests.get(url, auth=(constants.FTS_CLIENT_ID, constants.FTS_CLIENT_PASSWORD))
        result.raise_for_status()
        if result.json()['data']['report1']['fundingTotals']['total'] == 0:
            single = None
            print ('No funding data for country {} in {}'.format(country, year))
        else:
            single = result.json()['data']['report1']['fundingTotals']['objects'][0]['singleFundingObjects']

        if single:
            single = json_normalize(single)
            single['year'] = year
            single['dest_country_id'] = country
            single = single.sort_values('totalFunding', ascending=False)
            if top == True:
                single = single.head(top_n)
        return single

    country_ids = countries['id']

    data = pd.DataFrame([])

    #loop through each plan and append the donor data for it to a combined data set
    for country_id in country_ids:
        print 'Getting funding for country: {}'.format(country_id)
        funding = getDonorByCountry(country_id, year, top, top_n)
        print 'Done. Appending...'
        data = data.append(funding)

    data = data.merge(countries, how='left', left_on='dest_country_id', right_on='id')
    data.drop(['behavior','id_x', 'direction', 'type', 'dest_country_id', 'id_y'], axis=1,inplace=True)
    data.columns = (['organization_name', 'totalFunding', 'year', 'countryCode', 'Country'])

    return data


def getClusterFundingAmounts(plans):
    """
    For each plan, pull the amount required and funded at the cluster level.

    """
    # TODO: make a helper function like api_utils.get_fts_endpoint() that can take a very long key chain
    # TODO: make column indexes of final output a constant
    # TODO: add metadata! With update date.

    def getFundingByCluster(plan_id):
        url = None
        endpoint_str = '/public/fts/flow?planId={}&groupby=Cluster'.format(plan_id)
        url = 'https://api.hpc.tools/v1' + endpoint_str
        result = requests.get(url, auth=(constants.FTS_CLIENT_ID, constants.FTS_CLIENT_PASSWORD))
        result.raise_for_status()

        #Get the required funding amounts for each cluster
        requirements = result.json()['data']['requirements']
        if requirements and 'objects' in requirements:
            requirements = requirements['objects']
            requirements = json_normalize(requirements)
            requirements['plan_id'] = plan_id
        else:
            print ('No requirements data from this endpoint: {}'.format(url))
            requirements = None

        #Get the actual funded amounts for each cluster
        if len(result.json()['data']['report3']['fundingTotals']['objects']) > 0:
            funding = json_normalize(result.json()['data']['report3']['fundingTotals']['objects'][0]['singleFundingObjects'])
            funding['plan_id'] = plan_id
        else:
            print ('Empty data from this endpoint: {}'.format(url))
            funding = None

        #Join required and actual funding amounts together
        if funding is not None:
            combined = requirements.merge(funding, how='outer', on=['name', 'plan_id'])
        else:
            combined = requirements

        return combined

    plan_ids = plans['id']

    data = pd.DataFrame([])

    #loop through each plan and append the donor data for it to a combined data set
    for plan in plan_ids:
        print ('Getting for plan {}'.format(plan))
        funding = getFundingByCluster(plan)
        print ('Success! Appending plan {}'.format(plan))
        data = data.append(funding)
    #TODO: if a plan result in an error, skip that and move on

    #Merge on plan information for reference
    data = data.merge(plans, how='left', left_on='plan_id', right_on='id')

    #Select certain columns and rename them
    data = data[['name_x', 'revisedRequirements', 'totalFunding', 'plan_id','code','name_y','countryCode']]
    data.columns = (['cluster', 'revisedRequirements', 'totalFunding', 'plan_id', 'plan_code', 'plan_name','countryCode'])

    #Replace NaN funded amounts with 0s
    data.totalFunding = data.totalFunding.fillna(0)
    #Calculate percent funded
    data['percentFunded'] = data['totalFunding']/data['revisedRequirements']

    return data


def getCountryFundingAmounts(year_list, country_mapping):
    """
    For each country, pull the amount of funding received in each year.
    Since the path to the right data in the json is very long, I couldn't sort out how to keep the path in a variable.

    """
    # TODO: make a helper function like api_utils.get_fts_endpoint() that can take a very long key chain
    # TODO: make column indexes of final output a constant
    # TODO: add metadata! With update date.
    def getActualFundingByCountryGroup(year):
        url = None
        endpoint_str = '/public/fts/flow?year={}&groupby=Country'.format(year)
        url = 'https://api.hpc.tools/v1' + endpoint_str
        result = requests.get(url, auth=(constants.FTS_CLIENT_ID, constants.FTS_CLIENT_PASSWORD))
        result.raise_for_status()
        single = result.json()['data']['report3']['fundingTotals']['objects'][0]['singleFundingObjects']
        if single:
            single = json_normalize(single)
            single['year'] = year
        else:
            print ('Empty data from this endpoint: {}'.format(url))
            single = None
        return single

    data = pd.DataFrame([])

    #loop through each year and append the data for it to a combined data set
    for year in year_list:
        funding = getActualFundingByCountryGroup(year)
        data = data.append(funding)

    data = data.merge(country_mapping, how='left', on=['name','id'])
    data.drop(['id', 'direction', 'type'], axis=1,inplace=True)

    #Rename column headings
    data.rename(columns={'name': 'Country',
                             'iso3': 'countryCode'
                             }, inplace=True)

    data = data.sort_values(['Country','year'])
    #data.columns = (['organization_id', 'organization_name', 'totalFunding', 'plan_id', 'plan_code', 'plan_name','countryCode'])

    return data



def loadDataByDimension(dimension):
    """
    Given a dimension of funding data (e.g. clusters/donors/recipients), load the data for each country.
    Return a dict of country code to pandas dataframe for the funding data along the given dimension.
    """
    if dimension not in constants.FTS_SCHEMAS.keys():
        raise Exception('Not a valid funding dimension for downloaded data from FTS: {}!'.format(dimension))
    schema = constants.FTS_SCHEMAS[dimension]
    data_dir = os.path.join(constants.LATEST_RAW_DATA_PATH, constants.FTS_DIR)
    date_str = date.today().isoformat()
    with open(os.path.join(data_dir, constants.FTS_DOWNLOAD_DATE_FILE), 'r') as f:
        date_str = f.read().strip()
    data = {}
    for code, country in constants.COUNTRY_CODES.iteritems():
        file_name = '-'.join([constants.FTS_FILE_PREFIX, code, dimension, date_str])
        file_path = os.path.join(data_dir, '{}.csv'.format(file_name))
        df = pd.read_csv(file_path, encoding='utf-8')
        data[country] = df
    return data


# def loadDataByCountryCode(country_code):
#     """
#     Given a country, load the data for each funding dimension.
#     Return a dict of funding dimension to pandas dataframe for the funding data for the given country.
#     """
#     if country_code not in constants.COUNTRY_CODES.keys():
#         if country_code not in constants.COUNTRY_CODES.values():
#             raise Exception('Not a valid country code for downloaded data from FTS: {}!'.format(country_code)
#         else:
#             # Convert country name to country code
#             country_code = constants.COUNTRY_CODES.values().index(country_code)
#
#     data_dir = os.path.join(constants.LATEST_RAW_DATA_PATH, constants.FTS_DIR)
#     date_str = date.today().isoformat()
#     with open(os.path.join(data_dir, constants.FTS_DOWNLOAD_DATE_FILE), 'r') as f:
#         date_str = f.read().strip()
#     data = {}
#     for dimension, schema in constants.FTS_SCHEMAS.iteritems():
#         file_name = '-'.join([constants.FTS_FILE_PREFIX, country_code, dimension, date_str])
#         file_path = os.path.join(data_dir, '{}.csv'.format(file_name))
#         df = pd.read_csv(file_path, encoding='utf-8')
#         data[dimension] = df
#     return data


# def combineData(data, column):
#     """
#     Combine given data across a particular column, where data is a dictionary from keys to dataframes,
#     and the given column corresponds to a column name for the keys of the data dict, e.g. 'Country' or 'Dimension'.
#     Returns a single dataframe that combines all the dataframes in the given data.
#     """
#     combined_df = pd.DataFrame()
#     for key, df in data.iteritems():
#         df[column] = key
#         combined_df = combined_df.append(df)
#     return combined_df
#
#
# def updateLatestDataDir(download_path, current_date_str):
#     """
#     Copies all files from the given download_path into the latest data directory configured in
#     `resources/constants.py`. Appends to the run_dates.txt file with the current run date.
#     """
#     if not download_path or not current_date_str:
#         print 'Could not copy latest data for this run to the latest data directory!'
#         return
#     dir_util.copy_tree(download_path, constants.LATEST_DERIVED_DATA_PATH)
#     with open(constants.LATEST_DERIVED_RUN_DATE_FILE, 'a') as run_file:
#         run_file.write('{}-fts\n'.format(current_date_str))
#     return


# def createCurrentDateDir(parent_dir):
#     """
#     Create a new directory with the current date (ISO format) under the given parent_dir.
#     Return whether it was successful, the full path for the new directory, and the current date string.
#     If the date directory already exists or is not successful, default to returning the parent_dir as the full path.
#     """
#     # Create a new directory of the current date under the given parent_dir if it doesn't already exist
#     current_date_str = date.today().isoformat()
#     dir_path = os.path.join(parent_dir, current_date_str)
#     success = data_utils.safely_mkdir(dir_path)
#     if not success:
#         # Safely default to returning the parent_dir if we cannot create the dir_path
#         print 'Could not create a new directory for the current date [{}], defaulting to existing parent dir: {}'.format(current_date_str, parent_dir)
#         dir_path = parent_dir
#     else:
#         print 'Created new derived data dir: {}'.format(dir_path)
#     return success, dir_path, current_date_str
#
#
# def saveDerivedData(data, dir_path):
#     """
#     Save the derived data into a new dated directory under the given parent_dir (defaults to DERIVED_DATA_PATH configured in `resources/constants.py`).
#     Return whether any data saving was successful.
#     """
#     # Save data to dated directory under the given parent_dir
#     success = False
#     for dimension, df in data.iteritems():
#         df_path = os.path.join(dir_path, 'fts-{}.csv'.format(dimension))
#         print 'Saving derived data for dimension [{}] to: {}'.format(dimension, df_path)
#         df.to_csv(df_path, index=False, encoding='utf-8')
#         success = True
#     return success
#
#
# def run_transformations_by_dimension():
#     """
#     This is an example of some data transformations we can do to go from raw data to derived data.
#     """
#     print 'Load and process downloaded data from FTS'
#     print 'Create current date directory as the download path...'
#     _, download_path, current_date_str = createCurrentDateDir(constants.DERIVED_DATA_PATH)
#     print 'Load data by dimension...'
#     data_by_dimension = {}
#     for dimension, schema in constants.FTS_SCHEMAS.iteritems():
#         data_for_dimension = loadDataByDimension(dimension)
#         print 'Combine data for dimension [{}] across all countries...'.format(dimension)
#         data_by_dimension[dimension] = combineData(data_for_dimension, constants.COUNTRY_COL)
#         print data_by_dimension[dimension]
#
#     success = saveDerivedData(data_by_dimension, download_path)
#     if success:
#         print 'Copy data from {} to {}...'.format(download_path, constants.LATEST_DERIVED_DATA_PATH)
#         updateLatestDataDir(download_path, current_date_str)
#
#     #dir_util.copy_tree(download_path, constants.EXAMPLE_DERIVED_DATA_PATH)
#
#     print 'Done!'


def prepend_metadata(metadata, filepath):
    with open(filepath, 'r') as original:
        data = original.read()
    with open(filepath, 'w') as modified:
        modified.write('#')
        json.dump(metadata, modified)
        modified.write('\n' + data)


def run():

    t0 = time.time()

    # Hardcode FTS metadata
    metadata = {}
    metadata['extract_date'] = date.today().isoformat()
    metadata['source_data'] = date.today().isoformat()
    metadata['source_key'] = 'FTS'
    metadata['source_url'] = 'https://fts.unocha.org'
    metadata['update_frequency'] = 'Hourly'

    print 'Get list of countries and ISO-3 codes'
    countries = getCountries()
    print countries.head()


    print 'Get list of plans'
    plans = getPlans(year=constants.FTS_APPEAL_YEAR, country_mapping = countries)
    print plans.head()

    #Filter plans to only include those that are not RRPs and where the funding requirement is > 0
    plans = plans[(plans.categoryName != 'Regional response plan') & (plans.revisedRequirements > 0)]

    plan_index = plans[['id', 'code', 'name', 'countryCode']]


    print 'Get required and committed funding from the FTS API'
    initial_result = getInitialRequiredAndCommittedFunding(plans)
    print initial_result.head()
    official_data_path = os.path.join(constants.EXAMPLE_DERIVED_DATA_PATH, 'funding_progress.csv')
    initial_result.to_csv(official_data_path, encoding='utf-8', index=False)
    prepend_metadata(metadata, official_data_path)

    print 'Get donor funding amounts to each plan from the FTS API'
    donor_funding_plan = getDonorPlanFundingAmounts(plan_index)
    print donor_funding_plan.head()
    official_data_path = os.path.join(constants.EXAMPLE_DERIVED_DATA_PATH, 'funding_donors_appeal.csv')
    donor_funding_plan.to_csv(official_data_path, encoding='utf-8', index=False)
    prepend_metadata(metadata, official_data_path)

    print 'Get required and committed funding at the cluster level from the FTS API'
    cluster_funding = getClusterFundingAmounts(plan_index)
    print cluster_funding.head()
    official_data_path = os.path.join(constants.EXAMPLE_DERIVED_DATA_PATH, 'funding_clusters.csv')
    cluster_funding.to_csv(official_data_path, encoding='utf-8', index=False)
    prepend_metadata(metadata, official_data_path)

    print 'Get funding by destination country for given years'
    country_funding = getCountryFundingAmounts(range(2015, 2018), countries)
    print country_funding.head()
    official_data_path = os.path.join(constants.EXAMPLE_DERIVED_DATA_PATH, 'funding_dest_countries.csv')
    country_funding.to_csv(official_data_path, encoding='utf-8', index=False)
    prepend_metadata(metadata, official_data_path)

    print 'Get top donors by destination country for given years'
    donor_funding_country = getTopDonorCountryFundingAmounts(countries, 2016, top=True, top_n=5)
    print donor_funding_country.head()
    official_data_path = os.path.join(constants.EXAMPLE_DERIVED_DATA_PATH, 'funding_donors_country.csv')
    donor_funding_country.to_csv(official_data_path, encoding='utf-8', index=False)
    prepend_metadata(metadata, official_data_path)

    print 'Done!'
    print 'Total time taken in minutes: {}'.format((time.time() - t0)/60)



if __name__ == "__main__":
    run()
