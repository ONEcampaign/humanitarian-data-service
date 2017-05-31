# -*- coding: utf-8 -*-
import io
import ast
import json
import os.path
import requests
from pandas.io.json import json_normalize
import pandas as pd
from resources import constants


def safely_load_data(data_file, data_description, filter_value=None, filter_column=constants.COUNTRY_COL, has_metadata=False, na_values=None):
    """
    Attempt to load the data_file as a pandas dataframe (df).
    Return a tuple of whether it was successful, and either the df if it's successful, or an error message if it's not.
    """
    success = False
    result = None
    metadata = None
    file_path = None
    try:
        file_path = os.path.join(constants.EXAMPLE_DERIVED_DATA_PATH, data_file)
        if has_metadata and na_values:
            result = pd.read_csv(file_path, encoding='utf-8', header=1, na_values=na_values)
        elif has_metadata:
            result = pd.read_csv(file_path, encoding='utf-8', header=1)
        elif na_values:
            result = pd.read_csv(file_path, encoding='utf-8', na_values=na_values)
        else:
            result = pd.read_csv(file_path, encoding='utf-8')
        success = True
        if result.empty:
            result = 'Error: No {} data was found (empty file)'.format(data_description)
            success = False
        elif filter_value:
            result = result.loc[result[filter_column] == filter_value]
            if result.empty:
                result = 'Error: No {} data was found for the filter [{}: {}] (empty file)'.format(data_description, filter_column, filter_value)
                success = False
    except Exception as e:
        result = 'Error: No {} data was found ({})'.format(data_description, e)
        success = False

    if success:
        result = result.where((pd.notnull(result)), None)
        if has_metadata:
            # Extract metadata as json, expected to have the form "#{metadata_json}"
            # Find "source_key" key and do an org lookup and append with "source_org"
            with io.open(file_path, 'r', encoding='utf-8') as data_file:
                metadata_str = data_file.readline().strip()
                if metadata_str.startswith('#{') and metadata_str.endswith('}'):
                    metadata = json.loads(metadata_str[1:])
                    metadata["source_org"] = constants.DATA_SOURCES[metadata["source_key"]]

    return success, result, metadata


def safely_load_json_data(data_file, data_description):
    success = False
    result = None
    file_path = None
    try:
        file_path = os.path.join(constants.EXAMPLE_DERIVED_DATA_PATH, data_file)
        file = open(file_path, 'r')
        result =  file.read()
        result = json.loads(result)
        success = True
        if result == '':
            result = 'Error: No {} data was found (empty file)'.format(data_description)
            success = False
    except Exception as e:
        result = 'Error: No {} data was found ({})'.format(data_description, e)
        success = False

    return success, result


def load_metadata(endpoint_str=None, column=None, literal=False):
    """
    Load the metadata.csv file that maps metadata to each endpoint as a pandas dataframe. 
    Filter for the given endpoint string (e.g. '/funding/totals/:country' or '/indicators/gni') or metadata file column name (e.g. 'contact', 'source_date') if given.
    """
    metadata = pd.read_csv(constants.METADATA_FILE, encoding='utf-8')
    metadata = metadata.where((pd.notnull(metadata)), None)
    if endpoint_str and column:
        metadata = metadata[metadata.data_endpoint == endpoint_str].iloc[0][column]
        if metadata and literal:
            metadata = ast.literal_eval(metadata)
    elif endpoint_str:
        metadata = metadata[metadata.data_endpoint == endpoint_str]
    elif column:
        metadata = metadata[column]
    return metadata


def safe_apply(row, fn):
    """
    Safely apply the given function fn to the row (e.g for a pandas series apply function).
    """
    if row:
        return fn(row)
    else:
        return row

def format_metadata(orient='index'):
    """
    Load the metadata.csv file that maps metadata to each endpoint as a pandas dataframe.
    Reformat it to be json-friendly.
    """
    metadata = pd.read_csv(constants.METADATA_FILE, encoding='utf-8', index_col=constants.METADATA_INDEX)
    metadata = metadata.where((pd.notnull(metadata)), None)
    cols = set(metadata.columns.tolist())
    for col in constants.METADATA_LIST_COLS:
        if col in cols:
            metadata[col] = metadata[col].apply(lambda x: safe_apply(x, ast.literal_eval))
    for col in constants.METADATA_JSON_COLS:
        if col in cols:
            metadata[col] = metadata[col].apply(lambda x: safe_apply(x, json.loads))
    return metadata.to_dict(orient=orient)


def get_fts_endpoint(endpoint_str, key=None):
    """
    Make a request to the FTS API for the given endpoint_str, and optionally takes a key for additional json filtering.
    Return the normalized json response as a pandas dataframe if successful, or None if not.
    Example: endpoint_str = '/public/fts/flow?year=2017'
    """
    url = None
    if endpoint_str.startswith('/'):
        url = constants.FTS_API_BASE_URL + endpoint_str
    else:
        url = '/'.join([constants.FTS_API_BASE_URL, endpoint_str])
    result = requests.get(url, auth=(constants.FTS_CLIENT_ID, constants.FTS_CLIENT_PASSWORD))
    result.raise_for_status()
    result = result.json()['data']
    if result:
        if key:
            result = result[key]
        result = json_normalize(result)
    else:
        print 'Empty data from this endpoint: {}'.format(url)
        result = None
    return result

