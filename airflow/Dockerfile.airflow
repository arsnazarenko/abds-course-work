FROM apache/airflow:3.1.7
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" airflow-clickhouse-plugin airflow-clickhouse-plugin[common.sql]
