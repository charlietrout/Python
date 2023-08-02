import requests
import json
import pandas
import os
from time import sleep
import sys
import datetime
import openpyxl
import re

# Load the config file
with open('config8.json', 'r') as f:
    config = json.load(f)

#def city():

#####This script has the ability to handle LAUS, CES, QCEW, and OEWS
#####If you are using substate data, it will identify the area type from the series id you provide and return the respective data for all areas of that type in South Carolina (or any other state if you correctly
#####perform some minor alterations).

#####QCEW issues: The most important guidence documentation under the linke https://download.bls.gov/pub/time.series/ is missing QCEW. That means I do not have a comprehensive list of available geographic
#####areas or the appropriate syntax for all of the NAICS codes. 

#####OEWS is the most complicated data to request, because the series id is not shown when you look up the data on BLS. See the links below for additional info:
#####https://download.bls.gov/pub/time.series/oe/oe.txt
#####list of the available options are in the digital file folder available:
#####https://download.bls.gov/pub/time.series/oe/

#####Sample OEWS Series ID search:
#from example: series = ['OEUM000040000000000000001']
#         "prefix"     area    NAICS  industry      datatype
#series = ['WMU     M00004   000000    000000        01']
#Make sure you check measure for the different values. Area is selected for you as the list of available locations in SC
series = ['LAUCT451600000000006','LAUCT451600000000005','LAUCT451600000000004','LAUCT451600000000003']

#######set working directory to where you want your excel file saved
#######if you are saving a workbook in an existing file, the directory is the location of that file

# Set the working directory from the config file
os.chdir(config['working_directory'])

#######if this is used too much, then individuals need to create more keys. Each key has a 500 requests per day limit. If we want to be clever about this we can add everyone's keys to a pool of keys and then 
#######run a random number generator to select which key to use.

# Set the BLS API key from the config file
BLS_API_KEY = config['bls_api_key']

#######Series must be from the same data source, meaning the first two letters should be the same for all series codes, for example all LAUS or all CES. I recommend getting the series codes directly from the 
#######BLS data tool and cross reference some of your results to make sure they match the data you would like. Pay particular attention to seasonally adjusted and unadjusted differences. 
#######The area type is determined by the first id entered here. Enter the labels in the same order that you enter the series id numbers, or your output file labels will be jumbled around.
#######See additional details on series code formats here: https://www.bls.gov/help/hlpforma.htm
#series = ['ENU4501720010']

labels = ['laborforce','emplab','unemp','unemprate']
#######Name your base output files and worksheet.
outputfile = 'LAUS Data test.xlsx'
worksheetname = 'City LF'
########Enter starting year, the endyear function selects the current year. Please make sure the timeframe is covered by your data request. Not all substate data has the same start date, so 
########error catching for the time frame is not always implemented. 
########API LIMIT FOR ONE REQUEST IS TWENTY YEARS.
startyear = '2008'
endyear = '2023'
#endyear = str(datetime.datetime.today().year)
########Enter six digit NAICS codes as a list object filled with strings, NAICS must be 6 digits if using CES. NAICS will be ignored if your series do not accept industry codes. Enter '000000' if working in CES and 
########you would like all data within a supersector (or data is not broken down to more detail than supersector). OEWS only available at best to the 2 digit level of detail and only at the state level.
NAICS = ['000000']
########CES data requires supersector, supersector and NAICS must be the same length and corresponding values must be compatible. Many supersectors are only available as '000000'.
NAICS_supersect = []
########Enter six digit SOC codes as a list object filled with strings that are six digit numbers. SOC is only used for OEWS.
SOC = ['000000']
####South Carolina is 45, only change if you are looking into other states. You will need to point to an alternative area_df file that is filtered from the full list of local areas down to the respective state.
statecode = '45'
####You may want to pass additional parameters, though I believe they should mostly be included in the series numbers. Enter parameters here as a dictionary type with string values and the key as the parameter label. 
####This should be empty brackets if you do not want any additional parameters. 
####Some example uses would be requesting annual data or calculations such as percent change or net change (available for intervals of one, three, six, and twelve months) use:
####{'calculations':'true','annualaverage':'true'}
additionalparams = {}
####If you enter 'calculations':'true' as an additional parameter, the default is to return all 4 interval types (1, 3, 6, and 12 month periods) for net and percent change. Enter the periods you want excluded below
####for each type. If you would like all percent change excluded for example, then one of the dict entries should be 'pct_changes':['1','3','6','12']
exclude_calculations = {}


