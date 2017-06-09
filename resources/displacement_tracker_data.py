import requests
import pandas as pd
import os.path
from resources import constants
import json
from pandas.io.json import json_normalize

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

# Set year for country-level funding data
FUNDING_YEAR = 2016

# Define all endpoints
URL_POPULATIONS_REFUGEELIKE_ASYLUM = '/populations/refugeelike/asylum/index'
URL_INDICATORS_GNI = '/indicators/gni/index'
URL_PLANS_PROGRESS = '/funding/plans/progress/index'
URL_POPULATION = '/populations/totals/index'
URL_FRAGILE_STATE = '/fragility/fragile-state-index/index'
URL_NEEDS = '/needs/plans/index'
URL_FUNDING_DEST_COUNTRY = '/funding/countries/destination/index/{}'.format(FUNDING_YEAR)
URL_FUNDING_DEST_DONORS = '/funding/countries/donors/index'



# Define path for raw country names data
country_names_path = os.path.join(constants.EXAMPLE_RAW_DATA_PATH, 'UNSD Methodology.csv')

# Define path for relatable geography populations data
relatable_population_path = os.path.join(constants.EXAMPLE_DERIVED_DATA_PATH, '2017_relatable_population_rankings.csv')

# Define path for stories of displacement
displacement_stories_path = os.path.join(constants.EXAMPLE_DERIVED_DATA_PATH, 'stories_of_displacement_links.csv')

