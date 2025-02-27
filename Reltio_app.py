#Streamlit App to run Reltio tasks
#Author : Raj Kumar Panjiyara
import zipfile
import gzip
import json
import uuid
import datetime
import subprocess
from datetime import datetime
from datetime import timedelta
import csv
import os
import streamlit as st
import Entity
import Reltio_Count_Check_Automation as rc
import Relationship
import base64
# Import necessary modules for your Python scripts

def entity_export(params):
    Entity.main_entity(params)
    
def relation_export(params):
    Relationship.main_rel(params)

def count_check(params,user_input):
    rc.main_cnt(params,user_input)

def main():


    st.title("Reltio Task Management")

    # Select job type
    job_type = st.selectbox(
        "Select Job Type",
        ["Entity Export", "Relation Export", "Reltio Crosswalk Report"]
    )

    # Upload configuration file
    config_file = st.file_uploader("Upload Configuration File", type=["json"])
    user_input=''
    if job_type == "Reltio Crosswalk Report":
        user_input = st.text_input("Please enter the delimiter and country code(s) separated by commas:")

    if config_file is not None:
        config_params = json.load(config_file)
        # Run the selected job
        if st.button("Run Job"):
            if job_type == "Entity Export":
                st.write('Job Executed Successfully...')
                entity_export(config_params)
                st.write('Job Completed...')
            elif job_type == "Relation Export":
                st.write('Job Executed Successfully...')
                relation_export(config_params)
                st.write('Job Completed...')
            elif job_type == "Reltio Crosswalk Report":
                st.write('Job Executed Successfully...')
                count_check(config_params,user_input)
                st.write('Job Completed...')
            

if __name__ == "__main__":
    main()