# Check if the lengths of the labels and series lists are equal
if not len(labels)==len(series):
    print('Label and Series must be the same length')
    sys.exit(0)

# Check if any of the series IDs contain the substring 'SM'
if any(['SM' in codes for codes in series]):
    if not all(['SM' in codes for codes in series]):
        print("In your series search, please limit your request to the same series of data")
        sys.exit()
    if any([len(codes)!=20 for codes in series]):
        print('One or more of your series codes is the incorrect length')
        sys.exit()
    datatype = 'CES'
    
if any(['EN' in codes for codes in series]):
    datatype = 'QCEW'

if any(['LA' in codes for codes in series]):
    if not all(['LA' in codes for codes in series]):
        print("In your series search, please limit your request to the same series of data.")
        sys.exit()
    # If any of the series IDs have an incorrect length, print an error message and exit the script
    if any([len(codes)!=20 for codes in series]):
        print('One or more of your series codes is the incorrect length')
        sys.exit()
    datatype = 'LAUS'

if any(['OE' in codes for codes in series]):
    # If not all of the series IDs contain the substring 'OE', print an error message and exit the script
    if not all(['OE' in codes for codes in series]):
        print("In your series search, please limit your request to the same series of data.")
        sys.exit()
    datatype = 'OEWS'

def set_month(x):
    if 'Q' in x:
        # Extract digits from x, convert them to an integer, multiply by 3, subtract 2, and return as a string
        x = int(re.sub('[^0-9]','',x))
        return str((x*3)-2)
    if 'M' in x:
        # Extract digits from x and return them as a string
        x = re.sub('[^0-9]','',x)
        return x
    # If x does not contain a 'Q' or a 'M', return '01'
    else:
        return '01'



####start series specific function

#establish area df, codes with labels


if datatype == 'OEWS':
    full_area_codes = pandas.read_excel('SC_area_reference.xlsx', sheet_name= 'OEWS', converters={'area_code':str})
if datatype == 'CES':
    full_area_codes = pandas.read_excel('SC_area_reference.xlsx', sheet_name= 'CES')
if datatype == 'LAUS':
    area_df = pandas.read_excel('SC_area_reference.xlsx', sheet_name='LAUS')
    # Extract digits from the first element in the series list and select rows from area_df that contain this substring in the 'area_code' column
    area_example = [re.sub('[A-Z]',"",series[0])[0:13]][0]
    ref_area = area_df[area_df["area_code"].str.contains(area_example)]['area_code'].astype('string').values
    # Select rows from area_df that contain the first two characters of ref_area in the 'area_code' column
    full_area_codes = area_df[area_df["area_code"].str.contains(ref_area[0][0:2])]
if datatype == 'QCEW':
    full_area_codes = pandas.read_excel('SC_area_reference.xlsx', sheet_name='LAUS')
    full_area_codes = full_area_codes[full_area_codes["area_code"].str.contains('CN')]
    full_area_codes['area_code'] = [re.sub('[A-Z]','',code)[0:5] for code in full_area_codes['area_code']]
    # Extract characters 8 to 11 from each element in the series list
    datacodes = [code[8:11] for code in series]

# Select only the 'area_code' and 'area_text' columns from full_area_codes
full_area_codes = full_area_codes[['area_code','area_text']]

####prefix
prefix = [pre[0:3] for pre in series]


####datatype comes from Series id
if not datatype=='QCEW':
    datacodes = [code[-2:] for code in series]


# Define a dictionary that maps NAICS codes to supersector codes
supersector_dict = {'11':'10','21':'10','23':'20','31':'30','32':'30','33':'30','42':'40','44':'40','45':'40',"48":'40','49':'40','22':'40','51':'50',"52":'55','53':'55','54':'60','55':'60','56':'60','61':'65',
                    '62':'65','71':'70','72':'70','81':'80','91':'90','92':'90','93':'90','00':'00'}
#####Supersector is autopopulated when not provided. Ideally you have already populated supersector, because this approach is less than ideal. Often substate data is only available at the supersector level, meaning
#####the supersector is more important to enter. 
supersector_code = []
if datatype == 'CES' and NAICS and not NAICS_supersect:
    for codes in NAICS:
        # Check if the first two characters of codes are in the supersector_dict dictionary
        if codes[0:2] in supersector_dict:
                # If they are, append the value associated with these characters to the NAICS_supersect list
                NAICS_supersect.append(supersector_dict[codes[0:2]])
            
