import pandas as pd
import os
import json

# Load the configuration file
with open("config2.json", "r") as file:
    config = json.load(file)

# Get the folder path and data file path from the configuration file
folder_path = config["folder_path"]
data_file_path = config["data_file_path"]

os.chdir(
    folder_path
)  # Change the current working directory to the specified folder path
data = pd.read_excel(data_file_path)  # Read the data from the Excel file
column_name = "indcode"
unique_values = data[
    column_name
].unique()  # Get the unique values in the specified column of the data

# Filter the unique values to only include those that are longer than 2 characters and do not contain a hyphen
unique_values = [
    value for value in unique_values if len(str(value)) > 2 and "-" not in str(value)
]

for value in unique_values:
    filtered_data = data[
        data[column_name] == value
    ]  # Filter the data to only include rows where the specified column is equal to the current unique value
    file_name = f"{value}.xlsx"  # Construct the file name for the output file
    filtered_data.to_excel(
        file_name, index=False
    )  # Save the filtered data to an Excel file
