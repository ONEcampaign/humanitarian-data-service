import os.path

# Load secrets
try:
    from secrets import *
except ImportError:
    print 'Could not import secrets!'
    pass

# Paths
BASE = os.path.abspath(os.path.dirname(__file__))
BASE_DATA_PATH = os.path.join(BASE, 'data')
RAW_DATA_PATH = os.path.join(BASE_DATA_PATH, 'raw')
DERIVED_DATA_PATH = os.path.join(BASE_DATA_PATH, 'derived')
LATEST_RAW_DATA_PATH = os.path.join(RAW_DATA_PATH, 'latest')
LATEST_RAW_RUN_DATE_FILE = os.path.join(LATEST_RAW_DATA_PATH, 'run_dates.txt')
LATEST_DERIVED_DATA_PATH = os.path.join(DERIVED_DATA_PATH, 'latest')
LATEST_DERIVED_RUN_DATE_FILE = os.path.join(LATEST_DERIVED_DATA_PATH, 'run_dates.txt')
EXAMPLE_RAW_DATA_PATH = os.path.join(RAW_DATA_PATH, 'example')
EXAMPLE_DERIVED_DATA_PATH = os.path.join(DERIVED_DATA_PATH, 'example')

# Metadata
METADATA_URL = 'https://docs.google.com/spreadsheets/d/1eOphCuvRHRErw81vIGlt9XcKqT3aP-xtu3P_1_a_1QI/edit#gid=0'
METADATA_FILE = os.path.join(EXAMPLE_DERIVED_DATA_PATH, 'metadata.csv')
METADATA_INDEX = 'data_endpoint'
METADATA_LIST_COLS = ['contact']
METADATA_JSON_COLS = ['additional_metadata', 'merged_metadata']

# Standard name for a column of country names
COUNTRY_COL = 'Country'

# Map of country codes to country names, ISO 3166-1 alpha-3 (similar to UNDP and NATO standards)
# TODO: verify which country code standard the int'l dev community actually uses
COUNTRY_CODES = {
  'CHD': 'Chad',
  'CMR': 'Cameroon',
  'NER': 'Niger',
  'NGR': 'Nigeria'
}

# Metadata on original data sources (map from source_key to source_org)
DATA_SOURCES = {
  'HNO': 'UNOCHA: Humanitarian Needs Overview',
  'DTM': 'IOM, NEMA, SEMA, Red Cross: Displacement Tracking Matrix',
  'ORS': 'UNOCHA ROWCA: Online Reporting System (via HDX)',
  'FTS': 'UNOCHA: Financial Tracking Service',
  'WB' : 'World Bank: World Development Indicators',
  'HCR': 'UNHCR: The UN Refugee Agency',
  'ESA': 'UN Department of Economic and Social Affairs: World Population Prospects',
  'FSI': 'FFP: Fund For Peace'
}

# HDX website environments, in order of priority to pull data from (i.e. always try 'prod' first)
HDX_SITES = ['prod', 'feature', 'test']

# HDX data
HDX_DATASETS = [
  'lcb-displaced', 
  'lake-chad-basin-fts-appeal-data',
  'lake-chad-basin-key-figures-january-2017'  # This Dataset has multiple Resources
  #'conflict-events',
  #'lake-chad-basin-baseline-population',
  #'lac-chad-basin-area'  # zipped shapefiles
]

# Based off of HDX expected update frequency keywords (required for each Dataset)
UPDATE_FREQUENCY = [
  'Every day',
  'Every week',
  'Every two weeks',
  'Every month',
  'Every three months',
  'Every six months',
  'Every year',
  'Never',
  'Unknown / Irregular'
]

# UNHCR sub-directory (e.g. under data/raw/latest)
UNHCR_DIR = 'unhcr'

# FTS API (under UNOCHA)
FTS_API_BASE_URL = 'https://api.hpc.tools/v1'

# FTS sub-directory (e.g. under data/raw/latest)
FTS_DIR = 'fts'

# FTS data download date file
FTS_DOWNLOAD_DATE_FILE = 'download_date.txt'

# FTS data file prefix
FTS_FILE_PREFIX = 'fts-appeals'

# FTS data schemas
FTS_SCHEMAS = {
  'donors': ['Donor organization', 'Funding US$', 'Pledges US$'],
  'clusters': ['Cluster/Sector', 'Requirements US$', 'Funding US$', 'Coverage %'],
  'recipients': ['Recipient organization', 'Requirements US$', 'Funding US$', 'Pledges US$', 'Coverage %']
}

# DTM column names referring to states within a country
DTM_STATE_COLS = {
  'location': 'STATE',
  'site': 'STATE',
  'baseline': 'state_name'
}

# DTM file mapping (temporary for now)
# TODO: make file names generic including DTM assessment type to remove the need for this config
DTM_FILE_NAMES = {
  'location': '14_DTM_NIgeria_Round_XIV_Dataset_of_Location_Assessment.csv',
  'site': '06_DTM_Nigeria_Round_XIV_Dataset_of_Site_Assessment.csv',
  'baseline': 'wards_05_DTM_Nigeria_Round_XIV_Dataset_of_Baseline_Assessment.csv'
}

# UNHCR file mapping
UNHCR_FILE_NAMES = {
  'raw_asylum_country': 'unhcr_midyeartrends_table1_1_2016.csv',
  'asylum_country': 'unhcr_midyeartrends_population_by_asylum_country_2016.csv',
  'raw_origin_country': 'unhcr_midyeartrends_table1_2_2016.csv',
  'origin_country': 'unhcr_midyeartrends_population_by_origin_country_2016.csv'
}

# UN Department of Economic and Social Affairs file mapping
ESA_FILE_NAMES = {
  'wpp_overall': 'wpp_medium_projection_variantid2_2000_2017.csv'
}
