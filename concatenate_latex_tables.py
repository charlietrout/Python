import os
import json

# Load the configuration file
with open('config.json', 'r') as file:
    config = json.load(file)

# Get the directory path from the configuration file
directory = config['directory_path']

latex_code =""  # Initialize an empty string to store the LaTeX code
for filename in os.listdir(directory):
    if filename.endswith(".tex"):  
        file_path = os.path.join(directory, filename)  # Construct the full file path
        with open(file_path, "r",encoding="utf-8") as file:  # Open the file for reading
            table_content = file.read()  # Read the contents of the file
        table_code = f"""
        \\begin{{table}}
            \\centering
            \\caption{{Table Title}}
            \\label{{table:{filename}}}
        \\end{{table}}  
        """  # Construct the LaTeX table code
        latex_code += table_code  # Append the table code to the LaTeX code string

# Get the output file path from the configuration file
output_file_path = config['output_file_path']

# Open the output file for writing
with open(output_file_path, "w",encoding="utf-8") as output_file:
    output_file.write(latex_code) # Write the LaTeX code to the output file