import os
import errno
import pandas
from fuzzywuzzy import process


def fuzzy_filter(df, col, val, return_verbose=False):
    """
    Filter a pandas dataframe (df) for rows where the given column (col) has the closest fuzzy string match ratio to the given value (val). For exampl if a df had a 'Country' column and the given value is 'dominican rep', it would find 'Dominican Republic' as the closest string match and return that row of data. By default, return_verbose is false, which means just return thefiltered dataframe. If true, then also return the matched value and fuzzy string match ratio between the given value and the matched value.
    Return filtered df, matched value, and fuzzy match ratio
    """
    values = set(df[col].tolist())
    matched_value, fuzzy_match_ratio = process.extractOne(val, values)
    if return_verbose:
        return df.loc[df[col] == matched_value], matched_value, fuzzy_match_ratio
    else:
        return df.loc[df[col] == matched_value]


def safely_mkdir(directory_path):
    """
    Safely create the given directory if it doesn't already exist.
    Return whether or not the directory was successfully made (True if already existed).
    """
    success = False
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path)
            success = True
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise Exception("Could not safely create the directory: %s" % directory_path)
    else:
        success = True
    return success

def get_ordinal_number(value):
    try:
        value = int(value)
    except ValueError:
        return value

    if value % 100//10 != 1:
        if value % 10 == 1:
            ordval = u"%d%s" % (value, "st")
        elif value % 10 == 2:
            ordval = u"%d%s" % (value, "nd")
        elif value % 10 == 3:
            ordval = u"%d%s" % (value, "rd")
        else:
            ordval = u"%d%s" % (value, "th")
    else:
        ordval = u"%d%s" % (value, "th")

    return ordval


#def createCurrentDateDir(parent_dir):
#    """
#    Create a new directory with the current date (ISO format) under the given parent_dir.
#    Return whether it was successful, the full path for the new directory, and the current date string.
#    If the date directory already exists or is not successful, default to returning the parent_dir as the full path.
#    """
#    current_date_str = date.today().isoformat()
#    dir_path = os.path.join(parent_dir, current_date_str)
#    success = data_utils.safely_mkdir(dir_path)
#    if not success:
#        # TODO: handle this better
#        # Safely default to returning the parent_dir if we cannot create the dir_path
#        print('Could not create a new directory for the current date [{}], defaulting to existing parent dir'.format(current_date_str))
#        dir_path = parent_dir
#    else:
#        print('Created new raw data dir: {}'.format(dir_path))
#    return success, dir_path, current_date_str
#
#
#def updateLatestDataDir(download_path, latest_path, latest_run_date_file, current_date_str, run_date_suffix):
#    """
#    Copies all files from the given download_path into the given latest_path configured in
#    `resources/constants.py`. Appends to the latest_run_date_file with the current_date_str and run_date_suffix.
#    """
#    if not download_path or not current_date_str:
#        print('Could not copy data to the "latest" directory! Current date: [{}],data path:  {}'.format(current_date_str, download_path))
#        return
#    dir_util.copy_tree(download_path, latest_path)
#    with open(latest_run_date_file, 'a') as run_file:
#        run_file.write('{}-{}\n'.format(current_date_str, run_date_suffix))
#    return

