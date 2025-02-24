#Relationship_Extract_Utility
#Authors: Gutti Sravya and Saurabh Brij Nath Prasad
import zipfile
import gzip
import json
import uuid
import datetime
from datetime import datetime
from datetime import timedelta
import pandas as pd
import csv
import os
import boto3
from io import BytesIO, StringIO

s3 = boto3.client('s3')

def get_timestamp():
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    return timestamp

def write_sentence_to_file(output_file_path, sentence_to_write):
     # Extract bucket name and key from the output file path
    bucket_name = config_file["OutputBucket"]
    key = output_file_path
    sentence_to_write = "Current TimeStamp: " + str(get_timestamp()) + "   " + str(sentence_to_write) + "\n"
    try:
        obj = s3.get_object(Bucket=bucket_name, Key=key)
        existing_content = obj['Body'].read().decode('utf-8')
    except s3.exceptions.NoSuchKey:
        existing_content = ""
    updated_content = existing_content + sentence_to_write
    s3.put_object(Bucket=bucket_name, Key=key, Body=updated_content)

def load_json(file):
    try:
        data = json.load(file)
        all_data.extend(data)
    except Exception as e:
        print(f"An error occurred while loading JSON data: {e}")


def nested_child_json_to_csv(k, key, nested_child_list):
    try:
        sentence_to_write = "Nested Child records transformation from json to csv for " + str(k) + str(key)
        write_sentence_to_file(output_file_path, sentence_to_write)
        relation_nested_child_df = pd.DataFrame(nested_child_list)
        nested_child_name = str(k) + "_" + str(key) + '_Records_' + str(timestamp_unix_ms)
        csv_file_path_child = config_file["OutputLocation"]
        csv_file_path_child = str(csv_file_path_child).strip('/')  + "/" + nested_child_name + ".csv"
        header=True
        try:
            obj = s3.get_object(Bucket=config_file["OutputBucket"], Key=csv_file_path_child)
            existing_content = obj['Body'].read().decode('utf-8')
            mode = 'a'
            #header = False
        except s3.exceptions.NoSuchKey:
            existing_content = ""
            mode = 'w'
            #header = True
        csv_buffer = StringIO()
        relation_nested_child_df.to_csv(csv_buffer, sep=",", escapechar="\\", quoting=csv.QUOTE_ALL, mode=mode, header=header, index=None, na_rep='')
        s3.put_object(Bucket=config_file["OutputBucket"], Key=csv_file_path_child, Body=csv_buffer.getvalue())

    except Exception as e:
        print("An error occurred. Check the Log file for detail")
        sentence_to_write = f"An error occurred while transforming nested child records from JSON to CSV: {e}"
        write_sentence_to_file(output_file_path, sentence_to_write)

def child_json_to_csv(k, child_list):
    try:
        sentence_to_write = "Child records transformation from json to csv for " + str(k)
        write_sentence_to_file(output_file_path, sentence_to_write)
        relation_child_df = pd.DataFrame(child_list)
        child_name = str(k) + '_Records_' + str(timestamp_unix_ms)
        csv_file_path_child = config_file["OutputLocation"]
        csv_file_path_child = str(csv_file_path_child).strip('/') + "/" + child_name + ".csv"
        header=True
        try:
            obj = s3.get_object(Bucket=config_file["OutputBucket"], Key=csv_file_path_child)
            existing_content = obj['Body'].read().decode('utf-8')
            mode = 'a'
        except s3.exceptions.NoSuchKey:
            existing_content = ""
            mode = 'w'
        csv_buffer = StringIO()    
        relation_child_df.to_csv(csv_buffer, sep=",", escapechar="\\", quoting=csv.QUOTE_ALL, index=None, na_rep='', mode=mode, header=header)
        s3.put_object(Bucket=config_file["OutputBucket"], Key=csv_file_path_child, Body=csv_buffer.getvalue())        
                
    except Exception as e:
        print("An error occurred. Check the Log file for detail")
        sentence_to_write = f"An error occurred while transforming child records from JSON to CSV: {e}"
        write_sentence_to_file(output_file_path, sentence_to_write)

