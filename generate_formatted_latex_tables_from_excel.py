import os
import pandas as pd
import pylatex as pl
import datetime
import codecs
import json

# Load the config file
with open("config.json", "r") as f:
    config = json.load(f)

# Change the working directory to the one specified in the config file
os.chdir(config["working_directory"])

# Read data from an Excel file into a Pandas DataFrame
full_df = pd.read_excel("SC_full_iomatrix.xlsx")

# Extract a list of unique values from the "NAICS" column of the DataFrame
list_naics = list(full_df["NAICS"].unique())


# Define a function named insert_pd_df that takes a Pandas DataFrame as input
def insert_pd_df(df):
    # Remove the first two columns of the DataFrame
    df = df.iloc[:, 2:]
    # Get the values of the first three columns
    naics_code, naics_title, sector = df.iloc[0, :3]
    # Remove the first three columns of the DataFrame
    df = df.iloc[:, 3:]
    # Filter rows based on whether the value in the 3rd column contains the word "detailed"
    df = df[df.iloc[:, 2].str.contains("detailed", case=False)]
    # Drop the 3rd column of the DataFrame
    df = df.drop(df.columns[2], axis=1)
    # Create a temporary column with numeric values of the last column, replacing "**" with 0
    df["temp"] = pd.to_numeric(df.iloc[:, -1].replace("**", 0), errors="coerce")

    # Sort the rows of the DataFrame in descending order based on the values in the temporary column
    df = df.sort_values(by="temp", ascending=False)

    # Drop the temporary column
    df = df.drop("temp", axis=1)

    # Create a title for the LaTeX table using values extracted from the first three columns of the input DataFrame
    title = f"Common Occupations for {naics_title}\\\\NAICS Code {naics_code} - {sector.capitalize()}"

    # Truncate the values in the last column to 5 characters
    df.iloc[:, -1] = df.iloc[:, -1].apply(lambda x: str(x)[:5])

    # Format values in the 3rd column using a lambda function and string formatting
    df.iloc[:, 2] = df.iloc[:, 2].apply(
        lambda x: "{:.2f}".format(float(x)) + r"{\fontsize{7}{8.4}\selectfont\%}"
        if x != "**"
        else x
    )

    # Change the column names of the DataFrame
    df.columns = ["SOC Code", "SOC Title", "Share of Industry Jobs"]

    # Generate a LaTeX table from the resulting DataFrame using its to_latex method and custom options
    latex_table = df.to_latex(
        longtable=True,
        index=False,
        # Use makecell to enable text wrapping within specific columns
        column_format=r"c>{\raggedright\arraybackslash}p{12cm}r",
        caption=f"{title}",
    )

    # Return the generated LaTeX table
    return latex_table


# Create a list of packages to be used in a LaTeX document
packages = [
    "graphicx",
    "booktabs",
    "fancyhdr",
    "longtable",
    "adjustbox",
    "sectsty",
    "titlesec",
    #     "arydshln"
    #        "hhline",
    "array",
]

# Initialize a new LaTeX document using pylatex and custom options
latex_doc = pl.Document(document_options=["a4paper", "origlongtable"])

# Add packages to the document by appending them to its packages attribute
for package in packages:
    latex_doc.packages.append(pl.Package(package))

# Add additional packages to enable specific functionality in the document, such as text wrapping and custom geometry options
latex_doc.packages.append(pl.Package("makecell"))
latex_doc.packages.append(pl.Package("typearea", options="usegeometry"))
latex_doc.packages.append(pl.Package("typearea", options="usegeometry"))
latex_doc.packages.append(pl.Package("geometry"))
latex_doc.packages.append(pl.Package("xcolor", options="table,gray"))
latex_doc.packages.append(pl.Package("caption", options="justification = centering"))

