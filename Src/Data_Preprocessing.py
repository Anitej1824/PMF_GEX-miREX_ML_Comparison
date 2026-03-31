# Load Required Libraries
import pandas as pd
import gzip


def load_geo_matrix(file_path):
    """
    Load a GEO series matrix file (.txt.gz) and extract the expression table.

    Parameters
    ----------
    file_path : str
        Path to the GEO series matrix file.

    Returns
    -------
    pd.DataFrame
        Raw expression dataframe with probes as rows and samples as columns.
        Includes 'ID_REF' column.
    """
    data = []

    with gzip.open(file_path, 'rt') as f:
        # Skip metadata until expression table begins
        for line in f:
            if line.startswith("!series_matrix_table_begin"):
                break

        # Read header row (sample IDs)
        header = f.readline().strip().split("\t")

        # Read expression data
        for line in f:
            if line.startswith("!series_matrix_table_end"):
                break
            data.append(line.strip().split("\t"))

    df = pd.DataFrame(data, columns=header)
    return df


def clean_expression_data(df):
    """
    Clean and transform GEO expression data into ML-ready format.

    Steps performed:
    - Remove quotation marks from column names and probe IDs
    - Set probe IDs ('ID_REF') as index
    - Convert expression values to numeric
    - Transpose dataframe so samples are rows and genes are columns

    Parameters
    ----------
    df : pd.DataFrame
        Raw expression dataframe from GEO.

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe with:
        - Rows = samples (GSM IDs)
        - Columns = genes/probes
        - Values = numeric expression levels
    """
    # Remove quotation marks from column names
    df.columns = df.columns.str.replace('"', '')

    # Remove quotation marks from probe IDs
    df["ID_REF"] = df["ID_REF"].str.replace('"', '')

    # Set probe IDs as index
    df = df.set_index("ID_REF")

    # Convert all values to numeric
    df = df.apply(pd.to_numeric)

    # Transpose: samples as rows, genes as columns
    df = df.T

    return df

def extract_metadata(file_path):
    """
    Extract sample-level metadata from a GEO series matrix file.

    Parameters
    ----------
    file_path : str
        Path to the GEO series matrix file (.txt.gz).

    Returns
    -------
    pd.DataFrame
        Raw metadata dataframe with:
        - Rows = samples (GSM IDs)
        - Columns = metadata entries (unparsed)
        Each cell contains raw metadata strings (e.g., "disease: PMF").
    """
    meta_rows = []
    sample_ids = []

    with gzip.open(file_path, 'rt') as f:
        for line in f:
            # Extract sample IDs
            if line.startswith("!Sample_geo_accession"):
                sample_ids = line.strip().split("\t")[1:]

            # Extract metadata fields
            if line.startswith("!Sample_characteristics_ch1"):
                values = line.strip().split("\t")[1:]
                meta_rows.append(values)

    # Construct dataframe (samples as rows)
    meta = pd.DataFrame(meta_rows).T
    meta.index = [s.strip('"') for s in sample_ids]

    return meta

def parse_metadata(meta_df):
    """
    Parse and structure raw GEO metadata into clean tabular format.

    Steps performed:
    - Remove quotation marks from metadata entries
    - Split key-value pairs (e.g., "disease: PMF")
    - Construct structured columns from metadata keys
    - Standardize sample identifiers (remove quotes)

    Parameters
    ----------
    meta_df : pd.DataFrame
        Raw metadata dataframe from GEO.

    Returns
    -------
    pd.DataFrame
        Parsed metadata dataframe with:
        - Rows = samples (GSM IDs)
        - Columns = metadata fields (e.g., disease, tissue, etc.)
        - Values = cleaned metadata values
    """
    parsed_rows = []

    for _, row in meta_df.iterrows():
        row_dict = {}

        for item in row:
            if pd.isna(item):
                continue

            # Remove surrounding quotes
            item = item.strip('"')

            # Split key-value pairs
            if ": " in item:
                key, value = item.split(": ", 1)
                row_dict[key] = value

        parsed_rows.append(row_dict)

    parsed_df = pd.DataFrame(parsed_rows, index=meta_df.index)

    # Standardize sample IDs (remove quotes)
    parsed_df.index = parsed_df.index.str.replace('"', '', regex=False)

    return parsed_df