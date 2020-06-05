import datetime
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
import requests
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import logging


def data_to_dataframe(data):
    states = []
    cases = []
    dates = []
    for row in data:
        states.append(row['state'])
        cases.append(row['confirmed'])
        dates.append(datetime.datetime.strftime(datetime.datetime.today(), '%d-%m-%Y'))
    statewise_data = {
        'states': states,
        'cases': cases,
        'date': dates
    }
    statewise_dataframe = pd.DataFrame(statewise_data)
    return statewise_dataframe


def create_csv():
    try:
        api_response = requests.get('https://api.covidindiatracker.com/state_data.json')
        covid_data = api_response.json()
        statewise_dataframe = data_to_dataframe(covid_data)
        csv_name = 'csv_' + datetime.datetime.strftime(datetime.datetime.today(), '%d-%m-%Y') + '.csv'
        statewise_dataframe.to_csv(csv_name)
    except requests.exceptions.HTTPError as errh:
        logging.error("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        logging.erorr("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        logging.error("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        logging.error("OOps: Something Else", err)

def to_bigquery():
    csv_name = 'csv_' + datetime.datetime.strftime(datetime.datetime.today(), '%d-%m-%Y') + '.csv'
    csv_data = pd.read_csv(csv_name, index_col=0)
    credentials = service_account.Credentials.from_service_account_file(
        'bigquery-271709-03f68b4ecacf.json')
    project_id = 'bigquery-271709'
    client = bigquery.Client(credentials=credentials, project=project_id)
    csv_data.to_gbq(destination_table='covid_dataset.covid_statewise',
                project_id='bigquery-271709',
                credentials=credentials,
                if_exists='append',
                table_schema=None)

def percentage_upload():
    csv_name = 'csv_' + datetime.datetime.strftime(datetime.datetime.today(), '%d-%m-%Y') + '.csv'
    csv_data = pd.read_csv(csv_name, index_col=0)
    index = csv_data.index
    number_of_rows = len(index)
    credentials = service_account.Credentials.from_service_account_file(
        'bigquery-271709-03f68b4ecacf.json')
    project_id = 'bigquery-271709'
    sql = 'select count(*) as TotalRows from covid_dataset.covid_statewise_cases'
    client = bigquery.Client(project=project_id, credentials=credentials)
    bigquery_dataframe = client.query(sql).to_dataframe()
    rows_bigquery = bigquery_dataframe['TotalRows'][0]
    percent_upload = (rows_bigquery/number_of_rows)*100
    logging.info("The percentage upload is: " , percent_upload)


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime.datetime(2020, 6, 1),
    'email': ['shreya.kaushik@nineleaps.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'schedule_interval': '@daily',
    'retries': 1,
    'retry_delay': datetime.timedelta(seconds=5),
}

dag = DAG('covid_statewise',
          description='Statewise covid data',
          catchup=False,
          default_args = default_args)

csv_operator = PythonOperator(task_id='create_csv',
                                python_callable=create_csv, dag=dag)
bigquery_operator = PythonOperator(task_id='to_bigquery',
                                 python_callable=to_bigquery, dag=dag)
percentage_operator = PythonOperator(task_id='percentage_upload',
                                python_callable=percentage_upload, dag=dag)


csv_operator >> bigquery_operator >> percentage_operator

