import pandas as pd
import json

# Open the config.json file and load its contents into a variable
with open("config.json", "r") as file:
    config = json.load(file)

# Read the data from the Excel file specified in the config file
data = pd.read_excel(config["data_file_path"])

# Get the unique values in the 'indcode' column of the data
unique_values = data["indcode"].unique()

# Filter the unique values to only include those that are longer than 2 characters and do not contain a hyphen
unique_values = [
    value for value in unique_values if len(str(value)) > 2 and "-" not in str(value)
]

for value in unique_values:
    # Filter the data to only include rows where the 'indcode' column is equal to the current unique value
    filtered_data = data[data["indcode"] == value]
    # Convert the filtered data to a LaTeX table
    latex_table = filtered_data.to_latex(index=False)
    # Construct the file path for the output LaTeX table using the output folder path specified in the config file
    file_path = f"{config['output_folder_path']}/Latex Table {value}.tex"
    # Open the output file and write the LaTeX table to it
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(latex_table)
