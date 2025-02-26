#Reltio_Crosswalk_Count_Analysis_Report
#Authors: Gutti Sravya and Saurabh Brij Nath Prasad
import os
import pandas as pd
import json
import logging
from datetime import datetime
import gzip
import zipfile


    # Ensure user_entities is a list and convert to lowercase for case insensitivity
def count_crosswalk_values(df, user_entities, user_sources, user_country_code=None, delimiter=None):
    if delimiter is None and user_country_code is None:
        logger.info("No delimiter or country code provided. Processing all values.")
        user_country_code = []

    if not isinstance(user_entities, list):
        user_entities = [user_entities]
    user_entities_lower = [entity.lower() for entity in user_entities]
    # Ensure user_sources is a list and convert to lowercase for case insensitivity
    if not isinstance(user_sources, list):
        user_sources = [user_sources]
    user_sources_lower = [source.lower() for source in user_sources]

    # Initialize dictionary to store counts
    counts = {}
    total_counts = {}

    # Create a mapping of lowercase to original case for entity types
    entity_case_mapping = {entity.lower(): entity for entity in df['Type'].unique()}

    # Convert 'Type' column to lowercase for case insensitivity
    df['Type_lower'] = df['Type'].str.lower()

    # Check if user entities are in the DataFrame
    if not set(user_entities_lower).issubset(df['Type_lower'].unique()):
        logger.warning("Please enter only the entity names that are present in the Excel files.")
        return None

    # Iterate over each entity
    for user_entity, user_entity_lower in zip(user_entities, user_entities_lower):
        # Filter DataFrame based on user input of entity
        filtered_df = df[df['Type_lower'] == user_entity_lower]

        # Get column names containing "crosswalk" and the source (case insensitive)
        crosswalk_columns = [col for col in df.columns if 'crosswalk' in col.lower() and any(source in col.lower() for source in user_sources_lower)]

        # Initialize total count for this entity
        total_count = 0

        # If no country code provided or if it's an empty list, count all values in crosswalk columns
        if not user_country_code or all(code.strip() == '' for code in user_country_code):
            for column in crosswalk_columns:
                count = filtered_df[column].count()
                if count > 0:  # Only add to counts if count is greater than 0
                    counts[(entity_case_mapping[user_entity_lower], column, 'All')] = count
                    total_count += count
        else:
            # Count only if the country code string is present at the end after the delimiter
            for column in crosswalk_columns:
                for code in user_country_code:
                    # Initialize the count to 0 if it doesn't exist
                    if (entity_case_mapping[user_entity_lower], column, code) not in counts:
                        counts[(entity_case_mapping[user_entity_lower], column, code)] = 0
                    # Increment the count if the country code is found at the end after the delimiter
                    count = filtered_df[filtered_df[column].astype(str).str.endswith(f"{delimiter}{code}", na=False)][column].count()
                    if count > 0:  # Only add to counts if count is greater than 0
                        counts[(entity_case_mapping[user_entity_lower], column, code)] += count
                        total_count += count

        # Store the total count for this entity if it's greater than 0
        if total_count > 0:
            total_counts[entity_case_mapping[user_entity_lower]] = total_count

    # Create a DataFrame from the counts dictionary
    output_df = pd.DataFrame([(key[0], key[1], key[2], val) for key, val in counts.items() if val > 0], columns=['Entity Type', 'Columns', 'Country Code', 'Count'])

    # Add a row for the total count of each entity, source, and country code
    total_df = output_df.groupby(['Entity Type', 'Country Code']).sum().reset_index()
    total_df['Columns'] = 'Total'
    output_df = pd.concat([output_df, total_df], ignore_index=True)

    # Remove 'Country Code' column if no country code is provided
    if not user_country_code or all(code.strip() == '' for code in user_country_code):
        output_df = output_df.drop(columns=['Country Code'])

    return output_df, total_counts

