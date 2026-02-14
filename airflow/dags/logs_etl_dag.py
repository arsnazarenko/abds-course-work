from datetime import datetime, timedelta

from airflow import DAG
from airflow_clickhouse_plugin.operators.clickhouse import ClickHouseOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

dag = DAG(
    dag_id='logs_etl_pipeline',
    default_args=default_args,
    start_date=datetime.now() - timedelta(days=1),
    schedule=timedelta(minutes=5),
    catchup=False,
    tags=['etl', 'clickhouse', 'logs'],
)

create_data_marts = ClickHouseOperator(
    task_id='create_data_marts',
    database='default',
    sql=[
        '''
            CREATE TABLE IF NOT EXISTS logs_cleaned ON CLUSTER '{cluster}' (
                id UUID,
                created_at DateTime,
                received_at DateTime,
                level LowCardinality(String),
                source String,
                host String,
                environment LowCardinality(String),
                message String,
                error_type String
            ) ENGINE = ReplicatedMergeTree(
                '/clickhouse/tables/logs_cleaned',
                '{replica}'
            )
            ORDER BY (created_at, id)
            PARTITION BY toYYYYMM(created_at)
        ''',
        '''
            CREATE TABLE IF NOT EXISTS dm_logs_by_level ON CLUSTER '{cluster}' (
                level LowCardinality(String),
                log_count UInt64
            ) ENGINE = ReplicatedMergeTree(
                '/clickhouse/tables/dm_logs_by_level',
                '{replica}'
            )
            ORDER BY level
        ''',
        '''
            CREATE TABLE IF NOT EXISTS dm_logs_by_source ON CLUSTER '{cluster}' (
                source String,
                log_count UInt64,
                error_count UInt64
            ) ENGINE = ReplicatedMergeTree(
                '/clickhouse/tables/dm_logs_by_source',
                '{replica}'
            )
            ORDER BY log_count
        ''',
        '''
            CREATE TABLE IF NOT EXISTS dm_logs_by_error_type ON CLUSTER '{cluster}' (
                error_type String,
                log_count UInt64
            ) ENGINE = ReplicatedMergeTree(
                '/clickhouse/tables/dm_logs_by_error_type',
                '{replica}'
            )
            ORDER BY log_count
        ''',
        '''
            CREATE TABLE IF NOT EXISTS dm_logs_by_source_and_error ON CLUSTER '{cluster}' (
                source String,
                error_type String,
                log_count UInt64
            ) ENGINE = ReplicatedMergeTree(
                '/clickhouse/tables/dm_logs_by_source_and_error',
                '{replica}'
            )
            ORDER BY (source, log_count)
        ''',
        '''
            CREATE TABLE IF NOT EXISTS dm_logs_over_time ON CLUSTER '{cluster}' (
                time_slot DateTime,
                total_logs UInt64,
                error_logs UInt64,
                info_logs UInt64,
                warning_logs UInt64,
                debug_logs UInt64,
                critical_logs UInt64
            ) ENGINE = ReplicatedMergeTree(
                '/clickhouse/tables/dm_logs_over_time',
                '{replica}'
            )
            ORDER BY time_slot
            PARTITION BY toYYYYMM(time_slot)
        ''',
    ],
    clickhouse_conn_id='clickhouse_default',
    dag=dag,
)

clean_logs = ClickHouseOperator(
    task_id='clean_logs',
    database='default',
    sql=[
        '''
            TRUNCATE TABLE IF EXISTS logs_cleaned ON CLUSTER '{cluster}'
        ''',
        '''
            INSERT INTO logs_cleaned
            SELECT
                id,
                created_at,
                received_at,
                level,
                source,
                host,
                environment,
                message,
                error_type,
            FROM logs
            WHERE source IS NOT NULL
            AND notEmpty(source)
            AND source != '-'
            AND host IS NOT NULL
            AND notEmpty(host)
            AND host != '-'
            AND message IS NOT NULL
            AND notEmpty(message)
            AND message != '-'
            AND error_type IS NOT NULL
        ''',
    ],
    clickhouse_conn_id='clickhouse_default',
    dag=dag,
)

aggregate_by_level = ClickHouseOperator(
    task_id='aggregate_by_level',
    database='default',
    sql=[
        '''
            TRUNCATE TABLE IF EXISTS dm_logs_by_level ON CLUSTER '{cluster}'
        ''',
        '''
            INSERT INTO dm_logs_by_level
            SELECT
                level,
                count() AS log_count
            FROM logs_cleaned
            GROUP BY level
        ''',
    ],
    clickhouse_conn_id='clickhouse_default',
    dag=dag,
)

aggregate_by_source = ClickHouseOperator(
    task_id='aggregate_by_source',
    database='default',
    sql=[
        '''
            TRUNCATE TABLE IF EXISTS dm_logs_by_source ON CLUSTER '{cluster}'
        ''',
        '''
            INSERT INTO dm_logs_by_source
            SELECT
                source,
                count() AS log_count,
                countIf(level = 'error') AS error_count
            FROM logs_cleaned
            GROUP BY source
            ORDER BY log_count DESC
        ''',
    ],
    clickhouse_conn_id='clickhouse_default',
    dag=dag,
)

aggregate_by_error_type = ClickHouseOperator(
    task_id='aggregate_by_error_type',
    database='default',
    sql=[
        '''
            TRUNCATE TABLE IF EXISTS dm_logs_by_error_type ON CLUSTER '{cluster}'
        ''',
        '''
            INSERT INTO dm_logs_by_error_type
            SELECT
                error_type,
                count() AS log_count
            FROM logs_cleaned
            GROUP BY error_type
            ORDER BY log_count DESC
        ''',
    ],
    clickhouse_conn_id='clickhouse_default',
    dag=dag,
)

aggregate_by_source_and_error = ClickHouseOperator(
    task_id='aggregate_by_source_and_error',
    database='default',
    sql=[
        '''
            TRUNCATE TABLE IF EXISTS dm_logs_by_source_and_error ON CLUSTER '{cluster}'
        ''',
        '''
            INSERT INTO dm_logs_by_source_and_error
            SELECT
                source,
                error_type,
                log_count
            FROM (
                SELECT
                    source,
                    error_type,
                    count() AS log_count,
                    row_number() OVER (PARTITION BY source ORDER BY count() DESC) AS rn
                FROM logs_cleaned
                WHERE level = 'error'
                GROUP BY source, error_type
            )
            WHERE rn <= 3
            ORDER BY source, log_count DESC
        ''',
    ],
    clickhouse_conn_id='clickhouse_default',
    dag=dag,
)

aggregate_over_time = ClickHouseOperator(
    task_id='aggregate_over_time',
    database='default',
    sql=[
        '''
            TRUNCATE TABLE IF EXISTS dm_logs_over_time ON CLUSTER '{cluster}'
        ''',
        '''
            INSERT INTO dm_logs_over_time
            SELECT
                toStartOfFiveMinutes(created_at) AS time_slot,
                count() AS total_logs,
                countIf(level = 'critical') AS critical_logs,
                countIf(level = 'error') AS error_logs,
                countIf(level = 'info') AS info_logs,
                countIf(level = 'warning') AS warning_logs,
                countIf(level = 'debug') AS debug_logs
            FROM logs_cleaned
            GROUP BY time_slot
        ''',
    ],
    clickhouse_conn_id='clickhouse_default',
    dag=dag,
)

create_data_marts >> clean_logs >> [
    aggregate_by_level,
    aggregate_by_source,
    aggregate_by_error_type,
    aggregate_by_source_and_error,
    aggregate_over_time,
]
