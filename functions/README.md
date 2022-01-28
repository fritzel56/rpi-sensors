# Context
This folder contains code which is executed by the Google Cloud Function associated with the project. The function is triggered by the Pub/Sub topic tied to this job.

# File Guide
| File | Description |
|------|-------------|
| config.yaml | YAML file containing info on how to handle the messages from Pub/Sub. See below for structure. |
| main.py | Logic kicked off by the function used to parse the messages and then write them to BigQuery |
| requirements.txt | Contains requirements for the function to run the logic. |

# YAML structure

The YAML structure should have information encoded in the following structure:

device_id:
  dataset: dataset_name_in_bigquery
  table_name: table_name_in_bigquery
  data:
    - field_name1
    - field_name2
    - etc

device_id should be the device ID as registered in IoT core. The dataset and table_name should be the target database and table to write the data to in BigQuery. The data fields reflect which fields should be written to the are the fields which should be written to the database. These fields using these names (and capitalization) should already be present in the message. The only calculation which is done is parsing the date field.