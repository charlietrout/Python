import requests
import pandas as pd
import json

# change year parameter below to the year that you want your data from

# the part where dsource is hardcoded to acs below can be changed to the coreesponding data source abbreviation if data source of table
# which should be listed above it on the results tab on data.census.gov is not listed as American Community Survey which is typically the
# default source for a majority of the tables

# change dname to either acs1 or acs5 depending on the type of year estimate you are looking for

# change cols parameter to "group(___)" with the table name that your are getting your data from in the blank portion. Can also list
# individual variables here as well if you do not need the entire table of data

# change s_path parameter to either 'subject' or 'spp' for cols that begin with 'S' whether that be "group(S___)" or variables that
# begin with 'S'


def get_census_state_data(year, dname, cols, s_path):
    # Load the configuration file
    with open("config4.json", "r") as file:
        config = json.load(file)
    state = "45"  # Hardcode the value of state as '45'
    keyfile = config["keyfile"]  # Get the keyfile path from the configuration file
    dsource = "acs"  # Hardcode the value of dsource as 'acs'

    # construct base_url
    if cols.startswith("group(S") or cols.startswith("S"):
        base_url = f"https://api.census.gov/data/{year}/{dsource}/{dname}/{s_path}"
    elif cols.startswith("group(CP") or cols.startswith("CP"):
        base_url = f"https://api.census.gov/data/{year}/{dsource}/{dname}/cprofile"
    else:
        base_url = f"https://api.census.gov/data/{year}/{dsource}/{dname}"

    # read api key in from file
    with open(keyfile) as key:
        api_key = key.read().strip()

    # retrieve data, print output to screen
    data_url = f"{base_url}?get={cols}&for=state:{state}&key={api_key}"
    response = requests.get(
        data_url, verify=False
    )  # Send a GET request to the API URL and get the response
    popdata = response.json()  # Parse the response as JSON data

    # Create a pandas DataFrame from the data
    headers = popdata.pop(
        0
    )  # Remove the first row of data, which contains the column headers, and store it in a variable
    new_df = pd.DataFrame(
        popdata, columns=headers
    )  # Create a new DataFrame using the remaining data and the column headers

    # Filter the DataFrame to exclude columns that end in "M", "EA", or "MA"
    filtered_columns = [
        col
        for col in new_df.columns
        if not col.endswith("M") and not col.endswith("EA") and not col.endswith("MA")
    ]
    new_df = new_df[filtered_columns]

    # Replace all None values in new_df with zeros
    new_df = new_df.fillna(0)

    # Replace all instances of -888888888 and -666666666.0 in new_df with 'n/a'
    new_df = new_df.replace(["-888888888", "-666666666.0"], "n/a")

    return new_df