def process_files(properties, user_country_code, delimiter):
    
    input_directory = properties['input_directory']
    output_directory = properties['output_file']
    user_entities = properties['user_entities']
    user_entities_lower = [entity.lower() for entity in user_entities]
    user_sources = properties['user_sources']
    user_sources_lower = [source.lower() for source in user_sources]

    df_list = []
    
    def process_file(filepath):
        try:
            if filepath.endswith(".csv.gz"):
                with gzip.open(filepath, 'rt') as gz_file:
                    df = pd.read_csv(gz_file)
                    df_list.append(df)
                logger.info(f"Processed GZ file: {filepath}")
            elif filepath.endswith(".csv"):
                df = pd.read_csv(filepath)
                df_list.append(df)
                logger.info(f"Processed CSV file: {filepath}")
        except Exception as e:
            logger.error(f"An error occurred while processing the file {filepath}: {e}")

    files = os.listdir(input_directory)
    print(f"Files in directory: {files}")  # Debugging statement

    for filename in files:
        filepath = os.path.join(input_directory, filename)
        print(f"Processed file: {filename}")  # Debugging statement

        if filename.endswith(".zip"):
            try:
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(input_directory)
                logger.info(f"Extracted zip file: {filename}")
            except Exception as e:
                logger.error(f"An error occurred while extracting the zip file: {e}")

    # Process all files (including extracted files)
    extracted_files = os.listdir(input_directory)
    print(f"Extracted files: {extracted_files}")  # Debugging statement
    
    for filename in extracted_files:
        filepath = os.path.join(input_directory, filename)
        process_file(filepath)

    if df_list:
        merged_df = pd.concat(df_list, ignore_index=True)
        
        # Check if user entities and sources are in the DataFrame
        all_types = merged_df['Type'].str.lower().unique()
        all_sources = [col for col in merged_df.columns if 'crosswalk' in col.lower()]

        if not set(user_entities_lower).issubset(all_types):
            logger.warning("The Entity Name provided in Configuration File is not present in the input export file(s).")
            return

        if not any(source in col.lower() for source in user_sources_lower for col in all_sources):
            logger.warning("The Source Name provided in Configuration File is not present in the input export file(s).")
            return

        output_df, total_counts = count_crosswalk_values(merged_df, user_entities_lower, user_sources_lower, user_country_code, delimiter)
        if output_df is None:
            logger.warning("Invalid entity provided. Execution stopped.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        count_analysis_report = os.path.join(output_directory, f"Crosswalk_Count_Analysis_Report_{timestamp}.xlsx")
        os.makedirs(os.path.dirname(count_analysis_report), exist_ok=True)

        additional_df = pd.DataFrame(columns=['Entity Type', 'Source System', 'Country Code', 'Total Count'])
        for entity, entity_lower in zip(user_entities, user_entities_lower):
            for source, source_lower in zip(user_sources, user_sources_lower):
                source_columns = [col for col in merged_df.columns if 'crosswalk' in col.lower() and source_lower in col.lower()]
                if not user_country_code or all(code.strip() == '' for code in user_country_code):
                    total_count = sum(merged_df[col].count() for col in source_columns)
                    additional_df = pd.concat([additional_df, pd.DataFrame([{'Entity Type': entity, 'Source System': source, 'Country Code': 'All', 'Total Count': total_count}])], ignore_index=True)
                else:
                    for code in user_country_code:
                        total_count = sum(merged_df[merged_df[col].astype(str).str.endswith(f"{delimiter}{code}", na=False)][col].count() for col in source_columns)
                        additional_df = pd.concat([additional_df, pd.DataFrame([{'Entity Type': entity, 'Source System': source, 'Country Code': code, 'Total Count': total_count}])], ignore_index=True)

        if not user_country_code or all(code.strip() == '' for code in user_country_code):
            additional_df = additional_df.drop(columns=['Country Code'])

        with pd.ExcelWriter(count_analysis_report) as writer:
            additional_df.to_excel(writer, sheet_name='Total Summary', index=False)
            output_df.to_excel(writer, sheet_name='Detailed Report', index=False)
            
        
        logger.info(f"Data written to {count_analysis_report}")

    else:
        logger.warning("No DataFrames to concat")


def main_cnt(config_params,user_input):
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    global logger

    logger = logging.getLogger()

    global properties
    properties = config_params
    delimiter_country_code = user_input.split(',')

    if delimiter_country_code == ['']:
        delimiter = None
        user_country_code = None
    else:
        delimiter = delimiter_country_code[0][0]
        user_country_code = [code[1:] for code in delimiter_country_code]

    process_files(properties, user_country_code, delimiter)
