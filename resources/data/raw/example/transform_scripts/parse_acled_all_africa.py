import re
import pandas as pd


ACLED_FILE = 'ACLED-All-Africa-File_20170101-to-20170429.csv'

def clean_and_save():
    encoding_key = 'iso-8859-1'
    df = pd.read_csv(ACLED_FILE, encoding=encoding_key)
    print df.head()
    print df.columns
    print df.describe()
    cleaned_file = 'cleaned_{}'.format(ACLED_FILE)
    df.to_csv(cleaned_file, encoding='utf-8', index=False)
    return df, cleaned_file


# From a clean file, attempt to derive the country name 
def derive_cols(cleaned_file):
    df = pd.read_csv(cleaned_file, encoding='utf-8')
    print df.head()

    # string patterns to search for
    _digits = re.compile('\d')
    _parens = re.compile(r'^(.*?)(?: \((.*)\))?$')

    def extract_country(actor):
        country = None
        results = re.findall(_parens, actor)
        if results:
            descript, country = results[0]
            if bool(_digits.search(country)):
                # here it's probably a year, not a country
                # try to get last word of first string as proxy for region
                country = descript.split()[-1]
        return country.strip()
            
    df['extracted_country_or_region'] = df['ACTOR1'].apply(extract_country)
    print df.head()

    derived_file = 'derived_{}'.format(ACLED_FILE)
    df.to_csv(derived_file, encoding='utf-8', index=False)
    return df, derived_file


def run():
    print 'Transforming ACLED data...'
    cleaned_df, cleaned_file = clean_and_save()
    derived_df, derived_file = derive_cols(cleaned_file)
    print 'Done!'

run()
