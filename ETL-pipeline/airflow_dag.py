import pandas as pd
import pandahouse
from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context


connection = {
'host': 'https://clickhouse.lab.karpov.courses',
'password': 'password',
'user': 'student',
'database': 'simulator_20220420'
}

connection_test = {
'host': 'https://clickhouse.lab.karpov.courses',
'password': 'password',
'user': 'student-rw',
'database': 'test'
}

def ch_get_df(query, connection):
    df = pandahouse.read_clickhouse(query = query, connection=connection)
    return df


default_args = {
    'owner': 'mashkarin_ai',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2022, 3, 10),
}

schedule_interval = '0 23 * * *'

@dag(default_args=default_args, schedule_interval=schedule_interval, catchup=False)
def dag_mashkarin():

    @task()
    def extract_feed():
        q = '''SELECT toDate(time) as date,
                   user_id,
                   if(gender=1, 'male', 'female') as gender,
                   age,
                   os,
                   countIf(action = 'like') as likes,
                   countIf(action = 'view') as views
                FROM simulator_20220420.feed_actions
                WHERE toDate(time) = yesterday()
                GROUP BY date, user_id, gender, age, os'''
        df = ch_get_df(q, connection = connection)
        return df
    
    @task()
    def extract_msgs():
        q = '''select date, gender, age, os, user_id, messages_received, messages_sent, users_received, users_sent from
                (SELECT toDate(time) as date,
                        user_id,
                        if(gender=1, 'male', 'female') as gender,
                        age,
                        os,
                       count() as messages_sent,
                       uniqExact(reciever_id) as users_sent
                FROM simulator_20220420.message_actions
                WHERE toDate(time) = yesterday()
                group by date, user_id, gender, age, os) as t1
                left join
                (select reciever_id,
                        count() as messages_received,
                        uniqExact(user_id) as users_received
                FROM simulator_20220420.message_actions
                WHERE toDate(time) = yesterday()
                group by reciever_id) as t2
                on t1.user_id = t2.reciever_id'''
        df = ch_get_df(q, connection = connection)
        return df
    
    @task()
    def merge_df(df_1, df_2):
        df = df_1.merge(df_2, on=['user_id','date','gender','age','os'], how='outer').fillna(0)
        return df
    
    @task()
    def metric_calc(df, metric):
        df = df.groupby(['date',metric])['likes','views','messages_received','messages_sent','users_received','users_sent'].sum()\
        .sort_index().reset_index()
        df[metric] = df[metric].apply(lambda x: f'{metric} - ' + str(x))
        df = df.rename({metric : 'metrics'}, axis = 1)
        return df
    
    @task()
    def concat(df_os, df_gender, df_age):
        final_df = pd.concat([df_gender, df_os, df_age])
        final_df = final_df.rename({'date' : 'event_date'}, axis = 1)
        return final_df
    
    @task()
    def load(final_df):
        q = '''CREATE TABLE IF NOT EXISTS test.mashkarin_ai5
                (   event_date Date,
                    metrics String,
                    likes Float64,
                    views Float64,
                    messages_received Float64,
                    messages_sent Float64,
                    users_received Float64,
                    users_sent Float64
                ) ENGINE = Log()'''

        pandahouse.execute(connection=connection_test, query=q)

        pandahouse.to_clickhouse(final_df, 'mashkarin_ai5', index=False, connection=connection_test)
        
        
    df_feed = extract_feed()
    df_msgs = extract_msgs()
    
    df = merge_df(df_feed, df_msgs)
    
    df_os = metric_calc(df, 'os')
    df_gender = metric_calc(df, 'gender')
    df_age = metric_calc(df, 'age')
    
    final_df = concat(df_os, df_gender, df_age)
    
    load(final_df)
    
dag_mashkarin = dag_mashkarin()