# Check if the datatype is CES and if the lengths of the supersector_code and NAICS lists are not equal
if datatype == 'CES' and len(supersector_code)!=len(NAICS): 
    NAICS = []
    for codes in supersector_code:
        NAICS.append('000000')

# Check if NAICS is empty and if the datatype is QCEW
if not NAICS and datatype == 'QCEW':
    # If it is, set NAICS to a list of substrings extracted from elements in the series list
    NAICS = [ind[11:] for ind in series]

# Check if the datatype is OEWS and if NAICS is empty
if datatype == 'OEWS' and not NAICS:
    # If it is, set NAICS to a list containing a single element "110000"
    NAICS = ['110000']

def blsapi(seriesn, exclude_calcs = {}, id_columns = {},additionalfields={}):
    # Set headers for the request
    headers = {'Content-type': 'application/json'}
    # Set parameters for the request
    params = {'registrationkey':BLS_API_KEY,"seriesid": seriesn,"startyear":startyear,'endyear':endyear}
    # Update parameters with additional fields if provided
    if additionalfields:
        params.update(additionalfields)
    # Convert parameters to JSON format
    data = json.dumps(params)
    try:
        # Send a POST request to the BLS API
        p = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=data, headers=headers, verify=False)
        sleep(1)
        # Load the response text as JSON data
        json_data = json.loads(p.text)
    except Exception as e:
        # Print an error message if the request was unsuccessful
        print('One of your requests was unsuccessful. the Series ID '+seriesn+' failed with exception: '+str(e))
    # Create an empty DataFrame to store the results
    return_obj = pandas.DataFrame()
    if json_data['message'] and 'not exist' in json_data['message'][1]:
        return 'One or more of your Series do not Exist'
    indices = list(range(0,len(seriesn)))
    for index, label in zip(indices, labels):
        # Create a DataFrame from the data for the current series
        loop_obj = pandas.DataFrame(json_data['Results']['series'][index]['data'],columns=['year','period','periodName','value'])
        # Check if calculations are not requested or if the DataFrame is empty or if calculations are set to false
        if 'calculations' not in params or loop_obj.empty or params['calculations']=='false':
            # Rename the value column to the label of the current series
            loop_obj.columns=list(loop_obj.columns[0:3])+[label]
            if return_obj.empty:
                # If it is empty, set it to the current DataFrame sorted by year and period
                return_obj = loop_obj.sort_values(by = ['year','period'])               
            else:
                # If it is not empty, merge it with the current DataFrame sorted by year and period on year, period, and periodName columns using an outer join
                return_obj = pandas.merge(return_obj, loop_obj.sort_values(by = ['year','period']), on = ['year', 'period', 'periodName'], how='outer')
        else:
            # Loop through each row of data for the current series
            for i, val in enumerate(json_data['Results']['series'][index]['data']):
                # Check if calculations are not present in the current row and continue to the next row if they are not present
                if 'calculations' not in json_data['Results']['series'][index]['data'][i]:
                    continue
                row = json_data['Results']['series'][index]['data'][i]['calculations']['net_changes']
                # Convert the row to a dictionary with lists as values
                row = {k:[v] for k,v in row.items()}
                # Check if net_df is not defined yet
                if 'net_df' not in locals():
                    # If it is not defined, create it from the current row
                    net_df = pandas.DataFrame(row)
                else:
                    # If it is defined, concatenate it with a DataFrame created from the current row
                    net_df = pandas.concat([net_df, pandas.DataFrame(row)], ignore_index=True)
                # Get the percent changes calculations for the current row
                row = json_data['Results']['series'][index]['data'][i]['calculations']['pct_changes']
                # Convert the row to a dictionary with lists as values
                row = {k:[v] for k,v in row.items()}
                if 'pct_df' not in locals():
                    pct_df = pandas.DataFrame(row)
                else:
                    pct_df = pandas.concat([pct_df, pandas.DataFrame(row)], ignore_index = True)
            # Rename columns of net_df by adding '_net' suffix to each column name
            net_df.columns = [str(col) + '_net' for col in net_df.columns]
            # Rename columns of pct_df by adding '_pct' suffix to each column name
            pct_df.columns = [str(col) + '_pct' for col in pct_df.columns]
            if exclude_calcs['net_changes']:
                exclude_cols = [str(col) + '_net' for col in exclude_calcs['net_changes']]
            if exclude_calcs['pct_changes']:
                if 'exclude_cols' not in locals():
                    exclude_cols = [str(col) + '_pct' for col in exclude_calcs['pct_changes']]
                else:
                    exclude_cols = exclude_cols + [str(col) + '_pct' for col in exclude_calcs['pct_changes']]
            calcs_df =  pandas.concat([net_df,pct_df], axis = 1)
            # Delete net_df and pct_df                         
            del net_df
            del pct_df
            # Concatenate loop_obj and calcs_df along columns axis
            loop_obj = pandas.concat([loop_obj,calcs_df],axis=1)
            # Check if exclude_cols is defined
            if 'exclude_cols' in locals():
                # Loop through each column to exclude
                for col in exclude_cols:
                    try:
                        # Try to drop the column from loop_obj
                        loop_obj = loop_obj.drop(col, axis=1)
                    except:
                        # Print an error message if the column is not available in the series requested
                        print('The excluded columne '+ col + ' is not available in the series you requested')
            # Sort loop_obj by year and period
            loop_obj = loop_obj.sort_values(by = ['year','period'])
            # Rename columns of loop_obj by adding label as prefix to each column name after the first three columns
            loop_obj.columns=list(loop_obj.columns[0:3])+[label] + [label + '_' + str(col) for col in loop_obj.columns[4:]]
            if return_obj.empty:
                # If it is empty, set it to loop_obj
                return_obj = loop_obj
            else:
                # If it is not empty, merge it with loop_obj on year, period, and periodName columns using an outer join
                return_obj = pandas.merge(return_obj, loop_obj, on = ['year', 'period', 'periodName'], how='outer')
    if not return_obj.empty:
        # Rename the 'period' column to 'month'
        return_obj = return_obj.rename(columns={'period':'month'})
        # Apply the set_month function to the 'month' column
        return_obj['month'] = return_obj['month'].apply(set_month)
        # Convert the 'year' column to a datetime object and assign it to the 'year' column
        return_obj['year'] = pandas.to_datetime(return_obj.assign(day = 1).loc[:,['year','month','day']])
        # Rename the 'year' column to 'Date'
        return_obj = return_obj.rename(columns={'year':'Date'})
        # Drop the 'month' and 'periodName' columns
        return_obj = return_obj.drop(['month','periodName'],axis=1)
        # Loop through each key-value pair in id_columns
        for key,value in id_columns.items():
            # Insert a new column with the given key and value at the beginning of the DataFrame
            return_obj.insert(0, key, value)
    return return_obj

