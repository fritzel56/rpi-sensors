import base64
from ast import literal_eval
import datetime as dt
from google.cloud import bigquery
import pytz
import yaml
import pandas as pd


def write_to_gbq(data, client, table):
    """Takes in a dataframe and writes the values to BQ
    Args:
        data (df): the dataframe to be written
        client (client): client to connect to BQ.
        table (str): the table to be written to.
    """
    # write data
    rows_to_insert = data.values.tolist()
    errors = client.insert_rows(table, rows_to_insert)
    if errors != []:
        print(errors)
        assert errors == [], 'There were errors writing data see above.'


def pubsub_reader(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """

    # read in and examine data
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    print(f'raw event: {event}')
    print(f'raw context: {context}')
    print(pubsub_message)

    # get device ID from raw event attributes
    device_id = event['attributes']['deviceId']

    # read in config data
    with open('config.yaml') as stream:
        config = yaml.full_load(stream)
    table = config[device_id]['table_name']
    dataset = config[device_id]['dataset']
    data_cols = config[device_id]['data']

    # convert pubsub_message from string to dict, fix time
    pubsub_message = pubsub_message.replace("'", '"')
    data  = literal_eval(pubsub_message)
    if isinstance(data, dict):
        data = [data]
    df = pd.DataFrame(data)
    tz = pytz.timezone('America/Toronto')
    df['Date'] = df.Date.apply(lambda x: dt.datetime.fromtimestamp(x, tz=tz))
    print(df)

    # setting up BQ connection
    client = bigquery.Client()
    dataset = dataset
    dataset_ref = client.dataset(dataset)
    table_name = table
    table_name_ref = bigquery.TableReference(dataset_ref,
                                                table_name)
    site_data_table = client.get_table(table_name_ref)

    
    # create record and write
    df = df[data_cols]
    print(df)
    write_to_gbq(df, client, site_data_table)
    print('all done')
