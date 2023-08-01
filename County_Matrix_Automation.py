import pandas as pd
import os
import openpyxl
import datetime
import json
from dateutil.relativedelta import relativedelta
from get_census_county_data import get_census_county_data

# Load the configuration file
with open('config7.json', 'r') as f:
    config = json.load(f)

# Get the values from the configuration file
working_directory = config['working_directory']
excel_file = config['excel_file']

# Set the working directory
os.chdir(working_directory)

#month = ""
#year = ""

def paste_to_excel(df, file, worksheet, row, col, header = False):
    reader = pd.read_excel(file,engine='openpyxl')
    excelbook = openpyxl.load_workbook(file)
    with pd.ExcelWriter(file, engine='openpyxl', mode = 'a', if_sheet_exists='overlay') as writer:
        df.to_excel(writer, worksheet, index=True, header=header,startrow=row, startcol=col)

# Define a list of years for which to retrieve data
acs_years = [2012,2016,2021]

# Define a dictionary that maps FIPS codes to county names
fips_to_county = {
    '001': 'Abbeville','003': 'Aiken','005': 'Allendale','007': 'Anderson','009': 'Bamberg','011': 'Barnwell','013': 'Beaufort',
    '015': 'Berkeley','017': 'Calhoun','019': 'Charleston','021': 'Cherokee','023': 'Chester','025': 'Chesterfield','027': 'Clarendon',
    '029': 'Colleton','031': 'Darlington','033': 'Dillon','035': 'Dorchester','037': 'Edgefield','039': 'Fairfield','041': 'Florence',
    '043': 'Georgetown','045': 'Greenville','047': 'Greenwood','049': 'Hampton','051': 'Horry','053':'Jasper', '055':'Kershaw', 
    '057':'Lancaster', '059':'Laurens', '061':'Lee', '063':'Lexington', '065':'McCormick', '067':'Marion', '069':'Marlboro', 
    '071':'Newberry', '073':'Oconee', '075':'Orangeburg', '077':'Pickens', '079':'Richland', '081':'Saluda', '083':'Spartanburg', 
    '085':'Sumter', '087':'Union', '089':'Williamsburg', '091': 'York'
}

# Create an empty DataFrame to store the data
df = pd.DataFrame()

# Retrieve the data for the year 2012
data_2012 = get_census_county_data(
    year=acs_years[0],
    dname='acs5',
    cols='S1810_C01_001E',
    s_path='subject',
    county='*'
) 

# Retrieve the data for the year 2016
data_2016 = get_census_county_data(
    year=acs_years[1],
    dname='acs5',
    cols='S1810_C01_001E',
    s_path='subject',
    county='*'
) 

# Retrieve the data for the year 2021
data_2021 = get_census_county_data(
    year=acs_years[2],
    dname='acs5',
    cols='S1810_C01_001E',
    s_path='subject',
    county='*'
)

# Add the date column to the first row
df.loc[0, 0] = 'Date'

# Write the dates
date = datetime.datetime(2008,1,1)
row = 1
while date <= datetime.datetime(2023,6,1):
    # Write the current date to the DataFrame in the format 'MMM-YY'
    df.loc[row, 0] = date.strftime('%b-%y')
    row += 1
    # Increment the date by one month
    date += relativedelta(months=1)

# Create a list of counties from the fips_to_county dictionary
sc_counties = list(fips_to_county.values())

# Write the county names to the first row, starting from the second column
for col, county in enumerate(sc_counties):
    df.loc[0, col + 1] = f"{county} County"

# Add a "Sum" column to the DataFrame
df.loc[0, 47] = "Sum"

# Set the column names of the DataFrame to be the values in the first row
df.columns = df.iloc[0]

# Drop the first row of the DataFrame
df = df.drop(df.index[0])

# Set the index of the DataFrame to be the 'Date' column
df.set_index('Date', inplace= True)

# Find the row number for "Jul-10"
date_row_2010 = df.index.get_loc(f'Jul-{acs_years[0]-2002}')

# Find the row number for "Jul-14"
date_row_2014 = df.index.get_loc(f'Jul-{acs_years[1]-2002}')