# Loop over rows in the full_area_codes DataFrame
for area in full_area_codes.iterrows():
    # Set the 'Area' key in the id_col dictionary to the value of the 'area_text' column for the current row
    id_col = {'Area':str(area[1]['area_text'])}
    if datatype == 'LAUS':
        # If the datatype is 'LAUS', generate a list of request IDs by concatenating elements from the prefix and datacodes lists with the value of the 'area_code' column for the current row
        request_ids = [pre + str(area[1]['area_code']) + code for pre, code in zip(prefix,datacodes)]
        if 'return_df' not in locals() and 'return_df' not in globals():
            # If return_df does not exist, call the blsapi function with the generated request IDs and set return_df to the returned DataFrame
            return_df = blsapi(request_ids, exclude_calcs = exclude_calculations, id_columns = id_col,additionalfields=additionalparams)
        else:
            # If return_df does exist, call the blsapi function with the generated request IDs and concatenate the returned DataFrame with return_df
            request_df = blsapi(request_ids, exclude_calcs = exclude_calculations, id_columns = id_col,additionalfields=additionalparams)
            return_df = pandas.concat([return_df,request_df])
    else:
        indices = list(range(0, len(list(NAICS))))
        for index,inds in zip(indices,NAICS):
            if datatype == 'QCEW':
                # If the datatype is 'QCEW', update the 'NAICS' key in the id_col dictionary and generate a list of request IDs by concatenating elements from the prefix 
                # and datacodes lists with the value of the 'area_code' column for the current row and inds
                id_col.update({'NAICS':inds})
                request_ids = [pre + str(area[1]['area_code']) + code + inds for pre, code in zip(prefix,datacodes)]
            if datatype == 'CES':
                # If the datatype is 'CES', update the 'NAICS' key in the id_col dictionary and generate a list of request IDs by concatenating elements from the prefix, datacodes, 
                # and supersector_code lists with the value of the 'area_code' column for the current row and inds
                id_col.update({'NAICS':NAICS_supersect[index] + inds})
                request_ids = [pre + str(area[1]['area_code']) + supsect + inds + code for pre, code, supsect in zip(prefix,datacodes,supersector_code)]
            if datatype == 'CES' or datatype == 'QCEW':
                if 'return_df' not in locals() and 'return_df' not in globals():
                    return_df = blsapi(request_ids, exclude_calcs = exclude_calculations, id_columns = id_col,additionalfields=additionalparams)
                else:
                    request_df = blsapi(request_ids, exclude_calcs = exclude_calculations, id_columns = id_col,additionalfields=additionalparams)
                    return_df = pandas.concat([return_df,request_df])
            if datatype == 'OEWS':
                # If it is, update several keys in dictionaries and check if a SOC variable exists
                id_col.update({'NAICS':inds})
                additionalparams.update({'annualaverage':'true',"aspects":'true',"catalog":'true','calculations':'false'})
                if not SOC:
                    SOC = ['000000']
                for occupation in SOC:
                    # Update a key in a dictionary and generate a list of request IDs by concatenating elements from lists with values from dictionaries and columns
                    id_col.update({'SOC':occupation})
                    request_ids = [pre + str(area[1]['area_code'])+inds+occupation+dc1 for pre, dc1 in zip(prefix, datacodes)]
                    # Check if a return_df variable exists
                    if 'return_df' not in locals() and 'return_df' not in globals():
                        # If return_df does not exist, call the blsapi function with the generated request IDs and set return_df to the returned DataFrame if it is not a string
                        temp_df = blsapi(request_ids, exclude_calcs = exclude_calculations, id_columns = id_col,additionalfields=additionalparams)
                        if isinstance(temp_df, str):
                            continue
                        return_df = temp_df
                    else:
                        # If return_df does exist, call the blsapi function with the generated request IDs and concatenate the returned DataFrame with return_df if it is not a string
                        temp_df = blsapi(request_ids, exclude_calcs = exclude_calculations, id_columns = id_col,additionalfields=additionalparams)
                        if isinstance(temp_df, str):
                            continue
                        return_df = pandas.concat([return_df,temp_df])
    return_df = return_df.drop_duplicates(ignore_index=True)

