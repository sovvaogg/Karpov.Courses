import telegram
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import io
import pandahouse

sns.set()

chat_id = -691600284
bot = telegram.Bot(token=bot_token)

connection = {
'host': 'https://clickhouse.lab.karpov.courses',
'password': 'password',
'user': 'student',
'database': 'simulator_20220420'
}

q = '''select *
from 
(select toStartOfFifteenMinutes(time) as ts, 
uniqExact(user_id) as dau_feed, 
countIf(user_id, action = 'view') as views, 
countIf(user_id, action = 'like') as likes, 
round((countIf(user_id, action = 'like') / countIf(user_id, action = 'view') * 100), 2) as ctr 
from simulator_20220420.feed_actions 
where time >= today() -1 and time < toStartOfFifteenMinutes(now()) 
group by toStartOfFifteenMinutes(time) 
order by ts) as t1 
left join 
(select toStartOfFifteenMinutes(time) as ts, 
uniqExact(user_id) as dau_msgs, 
count(user_id) as messages 
from simulator_20220420.message_actions 
where time >= today() - 1 and time < toStartOfFifteenMinutes(now())
group by toStartOfFifteenMinutes(time)
order by ts 
) as t2 
using ts
order by ts'''
df = pandahouse.read_clickhouse(q, connection=connection)

def check_anomaly(df, metric, n=9, a=3.5):
    df['std'] = df[metric].shift(1).rolling(n).std()
    df['mean'] = df[metric].shift(1).rolling(n).mean()
    df['up'] = df['mean'] + df['std'] * a
    df['low'] = df['mean'] - df['std'] * a
    
    df['up'] = df['up'].rolling(n,center=True, min_periods=5).mean()
    df['low'] = df['low'].rolling(n,center=True, min_periods=5).mean()
    
    if (df[metric].iloc[-1] > df['up'].iloc[-1] or df[metric].iloc[-1] < df['low'].iloc[-1]) and (abs(1 - df[metric].iloc[-1] / df[metric].iloc[-2]) > 0.3):
        curr_val = df[metric].iloc[-1]
        diff = abs(1 - df[metric].iloc[-1] / df[metric].iloc[-2])
        
        msg = f'''Метрика {metric}.\nТекущее значение: {curr_val}, отклонение от предыдущего значения: {diff:.2%}.'''
        
        bot.sendMessage(chat_id, text = msg)
        
        
        plt.figure(figsize=(15,8))
        ax = sns.lineplot(x=df['ts'], y=df[metric], label=metric)
        ax = sns.lineplot(x=df['ts'], y=df['up'], label='up')
        ax = sns.lineplot(x=df['ts'], y=df['low'], label='low')
        plt.title('График метрики за текущий и предыдущий дни')
        plot_object = io.BytesIO()
        plt.savefig(plot_object)
        plot_object.seek(0)
        plot_object.name = 'plot.png'
        plt.close()
        bot.sendPhoto(chat_id=chat_id, photo=plot_object)
        
metrics = ['dau_feed', 'views', 'likes', 'ctr', 'dau_msgs', 'messages']



try:
    for metric in metrics:
        check_anomaly(df,metric)
except Exception as e:
    print(e)
