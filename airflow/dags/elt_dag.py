from datetime import datetime, timedelta
from airflow import DAG
from docker.types import Mount
from airflow.operators.python import PythonOperator
from airflow.providers.docker.operators.docker import DockerOperator
import subprocess

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

def run_elt_script():
    script_path = "/opt/airflow/elt/elt_script.py"
    result = subprocess.run(["python", script_path],
                            capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"Script failed with error: {result.stderr}")
    else:
        print(result.stdout)

with DAG(
    'elt_and_dbt',
    default_args=default_args,
    description='An ELT workflow with dbt',
    start_date=datetime(2024, 11, 8),
    catchup=False
) as dag:

    t1 = PythonOperator(
        task_id="run_elt_script",
        python_callable=run_elt_script
    )

    t2 = DockerOperator(
        task_id="dbt_run",
        image='ghcr.io/dbt-labs/dbt-postgres:1.4.7',
        command=[
            "run",
            "--profiles-dir",
            "/root",
            "--project-dir",
            "/dbt"
        ],
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
        mounts=[
            Mount(source='/home/rezou/Documents/docker_tutor/elt/custom_postgres',
                  target='/dbt', type='bind'),
            Mount(source='/home/rezou/.dbt',
                  target='/root', type='bind')
        ]
    )

    t1 >> t2