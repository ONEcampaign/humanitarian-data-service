import string
import os.path
import pandas as pd
from datetime import date
from distutils import dir_util

from resources import constants
from utils import data_utils, api_utils


def cleanTable1_1_Data():
    in_file_key = 'raw_asylum_country'
    out_file_key = 'asylum_country'
    file_name = constants.UNHCR_FILE_NAMES[in_file_key]
    file_path = os.path.join(constants.EXAMPLE_DERIVED_DATA_PATH, file_name)
    df = pd.read_csv(file_path, header=1, encoding='utf-8', na_values=['  -00 ', '   -00 '])
    other_cols = ['Notes', 'Misc']
    old_cols = ['Population Start 2016', 'of whom assisted by UNHCR Start 2016']
    df.drop(other_cols + old_cols, axis=1, inplace=True)
    nan_placeholder = 0
    df = df.where((pd.notnull(df)), nan_placeholder)
    numeric_cols = ['Population Mid 2016', 'of whom assisted by UNHCR Mid 2016']
    df = standardizeNumericCols(df, numeric_cols)

    # Pivot data by 'Type of population' column, and indexing on the asylum country column
    df.rename(columns={'Country/territory of asylum/residence': constants.COUNTRY_COL}, inplace=True)
    df = df[[constants.COUNTRY_COL, 'Type of population', 'Population Mid 2016', 'of whom assisted by UNHCR Mid 2016']]
    df = df.pivot(index=constants.COUNTRY_COL, columns='Type of population', values='Population Mid 2016').reset_index()

    data_path = os.path.join(constants.EXAMPLE_DERIVED_DATA_PATH, constants.UNHCR_FILE_NAMES[out_file_key])
    df.to_csv(data_path, index=False, encoding='utf-8')
    return df


def cleanTable1_2_Data():
    in_file_key = 'raw_origin_country'
    out_file_key = 'origin_country'
    file_name = constants.UNHCR_FILE_NAMES[in_file_key]
    file_path = os.path.join(constants.EXAMPLE_RAW_DATA_PATH, file_name)
    df = pd.read_csv(file_path, header=1, encoding='utf-8', na_values=['  -00 ', '   -00 '])
    other_cols = ['Notes', 'Misc']
    old_cols = ['Population Start 2016', 'of whom assisted by UNHCR Start 2016']
    df.drop(other_cols + old_cols, axis=1, inplace=True)
    nan_placeholder = 0
    df = df.where((pd.notnull(df)), nan_placeholder)
    numeric_cols = ['Population Mid 2016', 'of whom assisted by UNHCR Mid 2016']
    df = standardizeNumericCols(df, numeric_cols)

    # Pivot data by 'Type of population' column, and indexing on the origin country column
    df.rename(columns={'Origin': constants.COUNTRY_COL}, inplace=True)
    df = df[[constants.COUNTRY_COL, 'Type of population', 'Population Mid 2016', 'of whom assisted by UNHCR Mid 2016']]
    df = df.pivot(index=constants.COUNTRY_COL, columns='Type of population', values='Population Mid 2016').reset_index()

    data_path = os.path.join(constants.EXAMPLE_DERIVED_DATA_PATH, constants.UNHCR_FILE_NAMES[out_file_key])
    df.to_csv(data_path, index=False, encoding='utf-8')
    return df


def standardizeNumericCols(df, cols):
    identity = string.maketrans("", "")
    for col in cols:
        df[col] = df[col].apply(lambda x: str(x).translate(identity, " ,"))
        df[col] = pd.to_numeric(df[col], errors='coerce', downcast='unsigned')
        df[col] = df[col].astype(int)
        #df[col] = df[col].convert_objects(convert_numeric=True)
    return df


def run():
    print cleanTable1_1_Data()
    print cleanTable1_2_Data()

    print 'Done!'


if __name__ == "__main__":
    run()