# Find the row number for "Jul-19"
date_row_2019 = df.index.get_loc(f'Jul-{acs_years[2]-2002}')

for col, place in enumerate(sc_counties):
# Get the FIPS code for the current place
    fips_code = [code for code, name in fips_to_county.items() if name == county][0]

# Create empty lists to store data for each year
county_data_list_2010 = []
county_data_list_2014 = []
county_data_list_2019 = []

# Loop over each county in the list of counties
for col, county in enumerate(sc_counties):
    # Get the FIPS code for the current county
    fips_code = [code for code, name in fips_to_county.items() if name == county][0]

    # Retrieve data for the current county for the year 2010
    county_data_2010 = data_2012.query(f"county == '{fips_code}'")['S1810_C01_001E'].iloc[0]
    # Append the data to the list for 2010
    county_data_list_2010.append(float(county_data_2010))

    county_data_2014 = data_2016.query(f"county == '{fips_code}'")['S1810_C01_001E'].iloc[0]
    county_data_list_2014.append(float(county_data_2014))

    county_data_2019 = data_2021.query(f"county == '{fips_code}'")['S1810_C01_001E'].iloc[0]
    county_data_list_2019.append(float(county_data_2019))

# Write data from the lists to specific rows of the DataFrame using the iloc method
df.iloc[date_row_2010, 0:46] = county_data_list_2010
df.iloc[date_row_2014, 0:46] = county_data_list_2014
df.iloc[date_row_2019, 0:46] = county_data_list_2019

# Write the formula to cells B2 to AU31
for col in range(0, 47):
    for row in range(29,-1,-1):
        value = df.iloc[row + 1, col] - (((df.iloc[78, col]) - (df.iloc[30, col])) / 31)
        df.iloc[row, col] = value

# Calculate the values for cells B33 to AU79
for col in range(0, 47):
    for row in range(31, 78):
        value = df.iloc[row - 1, col] + (((df.iloc[78, col] - df.iloc[30, col])) / 48)
        df.iloc[row, col] = value

# Calculate the values for cells B81 to AU139
for col in range(0, 47):
    for row in range(79, 138):
        value = df.iloc[row - 1, col] + (((df.iloc[138, col] - df.iloc[78, col])) / 60)
        df.iloc[row, col] = value

# Calculate the values for cells B141 to AU185
for col in range(0, 47):
    for row in range(139, 186):
        value = df.iloc[row - 1, col] + (((df.iloc[138, col] - df.iloc[78, col])) / 60)
        df.iloc[row, col] = value

# Add a formula to each cell in column V that calculates the sum of the values in columns B to U for the corresponding row
for row in range(0, len(df)):
    df.iloc[row, 46] = df.iloc[row, 0:46].sum()

# Load spreadsheet
xl = pd.ExcelFile(excel_file)

# Load a sheet into a DataFrame by name
df1 = xl.parse('South Carolina LF')

# Select only the 'Date' and 'CNP' columns from the DataFrame
df1 = df1[['Date', 'CNP']]

# Change the data type of the 'Date' column to object
df1['Date'] = df1['Date'].astype('object')

# Change the format of the dates in df1 to match the format of the dates in df
df1['Date'] = df1['Date'].apply(lambda x: x.strftime('%b-%y'))

# Merge df1 and df on the 'Date' column
merged_df = pd.merge(df1, df, on='Date', how='inner')

# Rename the 'CNP' column to 'State #'
merged_df = merged_df.rename(columns={'CNP': 'State #'})

# Set the index to be the 'Date' column
merged_df.set_index('Date', inplace=True)

# Create a new DataFrame with the desired column order
new_df = pd.DataFrame(columns=merged_df.columns[1:].tolist() + [merged_df.columns[0]])

# Copy the data from merged_df to new_df
for col in merged_df.columns:
    new_df[col] = merged_df[col]

# Set merged_df to be equal to new_df
merged_df = new_df

# Calculate the ratio of the 'State #' column to the 'Sum' column
ratio = merged_df['State #'].div(merged_df['Sum'])

# Add the ratio as a new column to the DataFrame
merged_df['Ratio'] = ratio

paste_to_excel(df = merged_df, file = "file.xlsx", worksheet = "Sheet1", row = 0, col = 0, header = True)