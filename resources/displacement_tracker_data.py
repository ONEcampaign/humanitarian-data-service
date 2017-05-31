import requests
import pandas as pd
import os.path
from resources import constants



"""
This script aggregates data from multiple endpoints and returns a single .json file containing all data
used in the displacement tracker project.

Scheduling this script would mean that the /displacement_tracker endpoint always returned the latest data
contained within the Humanitarian Data Service API.
"""


# For development
ROOT = 'http://localhost:5000'

# For live
# ROOT = 'http://ec2-34-200-18-111.compute-1.amazonaws.com'


# Define all endpoints
URL_POPULATIONS_REFUGEELIKE_ASYLUM = '/populations/refugeelike/asylum/index'
URL_INDICATORS_GNI = '/indicators/gni/index'
URL_PLANS_PROGRESS = '/funding/plans/progress/index'
URL_POPULATION = '/populations/totals/index'
URL_FRAGILE_STATE = '/fragility/fragile-state-index/index'


def merge_data(
    url_populations_refugeelike_asylum=(ROOT + URL_POPULATIONS_REFUGEELIKE_ASYLUM),
    url_indicators_gni=(ROOT + URL_INDICATORS_GNI),
    url_plans_progress=(ROOT + URL_PLANS_PROGRESS),
    url_population=(ROOT + URL_POPULATION),
    url_fragile_state=(ROOT + URL_FRAGILE_STATE)
    ):

    ####################  POPULATIONS ####################
    # Get the data from the API
    population_data = requests.get(url_population).json()

    # Build a dataframe
    df_population = pd.DataFrame(population_data['data']).T

    # Select relevant fields
    df_population = df_population[[
        'PopTotal'
    ]]

    # Rename fields
    df_population.rename(columns={'PopTotal': 'Population'}, inplace=True)

    # Drop null values
    df_population = df_population.dropna()


    ####################  FRAGILE STATE ####################
    # Get the data from the API
    fragile_state_data = requests.get(url_fragile_state).json()

    # Build a dataframe
    df_fragile_state = pd.DataFrame(fragile_state_data['data']).T

    # Select relevant fields
    df_fragile_state = df_fragile_state[[
        'Total', 'Rank'
    ]]

    # Rename fields
    df_fragile_state.rename(columns={'Total': 'Fragile State Index Score',
                                  'Rank': 'Fragile State Index Rank'}, inplace=True)

    # Drop null values
    df_fragile_state = df_fragile_state.dropna()


    ####################  POPULATIONS_REFUGEELIKE_ASYLUM ####################
    # Get the data from the API
    populations_refugeelike_asylum_data = requests.get(url_populations_refugeelike_asylum).json()

    # Build a dataframe
    df_populations_refugeelike_asylum = pd.DataFrame(populations_refugeelike_asylum_data['data']).T

    # Select relevant fields
    df_populations_refugeelike_asylum = df_populations_refugeelike_asylum[[
        'Country', 'Total population of concern', 'Total Refugee and people in refugee-like situations'
    ]]

    # Drop null values
    df_populations_refugeelike_asylum = df_populations_refugeelike_asylum.dropna()



    ####################  INDICATORS GNI ####################
    # Get the data from the API
    indicators_gni_data = requests.get(url_indicators_gni).json()

    # Build a dataframe
    df_indicators_gni = pd.DataFrame(indicators_gni_data['data']).T

    # Select relevant fields
    df_indicators_gni = df_indicators_gni[[
        '2015'
    ]]

    # Rename fields
    df_indicators_gni.rename(columns={'2015': 'GDP Per Capita'}, inplace=True)

    # Drop null values
    df_indicators_gni = df_indicators_gni.dropna()



    ####################  PLANS PROGRESS ####################
    # Get the data from the API
    plans_progress_data = requests.get(url_plans_progress).json()

    # Build a dataframe
    df_plans_progress = pd.DataFrame(plans_progress_data['data']).T

    # Select relevant fields
    df_plans_progress = df_plans_progress[[
        'appealFunded','revisedRequirements','neededFunding'                        # Add more fields here
    ]]

    # Rename fields
    df_plans_progress.rename(columns={'appealFunded': 'Appeal funds committed to date',
                                      'revisedRequirements': 'Appeal funds requested',
                                      'neededFunding': 'Appeal funds still needed'}, inplace=True)



    # Drop null values
    df_plans_progress = df_plans_progress.dropna()



    ####################  SAMPLE CLUSTERS ####################

    # Build a dataframe
    #df_clusters = pd.read_json('sample_clusters.json').T
    #df_clusters = df_clusters[['clusters']]


    # Make a list of all dataframes
    all_dataframes = [
        df_populations_refugeelike_asylum,
        df_indicators_gni,
        df_plans_progress,
        df_population,
        df_fragile_state
     #   df_clusters
    ]

    df_final = pd.concat(all_dataframes, axis=1)

    # Add calculation for refugees as a ratio of total population
    df_final['Refugees and IDPs as Percent of Population'] = df_final['Total population of concern']/df_final['Population']


    return df_final



def run():
    print 'Pulling and merging data'
    data = merge_data()
    print data.head()
    official_data_path = os.path.join(constants.EXAMPLE_DERIVED_DATA_PATH, 'displacement_tracker.json')
    print 'Writing file'
    data.to_json(official_data_path, orient='index')



if __name__ == "__main__":
    run()