# Load the Excel file using the file path from the config file
xl = pandas.ExcelFile(config['city_file_path'])

# Load a sheet into a DataFrame by name
df1 = xl.parse('Sheet1')

df1 = df1[['Date', 'State #']]

# Convert the 'Date' column in return_df to a datetime object
return_df['Date'] = pandas.to_datetime(return_df['Date'])

# Define the input and output date formats
input_format = '%b-%y'

# Convert the 'Date' column to a datetime object with the desired format
df1['Date'] = pandas.to_datetime(df1['Date'], format=input_format)

merged_df = pandas.merge(df1, return_df, on='Date', how='inner')

# Load a sheet into a DataFrame by name
df2 = xl.parse('Sheet1')

df2 = df2[['Date', 'Aiken city, South Carolina', 'Anderson city, South Carolina', 'Bluffton town, South Carolina', 'Charleston city, South Carolina', 
           'Columbia city, South Carolina', 'Conway city, South Carolina', 'Florence city, South Carolina', 'Fort Mill town, South Carolina', 
           'Goose Creek city, South Carolina', 'Greenville city, South Carolina', 'Greer city, South Carolina', 'Hilton Head Island town, South Carolina', 
           'Mauldin city, South Carolina', 'Mount Pleasant town, South Carolina', 'Myrtle Beach city, South Carolina', 'North Charleston city, South Carolina', 
           'Rock Hill city, South Carolina', 'Spartanburg city, South Carolina', 'Summerville town, South Carolina', 'Sumter city, South Carolina', 'State #']]

# Convert the 'Date' column to a datetime object with the desired format
df2['Date'] = pandas.to_datetime(df2['Date'], format=input_format)

# Melt df2 to transform the city/town columns into rows
df2_melted = pandas.melt(df2, id_vars=['Date', 'State #'], var_name='Area', value_name='Population')

