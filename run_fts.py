import os.path
import pandas as pd
from datetime import date
from distutils import dir_util

import requests
from pandas.io.json import json_normalize

from resources import constants
from utils import data_utils, api_utils

"""
This script currently updates the committed and paid funding for appeals, and replaces the old `funding_progress.csv` file.
Scheduling this script to run on a nightly or weekly basis is sufficient to automatically update the /world/funding_progress endpoint.

Functions to query raw funding data from the UNOCHA FTS API, perform transformations, and save the data.
See API docs here: https://fts.unocha.org/sites/default/files/publicftsapidocumentation.pdf
"""


def getPlans(year=2017):
    # Get all plans from the FTS API
    data = api_utils.get_fts_endpoint('/public/plan/year/{}'.format(year))

    # Extract names from objects
    data['categoryName'] = data.categories.apply(lambda x: x[0]['name'])
    data['emergencies'] = data.emergencies.apply(lambda x: x[0]['name'] if x else None)
    data['countryCode'] = data.locations.apply(lambda x: x[0]['iso3'] if x else None)

    #Tidy the dataset
    data.drop(['origRequirements', 'startDate', 'endDate', 'years', 'categories', 'emergencies', 'locations'], axis=1, inplace=True)
    data = data.where((pd.notnull(data)), None).sort_values('name')

    return data


def updateCommittedAndPaidFunding(year=2017):
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
        plan_funds = api_utils.get_fts_endpoint('/public/fts/flow?planId={}'.format(plan_id), 'flows')
        funded = plan_funds[(plan_funds.boundary == 'incoming') & (plan_funds.status != 'pledge')]
        return funded['amountUSD'].sum()

    data['appealFunded'] = data['id'].apply(pull_committed_funding_for_plan)
    
    # Calculate percent funded
    data['percentFunded'] = data.appealFunded / data.revisedRequirements

    data['neededFunding'] = data.revisedRequirements - data.appealFunded

    return data


def getDonorFundingAmounts(plans):
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
        result = result.json()['data']['report1']['fundingTotals']['objects'][0]['singleFundingObjects']
        if result:
            result = json_normalize(result)
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
    data.drop(['id_y', 'direction', 'type'], axis=1,inplace=True)
    data.columns = (['organization_id', 'organization_name', 'totalFunding', 'plan_id', 'plan_code', 'plan_name','countryCode'])

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
        funding = result.json()['data']['report3']['fundingTotals']['objects'][0]['singleFundingObjects']
        if funding:
            funding = json_normalize(funding)
            funding['plan_id'] = plan_id
        else:
            print ('Empty data from this endpoint: {}'.format(url))
            funding = None

        #Join required and actual funding amounts together
        combined = requirements.merge(funding, how='outer', on=['name', 'plan_id'])

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


def getCountryFundingAmounts(years):
    """
    For each country, pull the amount funded in each year.
    Since the path to the right data in the json is very long, I couldn't sort out how to keep the path in a variable.

    """
    # TODO: make a helper function like api_utils.get_fts_endpoint() that can take a very long key chain
    # TODO: make column indexes of final output a constant
    # TODO: add metadata! With update date.
    def getActualFundingByCountryGroup(year):
        url = None
        endpoint_str = '/public/fts/flow?year={}&groupby=Country'.format(year)
        url = 'https://api.hpc.tools/v1' + endpoint_str
        result = requests.get(url, auth=(CLIENT_ID, PASSWORD))
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
    for year in years:
        funding = getActualFundingByCountryGroup(year)
        data = data.append(funding)

    #data = data.merge(plans, how='left', left_on='plan_id', right_on='id')
    #data.drop(['id_y', 'direction', 'type'], axis=1,inplace=True)
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


def loadDataByCountryCode(country_code):
    """
    Given a country, load the data for each funding dimension.
    Return a dict of funding dimension to pandas dataframe for the funding data for the given country.
    """
    if country_code not in constants.COUNTRY_CODES.keys():
        if country_code not in constants.COUNTRY_CODES.values():
            raise Exception('Not a valid country code for downloaded data from FTS: {}!'.format(country))
        else:
            # Convert country name to country code
            country_code = constants.COUNTRY_CODES.values().index(country_code)

    data_dir = os.path.join(constants.LATEST_RAW_DATA_PATH, constants.FTS_DIR)
    date_str = date.today().isoformat()
    with open(os.path.join(data_dir, constants.FTS_DOWNLOAD_DATE_FILE), 'r') as f:
        date_str = f.read().strip()
    data = {}
    for dimension, schema in constants.FTS_SCHEMAS.iteritems():
        file_name = '-'.join([constants.FTS_FILE_PREFIX, country_code, dimension, date_str])
        file_path = os.path.join(data_dir, '{}.csv'.format(file_name))
        df = pd.read_csv(file_path, encoding='utf-8')
        data[dimension] = df
    return data