def getRelationshipinfo(relation_list, i,dict_map, relationship_name):
    child_list = []
    dict_child_struct = {}
    nested_child_dict = {}
    nested_child_list = []
    record_dict = {}
    try:
        for k1, v1 in i.items():
            if k1 == 'attributes':
                if isinstance(v1, dict) and v1:  # Check if v1 is a non-empty dictionary
                    for k, v in v1.items():
                        try:
                            if k in dict_map["Attributes"]:
                                record_dict[k] = v[0]['value'] if v and 'value' in v[0] else None
                            if k in dict_map["Nested"]:
                                dict_child_struct = {}
                                child_list = []
                                list_of_subattributes = dict_map["Nested"][k]
                                dict_child_struct = {key: None for key in list_of_subattributes}
                                for t in v:
                                    if 'uri' in t:
                                        dict_child_struct["uri"] = t['uri']
                                        dict_child_struct["parent_uri"] = i['uri']
                                    if 'value' in t:
                                        for key in t['value']:
                                            nested_child_dict = {}
                                            nested_child_list = []
                                            if dict_map["Nested"][k][key] == "":
                                                if t['value'][key][0]['ov'] == True:
                                                    dict_child_struct[key] = t['value'][key][0]['value'] if t['value'][key][0]['value'] else None
                                            else:
                                                for s in t['value'][key]:
                                                    nested_child_dict = {}
                                                    if 'value' in s:
                                                        for x, y in s['value'].items():
                                                            if x in dict_map["Nested"][k][key]:
                                                                if s['value'][x][0]['ov'] == True:
                                                                    nested_child_dict[x] = s['value'][x][0]['value'] if s['value'][x][0]['value'] else None
                                                        nested_child_dict["parent_uri"] = t['uri']
                                                        nested_child_dict["grand_parent_uri"] = i['uri']
                                                        nested_child_list.append(nested_child_dict)
                                                nested_child_json_to_csv(k, key, nested_child_list)
                                    child_list.append(dict_child_struct)
                                    dict_child_struct = {}
                                child_json_to_csv(k, child_list)
                                child_list = []
                                dict_child_struct = {}
                        except Exception as e:
                            print(f"An error occurred while processing key {k}: {e}")
                            sentence_to_write = f"An error occurred while processing the attributes of records: {e}"
                            write_sentence_to_file(output_file_path, sentence_to_write)
            if k1 == 'startObject':
                if isinstance(v1, dict) and v1:  # Check if v1 is a non-empty dictionary
                    if 'type' in v1 and 'objectURI' in v1:
                        record_dict['startObjectType'] = v1['type']
                        record_dict['startObjectURI'] = v1['objectURI']
            if k1 == 'endObject':
                if isinstance(v1, dict) and v1:  # Check if v1 is a non-empty dictionary
                    if 'type' in v1 and 'objectURI' in v1:
                        record_dict['endObjectType'] = v1['type']
                        record_dict['endObjectURI'] = v1['objectURI']
            if k1 in dict_map["System_Variables"] and k1 != 'attributes':
                record_dict[k1] = v1 if v1 else None
        relation_list.append(record_dict)
        return relation_list
    except Exception as e:
        print(f"An error occurred while processing key {k1}: {e}")
        sentence_to_write = f"An error occurred while retrieving Relationship information: {e}"
        write_sentence_to_file(output_file_path, sentence_to_write)


