from datetime import datetime
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
import requests
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

def create_csv():
    resp = requests.get('https://api.covidindiatracker.com/state_data.json')
    data = resp.json()
    states = []
    cases = []
    dates = []
    for d in data:
        states.append(d['state'])
        cases.append(d['confirmed'])
        dates.append(datetime.strftime(datetime.today(), '%d-%m-%Y'))
    df = {
        'states': states,
        'cases': cases,
        'date': dates
    }
    dff = pd.DataFrame(df)
    csv_name = 'csv_' + datetime.strftime(datetime.today(), '%d-%m-%Y') + '.csv'
    dff.to_csv(csv_name)

def to_bigquery():
    csv_name = 'csv_' + datetime.strftime(datetime.today(), '%d-%m-%Y') + '.csv'
    data = pd.read_csv(csv_name, index_col=0)
    print(data.dtypes)
    credentials = service_account.Credentials.from_service_account_file(
        'bigquery-271709-03f68b4ecacf.json')
    project_id = 'bigquery-271709'
    client = bigquery.Client(credentials=credentials, project=project_id)
    data.to_gbq(destination_table='covid_dataset.covid_statewise',
                project_id='bigquery-271709',
                credentials=credentials,
                if_exists='append',
                table_schema=None)

def percentage_upload():
    csv_name = 'csv_' + datetime.strftime(datetime.today(), '%d-%m-%Y') + '.csv'
    data = pd.read_csv(csv_name, index_col=0)
    index = data.index
    number_of_rows = len(index)
    credentials = service_account.Credentials.from_service_account_file(
        'bigquery-271709-03f68b4ecacf.json')
    project_id = 'bigquery-271709'
    sql = 'select count(*) as TotalRows from covid_dataset.covid_statewise_cases'
    client = bigquery.Client(project=project_id, credentials=credentials)
    df = client.query(sql).to_dataframe()
    rows_bigquery = df['TotalRows'][0]
    percent_upload = (rows_bigquery/number_of_rows)*100
    print(percent_upload)


dag = DAG('covid_statewise', description='Statewise covid data',
          schedule_interval='@daily',
          start_date= datetime(2020, 6, 3), catchup=False)

dummy_operator = DummyOperator(task_id='dummy_task', retries=3,
                               dag=dag)
csv_operator = PythonOperator(task_id='create_csv',
                                python_callable=create_csv, dag=dag)
bigquery_operator = PythonOperator(task_id='to_bigquery',
                                 python_callable=to_bigquery, dag=dag)
percentage_operator = PythonOperator(task_id='percentage_upload',
                                python_callable=percentage_upload, dag=dag)


dummy_operator >> csv_operator >> bigquery_operator >> percentage_operator
