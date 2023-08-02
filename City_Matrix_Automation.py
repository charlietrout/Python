import pandas as pd
import os,datetime,openpyxl
from dateutil.relativedelta import relativedelta
os.chdir("S:/LMI_Research/lmi/Shared Python Scripts/Data Functions & Files Using Them")
from Census_API_Script_City_Level import get_census_city_data

month = ""
year = ""

def paste_to_excel(df, file, worksheet, row, col, header = False):
    reader = pd.read_excel(file,engine='openpyxl')
    excelbook = openpyxl.load_workbook(file)
    with pd.ExcelWriter(file, engine='openpyxl', mode = 'a', if_sheet_exists='overlay') as writer:
        df.to_excel(writer, worksheet, index=True, header=header,startrow=row, startcol=col)

acs_years = [2012,2016,2021]

fips_to_place = {
    '00550': 'Aiken city','01360': 'Anderson city','07210': 'Bluffton town','13330': 'Charleston city','16000': 'Columbia city',
    '16405': 'Conway city','25810': 'Florence city','26890': 'Fort Mill town','29815': 'Goose Creek city','30850': 'Greenville city',
    '30985': 'Greer city','34045': 'Hilton Head Island town','45115': 'Mauldin city','48535': 'Mount Pleasant town',
    '49075': 'Myrtle Beach city','50875': 'North Charleston city','61405': 'Rock Hill city','68290': 'Spartanburg city',
    '70270': 'Summerville town','70405': 'Sumter city'
}

# Create an empty DataFrame to store the data
df = pd.DataFrame()

# Retrieve the data for the year 2012
data_2012 = get_census_city_data(
    year=acs_years[0],
    dname='acs5',
    cols='S1810_C01_001E',
    s_path='subject',
    place='00550,01360,07210,13330,16000,16405,25810,26890,29815,30850,30985,34045,45115,48535,49075,50875,61405,68290,70270,70405'
) 

# Retrieve the data for the year 2016
data_2016 = get_census_city_data(
    year=acs_years[1],
    dname='acs5',
    cols='S1810_C01_001E',
    s_path='subject',
    place='00550,01360,07210,13330,16000,16405,25810,26890,29815,30850,30985,34045,45115,48535,49075,50875,61405,68290,70270,70405'
) 

# Retrieve the data for the year 2021
data_2021 = get_census_city_data(
    year=acs_years[2],
    dname='acs5',
    cols='S1810_C01_001E',
    s_path='subject',
    place='00550,01360,07210,13330,16000,16405,25810,26890,29815,30850,30985,34045,45115,48535,49075,50875,61405,68290,70270,70405'
)

# Add the date column to the first row
df.loc[0, 0] = 'Date'

# Write the dates
date = datetime.datetime(2008,1,1)
row = 1
while date <= datetime.datetime(2023,5,1):
    df.loc[row, 0] = date.strftime('%b-%y')
    row += 1
    date += relativedelta(months=1)

# Create a list of places from the fips_to_place dictionary
sc_places = list(fips_to_place.values())

# Write the place names to the first row, starting from the second column
for col, place in enumerate(sc_places):
    df.loc[0, col + 1] = f"{place}, South Carolina"

df.loc[0, 21] = "Sum"

df.columns = df.iloc[0]

df = df.drop(df.index[0])

df.set_index('Date', inplace= True)

# Find the row number for "Jul-10"
date_row_2010 = df.index.get_loc(f'Jul-{acs_years[0]-2002}')

# Find the row number for "Jul-14"
date_row_2014 = df.index.get_loc(f'Jul-{acs_years[1]-2002}')

# Find the row number for "Jul-19"
date_row_2019 = df.index.get_loc(f'Jul-{acs_years[2]-2002}')

for col, place in enumerate(sc_places):
# Get the FIPS code for the current place
    fips_code = [code for code, name in fips_to_place.items() if name == place][0]

place_data_list_2010 = []
place_data_list_2014 = []
place_data_list_2019 = []

for col, place in enumerate(sc_places):
    fips_code = [code for code, name in fips_to_place.items() if name == place][0]

    place_data_2010 = data_2012.query(f"place == '{fips_code}'")['S1810_C01_001E'].iloc[0]
    place_data_list_2010.append(float(place_data_2010))

    place_data_2014 = data_2016.query(f"place == '{fips_code}'")['S1810_C01_001E'].iloc[0]
    place_data_list_2014.append(float(place_data_2014))

    place_data_2019 = data_2021.query(f"place == '{fips_code}'")['S1810_C01_001E'].iloc[0]
    place_data_list_2019.append(float(place_data_2019))


df.iloc[date_row_2010, 0:20] = place_data_list_2010
df.iloc[date_row_2014, 0:20] = place_data_list_2014
df.iloc[date_row_2019, 0:20] = place_data_list_2019

#Calculate the values for cells B2 to U31
for col in range(0, 20):
    for row in range(29,-1,-1):
        value = df.iloc[row + 1, col] - (((df.iloc[78, col]) - (df.iloc[30, col])) / 31)
        df.iloc[row, col] = value

# Calculate the values for cells B33 to U79
for col in range(0, 20):
    for row in range(31, 78):
        value = df.iloc[row - 1, col] + (((df.iloc[78, col] - df.iloc[30, col])) / 48)
        df.iloc[row, col] = value

# Calculate the values for cells B81 to U139
for col in range(0, 20):
    for row in range(79, 138):
        value = df.iloc[row - 1, col] + (((df.iloc[138, col] - df.iloc[78, col])) / 60)
        df.iloc[row, col] = value

# Calculate the values for cells B141 to U185
for col in range(0, 20):
    for row in range(139, 185):
        value = df.iloc[row - 1, col] + (((df.iloc[138, col] - df.iloc[78, col])) / 60)
        df.iloc[row, col] = value

# Add a formula to each cell in column V that calculates the sum of the values in columns B to U for the corresponding row
for row in range(0, len(df)):
    df.iloc[row, 20] = df.iloc[row, 0:20].sum()

# Load spreadsheet
xl = pd.ExcelFile('S:\LMI_Research\lmi\Gerald B\Labor Force Participation Rate\LAUS Data.xlsx')

# Load a sheet into a DataFrame by name
df1 = xl.parse('South Carolina LF')

df1 = df1[['Date', 'CNP']]

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

paste_to_excel(df = merged_df, file = "city_file.xlsx", worksheet = "Sheet1", row = 0, col = 0, header = True)