# Append commands to the preamble of the document to customize its appearance, such as changing caption settings and title spacing
latex_doc.preamble.append(pl.NoEscape(r"\captionsetup[table]{labelformat=empty}"))
# Append additional commands to the preamble of the document to customize its appearance, such as changing title spacing and defining new column types
latex_doc.preamble.append(
    pl.NoEscape(r"\titlespacing*{\section}{0pt}{-0.5\baselineskip}{-2.1\baselineskip}")
)
latex_doc.preamble.append(
    pl.NoEscape(r"\newcolumntype{L}{>{\raggedright\arraybackslash}p{4cm}}")
)
latex_doc.preamble.append(
    pl.NoEscape(r"\newcolumntype{R}{>{\raggedleft\arraybackslash}p{5.5cm}}")
)
latex_doc.preamble.append(pl.NoEscape(r"\titleformat*{\section}{\tiny}"))

# Define portrait and landscape layout
latex_doc.preamble.append(
    pl.NoEscape(
        r"\newcommand*\useportrait{\cleardoublepage \KOMAoptions{paper=portrait,DIV=current} \newgeometry{hmargin=.1cm,top=1cm,bottom=1cm,headheight=47.6pt}}"
    )
)

# Add additional packages and commands to the preamble of the document
latex_doc.preamble.append(pl.NoEscape(r"\usepackage{array}"))
latex_doc.preamble.append(
    pl.NoEscape(r"\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}")
)

# Define custom headers
page_style = pl.PageStyle("pageheader")
with page_style.create(pl.Head("L")) as header_left:
    with header_left.create(
        pl.MiniPage(
            width=pl.NoEscape(r"0.39\textwidth"), pos="b", align="l", content_pos="b"
        )
    ) as l_wrapper:
        # Add a graphic to the left header using its StandAloneGraphic method and custom options
        l_wrapper.append(
            pl.StandAloneGraphic(
                image_options="width = 110px", filename=pl.NoEscape("LMI_LOGO_Copy.png")
            )
        )
with page_style.create(pl.Head("R")) as header_right:
    with header_right.create(
        pl.MiniPage(
            width=pl.NoEscape(r"0.39\textwidth"), pos="b", align="r", content_pos="b"
        )
    ) as r_wrapper:
        # Add a graphic to the right header using its StandAloneGraphic method and custom options
        r_wrapper.append(
            pl.StandAloneGraphic(
                image_options="width = 120px", filename=pl.NoEscape("Dew_Logo_copy.png")
            )
        )

# Append a command to the preamble of the document to use portrait layout at the beginning of the document
latex_doc.preamble.append(pl.NoEscape(r"\AtBeginDocument{\useportrait}"))

# Begin doc

# Drop tables

# Get the unique values in the NAICS column
naics_values = full_df["NAICS"].unique()

# Create an empty list to store the DataFrames
dataframes = []

# Iterate over the unique NAICS values
for naics in naics_values:
    # Subset the full_df DataFrame to only include rows where NAICS equals the current naics value
    subset_df = full_df[full_df["NAICS"] == naics]

    # Check if the subset DataFrame has any rows after filtering based on whether the value in the 3rd column contains the word "detailed"
    if not subset_df[subset_df.iloc[:, 7].str.contains("detailed", case=False)].empty:
        # Add the subset DataFrame to the list of DataFrames
        dataframes.append(subset_df)

# Iterate over the list of DataFrames
for df in dataframes:
    # Apply the insert_pd_df function to the current DataFrame
    latex_table = insert_pd_df(df)

    # Add the resulting LaTeX table to the document
    latex_doc.append(pl.NoEscape(latex_table))

# Specify the file name for the generated PDF
pdf_filename = "latex_doc.pdf"

# Generate the PDF file using pylatex's generate_pdf method and custom options
latex_doc.generate_pdf(
    filepath=(config["file_path"]),
    clean_tex=False,
)

# Append additional commands to the preamble of the document, such as setting page style and section numbering depth
latex_doc.preamble.append(page_style)
latex_doc.preamble.append(pl.NoEscape(r"\setcounter{secnumdepth}{0}"))

# Change document style to use custom headers
latex_doc.change_document_style("pageheader")
