# airflow_covid_statewise

About project:

In this project I created a pipline from scratch which takes daily covid data and store it in google bigquery using apache-airflow. The pipeline have 3 tasks:

Task 1: It fetches data from web api and write it to a csv in local system

Task 2: It reads data from the csv file and upload it to google big query table

Task 3: It reads the data from bigquery table and calculate percentage of upload.(total rows in BQ table for today * 100 / total rows in today’s CSV)


To install airflow in your system:

pip install apache-airflow\
airflow initdb

For more information: https://airflow.apache.org/docs/stable/installation.html

Bigquery setup:

pip install google-cloud-bigquery

To get credentials:

1. In the Cloud Console, go to the Create service account key page.
2. From the Service account list, select New service account. 
3. In the Service account name field, enter a name.
4. From the Role list, select Project > Owner.
5. Click Create. A JSON file that contains your key downloads to your computer.

For more information: https://cloud.google.com/bigquery/docs/reference/libraries

To create new bigquery dataset: https://cloud.google.com/bigquery/docs/datasets


To run this project in your system:

airflow webserver\
airflow scheduler

The webserver will be running on 8080 port