def main_rel(configuration_file_path):

    global config_file
    config_file=configuration_file_path
    global timestamp_unix_ms
    Record_number = 0

    try:
        now = datetime.now()
        timestamp_unix_ms = int(now.timestamp() * 1000)
    except Exception as e:
        print(f"An error occurred while generating the timestamp: {e}")

    #try:
     #   with open(configuration_file_path, 'r') as file:
      #      config_file = json.load(file)
    #except Exception as e:
        #print(f"An error occurred while opening the configuration file: {e}")

    global output_file_path
    mapping_file_path = config_file["InputLocationMappingFile"]
    output_file_path = config_file["OutputLocation"]
    output_file_path = output_file_path.strip('/') + "/" + "Output_Logs" + "_" + str(timestamp_unix_ms) + ".txt"

    try:
        mapping_file_obj = s3.get_object(Bucket=config_file["InputBucket"], Key=mapping_file_path)
        dict_map = json.loads(mapping_file_obj['Body'].read().decode('utf-8'))
    except Exception as e:
        print(f"An error occurred while retrieving the mapping file from S3: {e}")
        return  

    input_file = config_file["InputLocation"]

    bucket_name = config_file["InputBucket"]
    global all_data
    all_data = []

    for filename in s3.list_objects_v2(Bucket=bucket_name, Prefix=input_file)['Contents']:
        if filename['Key'].endswith(".zip"):
            try:
                obj = s3.get_object(Bucket=bucket_name, Key=filename['Key'])
                with zipfile.ZipFile(BytesIO(obj['Body'].read()), 'r') as zip_ref:
                    for file in zip_ref.namelist():
                        if file.endswith(".json"):
                            with zip_ref.open(file) as f:
                                load_json(f)
            except Exception as e:
                print(f"An error occurred while processing the ZIP file: {e}")

        elif filename['Key'].endswith(".gz"):
            try:
                obj = s3.get_object(Bucket=bucket_name, Key=filename['Key'])
                with gzip.open(BytesIO(obj['Body'].read()), 'rt') as gz_file:
                    load_json(gz_file)
            except Exception as e:
                print(f"An error occurred while processing the JSON file: {e}")
        elif filename['Key'].endswith(".json"):
            try:
                obj = s3.get_object(Bucket=bucket_name, Key=filename['Key'])
                load_json(BytesIO(obj['Body'].read()))
            except Exception as e:
                print(f"An error occurred while processing the JSON file: {e}")
    global relation_list           
    relation_list = []
    record_dict = {}

    for i in all_data:
        relationship_name = i["type"]
        try:
            combined_dict = {**dict_map["System_Variables"], **dict_map["Attributes"], **dict_map["startObject"], **dict_map["endObject"]}
            record_dict = combined_dict.copy()
            Record_number += 1
            print("Record_number: " + str(Record_number))
            sentence_to_write = "Record_number: " + str(Record_number)
            write_sentence_to_file(output_file_path, sentence_to_write)
            relation_list = getRelationshipinfo(relation_list, i,dict_map, relationship_name)
        except KeyError:
            sentence_to_write = f"The key {relationship_name} does not exist in the dictionary."
            write_sentence_to_file(output_file_path, sentence_to_write)

    csv_file_path = config_file["OutputLocation"]
    csv_file_path = str(csv_file_path).strip('/')  + "/" + "Relationships_" + str(timestamp_unix_ms) + ".csv"

    if len(relation_list) != 0:
        try:
            relationship_df = pd.DataFrame(relation_list)
            csv_buffer = StringIO()
            relationship_df.to_csv(csv_buffer, sep=",", escapechar="\\", quoting=csv.QUOTE_ALL, index=None, na_rep='', header=True)
            s3.put_object(Bucket=config_file["OutputBucket"], Key=csv_file_path, Body=csv_buffer.getvalue())
        except Exception as e:
            print("An error occurred. Check the Log file for detail")
            sentence_to_write = f"An error occurred while writing the DataFrame to a CSV file: {e}"
            write_sentence_to_file(output_file_path, sentence_to_write)
    else:
        try:
            combined_dict = {**dict_map["System_Variables"], **dict_map["Attributes"], **dict_map["startObject"], **dict_map["endObject"]}
            record_dict = combined_dict.copy()
            relation_list.append(record_dict)
            relationship_df = pd.DataFrame(columns=record_dict)
            csv_buffer = StringIO()
            relationship_df.to_csv(csv_buffer, sep=",", escapechar="\\", quoting=csv.QUOTE_ALL, index=None, na_rep='', header=True)
            print("No data to process.")
            sentence_to_write = "Relationship type of input data doesn't match with that of configuration file. No data to process."
            write_sentence_to_file(output_file_path, sentence_to_write)
            sentence_to_write = f"The file for 'Relationships' has been created in the directory."
            write_sentence_to_file(output_file_path, sentence_to_write)
        except Exception as e:
            print("An error occurred. Check the Log file for detail")
            sentence_to_write = f"An error occurred while writing the DataFrame to a CSV file: {e}"
            write_sentence_to_file(output_file_path, sentence_to_write)
    relation_list=[]