def merge_data(
        funding_year = FUNDING_YEAR,
        country_names_path=country_names_path,
        relatable_population_path=relatable_population_path,
        displacement_stories_path=displacement_stories_path,
        url_populations_refugeelike_asylum=(ROOT + URL_POPULATIONS_REFUGEELIKE_ASYLUM),
        url_indicators_gni=(ROOT + URL_INDICATORS_GNI),
        url_plans_progress=(ROOT + URL_PLANS_PROGRESS),
        url_population=(ROOT + URL_POPULATION),
        url_fragile_state=(ROOT + URL_FRAGILE_STATE),
        url_needs=(ROOT + URL_NEEDS),
        url_funding_dest_country=(ROOT + URL_FUNDING_DEST_COUNTRY),
        url_funding_dest_donors=(ROOT + URL_FUNDING_DEST_DONORS)
    ):

    ####################  COUNTRY NAMES ####################
    # Get the data from .csv
    df_country_names = pd.read_csv(country_names_path, encoding='utf-8')

    # Select relevant fields
    df_country_names = df_country_names[[
        'Country or Area',
        'ISO-alpha3 Code'
    ]]

    # Drop null values
    df_country_names = df_country_names.dropna()

    # Set country code to be the index
    df_country_names = df_country_names.set_index('ISO-alpha3 Code')

    # Rename fields
    df_country_names.rename(columns={'Country or Area': 'Country'}, inplace=True)


    ####################  DISPLACEMENT STORIES ####################
    # Get the data from .csv
    df_displacement_stories = pd.read_csv(displacement_stories_path, encoding='utf-8')

    # Set country code to be the index
    df_displacement_stories = df_displacement_stories.set_index('countryCode')

    # Select relevant fields
    df_displacement_stories = df_displacement_stories[[
        'storyTitle', 'storySource',
        'storyTagLine', 'storyURL'
    ]]

    # Drop null values
    df_displacement_stories = df_displacement_stories.dropna()


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
        'Total population of concern', 'Total Refugee and people in refugee-like situations'
    ]]

    # Add field to rank total total population of concern
    df_populations_refugeelike_asylum['Rank of total population of concern'] = df_populations_refugeelike_asylum[
        'Total population of concern'].rank(ascending=False, method='min').astype(int)

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
        'appealFunded', 'revisedRequirements', 'neededFunding'  # Add more fields here
    ]]

    # Rename fields
    df_plans_progress.rename(columns={'appealFunded': 'Appeal funds committed to date',
                                      'revisedRequirements': 'Appeal funds requested',
                                      'neededFunding': 'Appeal funds still needed'}, inplace=True)

    df_plans_progress['Appeal percent funded'] = df_plans_progress['Appeal funds committed to date']/df_plans_progress['Appeal funds requested']

    # Drop null values
    df_plans_progress = df_plans_progress.dropna()


    ######## FUNDING BY DESTINATION COUNTRY ############
    #Get the data from the API
    funding_dest_country_data = requests.get(url_funding_dest_country).json()

    # Build a dataframe
    df_funding_dest_country = pd.DataFrame(funding_dest_country_data['data']).T

    # Select relevant fields
    df_funding_dest_country = df_funding_dest_country[[
        'totalFunding'
    ]]

    # Rename fields
    df_funding_dest_country.rename(columns={'totalFunding': 'Humanitarian aid received'},
                                   inplace=True)

    # Add field to rank total total population of concern
    df_funding_dest_country['Rank of humanitarian aid received'] = df_funding_dest_country[
        'Humanitarian aid received'].rank(ascending=False, method='min').astype(int)

    # Drop null values
    df_funding_dest_country = df_funding_dest_country.dropna()


    ################## TOP 5 DONORS TO EACH DESTINATION COUNTRY ###################
    #Get the data from the API
    funding_dest_donors_data = requests.get(url_funding_dest_donors).json()

    # Build a dataframe
    df_funding_dest_donors = json_normalize(funding_dest_donors_data['data']).T
    #df_funding_dest_donors = pd.DataFrame(funding_dest_donors_data['data']).T

    df_funding_dest_donors.columns = (['Top 5 Donors'])


    ####################  NEEDS ####################
    # Get the data from the API
    needs_data = requests.get(url_needs).json()

    # Build a dataframe
    df_needs = pd.DataFrame(needs_data['data']).T

    # Select relevant fields
    df_needs = df_needs[[
        'inNeedTotal', 'inNeedHealth', 'inNeedEducation',
        'inNeedFoodSecurity', 'inNeedProtection', 'sourceURL',
        'inNeedShelter-CCCM-NFI', 'inNeedWASH', 'sourceType'
    ]]

    # Rename fields
    df_needs.rename(columns={'inNeedTotal': 'Total people in need',
                             'inNeedHealth': 'People in need of health support',
                             'inNeedEducation': 'Children in need of education',
                             'inNeedFoodSecurity': 'People who are food insecure',
                             'inNeedProtection': 'People in need of protection',
                             'inNeedShelter-CCCM-NFI': 'People in need of shelter',
                             'inNeedWASH': 'People in need of water, sanitization & hygiene',
                             'sourceURL': 'Source of needs data',
                             'sourceType': 'Source type of needs data'
                             }, inplace=True)


    ######## FIND PLACES WITH SIMILAR POPULATIONS TO PEOPLE IN NEED ########

    # Get the relateable populations data from .csv
    df_relatable_populations = pd.read_csv(relatable_population_path)

    def find_nearest_place_population(reference_value):

        if reference_value:
            nearest_row = df_relatable_populations.iloc[(df_relatable_populations['Population']- reference_value).abs().argsort()[0]]
            nearest_population = nearest_row['Population']
        else:
            nearest_population = 0.00

        return nearest_population

    def find_nearest_place(reference_value):

        if reference_value:
            nearest_row = df_relatable_populations.iloc[(df_relatable_populations['Population']- reference_value).abs().argsort()[0]]
            nearest_place = nearest_row['City, State, Country']
        else:
            nearest_place = ''

        return nearest_place

    df_needs['Place with similar population as people in need'] = df_needs['Total people in need'].apply(
        find_nearest_place)

    df_needs['Population of place with similar population'] = df_needs['Total people in need'].apply(
        find_nearest_place_population)


    ####################  SAMPLE CLUSTERS ####################

    # Build a dataframe
    # df_clusters = pd.read_json('sample_clusters.json').T
    # df_clusters = df_clusters[['clusters']]


    ################# COMBINE ALL DATA ##############

    # Make a list of all dataframes
    all_dataframes = [
        df_country_names,
        df_populations_refugeelike_asylum,
        df_indicators_gni,
        df_plans_progress,
        df_population,
        df_fragile_state,
        df_needs,
        df_funding_dest_country,
        df_funding_dest_donors,
        df_displacement_stories
        #   df_clusters
    ]

    df_final = pd.concat(all_dataframes, axis=1)

    # Add calculation for displaced people as a ratio of total population
    df_final['Population of concern per 1000 population'] = (df_final['Total population of concern'] / df_final[
        'Population'])*1000

    # Add calculation for displaced people per million GDP
    df_final['Population of concern per million GDP'] = ((df_final['Total population of concern'] * 1000000) / (df_final[
        'GDP Per Capita'] * df_final['Population']))

    # Add field to specify whether country has current humanitarian appeal in FTS
    df_final['Country has current appeal'] = df_final['Appeal funds requested'].notnull()


    ################## STRUCTURE DICTIONARY ##################

    # Clean up NaN values
    df_final = df_final.fillna('')

    # Transform dataframe to dictionary
    df_as_dict = df_final.to_dict(orient='index')

    # Define field names for each strand
    strand_01_fields = ['Appeal funds still needed', 'Appeal funds requested', 'Appeal funds committed to date',
                        'Appeal percent funded', 'Source of needs data', 'Source type of needs data',
                        'Total people in need', 'Place with similar population as people in need']
    strand_02_fields = ['Population of concern per 1000 population', 'Fragile State Index Score',
                        'Total population of concern', 'Total Refugee and people in refugee-like situations',
                        'GDP Per Capita', 'Population of concern per million GDP']
    strand_03_fields = ['Humanitarian aid received', 'Appeal funds requested', 'Appeal percent funded',
                        'Rank of total population of concern', 'Rank of humanitarian aid received']

    needs_fields = ['People in need of health support','Children in need of education',
                    'People who are food insecure','People in need of protection','People in need of shelter',
                    'People in need of water, sanitization & hygiene']

    story_fields = ['storyTitle', 'storySource', 'storyTagLine', 'storyURL']

    # For every object, get / group the values by strand
    data = {}
    for x in df_as_dict.keys():

        # Create an empty dict
        country_dict = {}

        # Populate the dict with those value that don't require nesting
        country_dict['Country'] = df_as_dict[x]['Country']
        country_dict['Fragile State Index Rank'] = df_as_dict[x]['Fragile State Index Rank']
        country_dict['Country has current appeal'] = df_as_dict[x]['Country has current appeal']

        # Populate the dict with story fields
        story_fields_dict = {}
        if df_as_dict[x]['storyURL']:
            for field in story_fields:
                story_fields_dict[field] = (df_as_dict[x][field])
        country_dict['Displacement_story'] = story_fields_dict

        # Populate the dict with strand 1 data if the country has a current appeal
        strand_01_dict = {}
        if df_as_dict[x]['Country has current appeal']:
            strand_01_dict['Needs_Data'] = {}
            for names_01 in strand_01_fields:
                strand_01_dict[names_01] = (df_as_dict[x][names_01])
            for name in needs_fields:
                if df_as_dict[x][name] != '':
                    strand_01_dict['Needs_Data'][name] = (df_as_dict[x][name])
        country_dict['Strand_01_Needs'] = strand_01_dict

        # Populate the dict with strand 2 data
        strand_02_dict = {}
        for names_02 in strand_02_fields:
            strand_02_dict[names_02] = (df_as_dict[x][names_02])
        country_dict['Strand_02_People'] = strand_02_dict

        # Populate the dict with strand 3 data
        strand_03_dict = {}
        strand_03_dict['Top 5 donors of humanitarian aid'] = []
        for names_03 in strand_03_fields:
            strand_03_dict[names_03] = (df_as_dict[x][names_03])
        if df_as_dict[x]['Top 5 Donors']:
            strand_03_dict['Top 5 donors of humanitarian aid'] = df_as_dict[x]['Top 5 Donors']
        country_dict['Strand_03_Aid'] = strand_03_dict

        # Add the country dict to the data dict
        data[x] = country_dict

    # Create the metadata dict
    metadata = {
        "State fragility index": "some metadata here",
        "Total amount of money funded to date": "some metadata here",
        "Total amount of money needed": "some metadata here"
    }

    # At the higher level, structure the json with 'data' and 'metadata'
    final_json = {
        'data': data,
        'metadata': metadata
    }

    return final_json


def run():
    print 'Pulling and merging data'
    data = merge_data()
    # print data.head()
    official_data_path = os.path.join(constants.EXAMPLE_DERIVED_DATA_PATH, 'displacement_tracker.json')

    print 'Writing file'
    with open(official_data_path, 'w') as outfile:
        json.dump(data, outfile, indent=4, separators=(',', ': '), ensure_ascii=True, sort_keys=True)  # .encode('utf-8')
        # outfile.write(unicode(data))
        # data.to_json(official_data_path, orient='index')
        # json.dumps(data, indent=4, separators=(',', ': '))


if __name__ == "__main__":
    run()
