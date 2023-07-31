import requests,csv
import configparser

# Create a ConfigParser object
config = configparser.ConfigParser()

# Read the configuration file
config.read('config.ini')

# Get the file path from the configuration file
keyfile = config.get('Paths', 'keyfile')

# Set parameters for the Census API request
year = '2019'
dsource = 'pep'
dname = 'population'
cols = 'NAME,POP,DATE_DESC'
state = '45'
county = '*'
dcode = '2,12'
outfile = 'pop2019_sc_counties.txt'
base_url = f'https://api.census.gov/data/{year}/{dsource}/{dname}'

# Read the Census API key from the keyfile
with open(keyfile) as key:
    api_key = key.read().strip()

# Construct the data URL for the Census API request
data_url = f'{base_url}?get={cols}&DATE_CODE={dcode}&for=county:{county}\&in=state:{state}&key={api_key}'

# Send a GET request to the Census API and get the response
response = requests.get(data_url, verify = False)
popdata = response.json()

# Print each record in the population data
for record in popdata:
    print(record)
    
# Write the population data to a CSV file
with open(outfile, 'w', newline = '') as writefile:
    writer = csv.writer(writefile, quoting = csv.QUOTE_ALL, delimiter=',')
    writer.writerow(popdata)