def combineData(data, column):
    """
    Combine given data across a particular column, where data is a dictionary from keys to dataframes,
    and the given column corresponds to a column name for the keys of the data dict, e.g. 'Country' or 'Dimension'.
    Returns a single dataframe that combines all the dataframes in the given data.
    """
    combined_df = pd.DataFrame()
    for key, df in data.iteritems():
        df[column] = key
        combined_df = combined_df.append(df)
    return combined_df


def updateLatestDataDir(download_path, current_date_str):
    """
    Copies all files from the given download_path into the latest data directory configured in
    `resources/constants.py`. Appends to the run_dates.txt file with the current run date.
    """
    if not download_path or not current_date_str:
        print 'Could not copy latest data for this run to the latest data directory!'
        return
    dir_util.copy_tree(download_path, constants.LATEST_DERIVED_DATA_PATH)
    with open(constants.LATEST_DERIVED_RUN_DATE_FILE, 'a') as run_file:
        run_file.write('{}-fts\n'.format(current_date_str))
    return


def createCurrentDateDir(parent_dir):
    """
    Create a new directory with the current date (ISO format) under the given parent_dir.
    Return whether it was successful, the full path for the new directory, and the current date string.
    If the date directory already exists or is not successful, default to returning the parent_dir as the full path.
    """
    # Create a new directory of the current date under the given parent_dir if it doesn't already exist
    current_date_str = date.today().isoformat()
    dir_path = os.path.join(parent_dir, current_date_str)
    success = data_utils.safely_mkdir(dir_path)
    if not success:
        # Safely default to returning the parent_dir if we cannot create the dir_path
        print 'Could not create a new directory for the current date [{}], defaulting to existing parent dir: {}'.format(current_date_str, parent_dir)
        dir_path = parent_dir
    else:
        print 'Created new derived data dir: {}'.format(dir_path)
    return success, dir_path, current_date_str


def saveDerivedData(data, dir_path):
    """
    Save the derived data into a new dated directory under the given parent_dir (defaults to DERIVED_DATA_PATH configured in `resources/constants.py`).
    Return whether any data saving was successful.
    """
    # Save data to dated directory under the given parent_dir
    success = False
    for dimension, df in data.iteritems():
        df_path = os.path.join(dir_path, 'fts-{}.csv'.format(dimension))
        print 'Saving derived data for dimension [{}] to: {}'.format(dimension, df_path)
        df.to_csv(df_path, index=False, encoding='utf-8')
        success = True
    return success


def run_transformations_by_dimension():
    """
    This is an example of some data transformations we can do to go from raw data to derived data.
    """
    print 'Load and process downloaded data from FTS'
    print 'Create current date directory as the download path...'
    _, download_path, current_date_str = createCurrentDateDir(constants.DERIVED_DATA_PATH)
    print 'Load data by dimension...'
    data_by_dimension = {}
    for dimension, schema in constants.FTS_SCHEMAS.iteritems():
        data_for_dimension = loadDataByDimension(dimension)
        print 'Combine data for dimension [{}] across all countries...'.format(dimension)
        data_by_dimension[dimension] = combineData(data_for_dimension, constants.COUNTRY_COL)
        print data_by_dimension[dimension]

    success = saveDerivedData(data_by_dimension, download_path)
    if success:
        print 'Copy data from {} to {}...'.format(download_path, constants.LATEST_DERIVED_DATA_PATH)
        updateLatestDataDir(download_path, current_date_str)
    
    #dir_util.copy_tree(download_path, constants.EXAMPLE_DERIVED_DATA_PATH)

    print 'Done!'


def run():

    print 'Get list of plans'
    plans = getPlans(year=2017)
    print plans.head()

    #Filter plans to only include those that are not RRPs and where the funding requirement is > 0
    plans = plans[(plans.categoryName != 'Regional response plan') & (plans.revisedRequirements > 0)]

    plan_index = plans[['id', 'code', 'name', 'countryCode']]

    print 'Get required and committed funding from the FTS API'
    initial_result = getInitialRequiredAndCommittedFunding(plans)
    print initial_result.head()
    official_data_path = os.path.join(constants.EXAMPLE_DERIVED_DATA_PATH, 'funding_progress.csv')
    initial_result.to_csv(official_data_path, encoding='utf-8', index=False)

    print 'Get donor funding amounts to each plan from the FTS API'
    donor_funding = getDonorFundingAmounts(plan_index)
    print donor_funding.head()
    official_data_path = os.path.join(constants.EXAMPLE_DERIVED_DATA_PATH, 'funding_donors.csv')
    donor_funding.to_csv(official_data_path, encoding='utf-8', index=False)

    print 'Get required and committed funding at the cluster level from the FTS API'
    cluster_funding = getClusterFundingAmounts(plan_index)
    print cluster_funding.head()
    official_data_path = os.path.join(constants.EXAMPLE_DERIVED_DATA_PATH, 'funding_clusters.csv')
    cluster_funding.to_csv(official_data_path, encoding='utf-8', index=False)

    print 'Done!'



if __name__ == "__main__":
    run()