# Remove ", SC" and ", South Carolina" from the column names in merged_df
merged_df['Area'] = merged_df['Area'].str.replace(', SC', '')

# Remove ", SC" and ", South Carolina" from the 'Area' column in df2_melted
df2_melted['Area'] = df2_melted['Area'].str.replace(', South Carolina', '')

# Merge return_df and df2 on the 'Date' and 'State #' columns
merged_df1 = pandas.merge(df2_melted, merged_df, on=['Date', 'State #', 'Area'], how='inner')

# Load the Excel file using the file path from the config file
xl1 = pandas.ExcelFile(config['file_path'])

# Load a sheet into a DataFrame by name
df3 = xl1.parse('Sheet1')

df3 = df3[['Date', 'State #', 'Ratio']]

# Convert the 'Date' column to a datetime object with the desired format
df3['Date'] = pandas.to_datetime(df3['Date'], format=input_format)

merged_df2 = pandas.merge(df3, merged_df1, on=['Date', 'State #'], how='inner')

# Add a new 'CNP' column to merged_df2 that multiplies the 'Ratio' column by the 'Population' column
merged_df2 = merged_df2.assign(CNP=merged_df2['Ratio'] * merged_df2['Population'])

merged_df2['laborforce'] = pandas.to_numeric(merged_df2['laborforce'], errors='coerce')

# Add a new 'LF/Adjusted' column to merged_df2 that divides the 'laborforce' column by the 'CNP' column
merged_df2 = merged_df2.assign(LF_Adjusted=merged_df2['laborforce'] / merged_df2['CNP'])

# Add a new 'LF x2' column to merged_df2 that divides the 'laborforce' column by the 'Population' column
merged_df2 = merged_df2.assign(LF_x2=merged_df2['laborforce'] / merged_df2['Population'])

# Add a new column named 'LF_X3' to merged_df2 that multiplies the values in the 'LF_x2' column by 100
merged_df2 = merged_df2.assign(LF_X3=merged_df2['LF_x2']*100)

# Convert the 'emplab' column in merged_df2 to a numeric data type, coercing any errors
merged_df2['emplab'] = pandas.to_numeric(merged_df2['emplab'], errors='coerce')

# Add a new column named 'emppopratio' to merged_df2 that divides the values in the 'emplab' column by the values in the 'Population' column and multiplies the result by 100
merged_df2 = merged_df2.assign(emppopratio=merged_df2['emplab'] / merged_df2['Population']*100)

# Rename the 'CNP' column to 'State #'
merged_df2 = merged_df2.rename(columns={'State #': 'State Population'})

# Rename the 'CNP' column to 'State #'
merged_df2 = merged_df2.rename(columns={'Area': 'Areaname'})

# Add a new 'CNP' column to merged_df2 that multiplies the 'Ratio' column by the 'Population' column
merged_df2 = merged_df2.assign(LFPR=merged_df2['LF_X3'])

merged_df2 = merged_df2.rename(columns={'LF_Adjusted': 'LF/Adjusted'})

merged_df2 = merged_df2.rename(columns={'LF_x2': 'LF x2'})

merged_df2 = merged_df2.rename(columns={'LF_X3': 'LF X3'})

# Define the desired column order
column_order = ['Areaname', 'Date', 'laborforce', 'emplab', 'unemp', 'unemprate', 'State Population', 'Population', 'Ratio', 'CNP', 'LF/Adjusted', 'LF x2', 'LF X3', 'LFPR', 'emppopratio']

# Reorder the columns of merged_df2
merged_df2 = merged_df2[column_order]

# Check if the output file exists
if not os.path.isfile(outputfile):
    # If the output file does not exist, write the merged_df2 DataFrame to an Excel file with the specified sheet name and without including the index
    merged_df2.to_excel(outputfile,sheet_name=worksheetname, index = False)
else:
    # If the output file does exist, read it into a DataFrame using the openpyxl engine
    reader = pandas.read_excel(outputfile,engine='openpyxl')
    # Load the output file into an openpyxl workbook
    excelbook = openpyxl.load_workbook(outputfile)
    # Create an ExcelWriter object in append mode with the openpyxl engine and with the option to replace existing sheets
    with pandas.ExcelWriter(outputfile,mode='a',engine='openpyxl',if_sheet_exists='replace') as writer:
        # Write the merged_df2 DataFrame to the workbook using the specified sheet name and without including the index
        merged_df2.to_excel(writer,worksheetname,index=False)