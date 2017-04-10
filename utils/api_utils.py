import json
import os.path
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
            # TODO: also extract metadata (read first line of file) an return it
        elif has_metadata:
            result = pd.read_csv(file_path, encoding='utf-8', header=1)
            # TODO: also extract metadata (read first line of file) an return it
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
            with open(file_path, 'r') as data_file:
                metadata_str = data_file.readline().strip()
                if metadata_str.startswith('#{') and metadata_str.endswith('}'):
                    metadata = json.loads(metadata_str[1:])
                    metadata["source_org"] = constants.DATA_SOURCES[metadata["source_key"]]

    return success, result, metadata

