import sys
sys.path.append('/opt/airflow/scripts')

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from reddit_etl import fetch_reddit_data, transform_with_pyspark, save_to_postgresql

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5)
}

dag = DAG(
    "reddit_etl_pipeline",
    default_args=default_args,
    description="ETL pipeline for r/datascience subreddit data using PostgreSQL and PySpark",
    schedule_interval='*/30 * * * *',
    catchup=False
)

def etl_pipeline():
    subreddit_name = "datascience"
    raw_data = fetch_reddit_data(subreddit_name)
    transformed_data = transform_with_pyspark(raw_data)

    db_config = {
        "dbname": "reddit_db",
        "user": "root",
        "password": "hello123",
        "host": "postgres",
        "port": 5432
    }

    save_to_postgresql(transformed_data, "processed_reddit_data", db_config)

etl_task = PythonOperator(
    task_id="run_etl_pipeline",
    python_callable=etl_pipeline,
    dag=dag
)
