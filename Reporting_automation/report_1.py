import telegram
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io
import pandahouse

sns.set()

def test_report(chat=None):
    chat_id = chat or -799682816
    bot = telegram.Bot(token=bot_token)
    
    connection = {
    'host': 'https://clickhouse.lab.karpov.courses',
    'password': 'password',
    'user': 'student',
    'database': 'simulator_20220420'
    }
    q = '''SELECT toStartOfDay(toDateTime(time)) AS "Дата",
       count(DISTINCT user_id) AS "Уникальные пользователи"
    FROM {db}.feed_actions
    where toDate(time) between today() - 7 and today() - 1
    GROUP BY toStartOfDay(toDateTime(time))
    ORDER BY "Дата" '''
    df = pandahouse.read_clickhouse(q, connection=connection)
    q = '''SELECT toStartOfDay(toDateTime(time)) AS "Дата",
       action AS action,
       count(user_id) AS "Пользователи"
    FROM {db}.feed_actions
    where toDate(time) between today() - 7 and today() - 1
    GROUP BY action, toStartOfDay(toDateTime(time))
    ORDER BY "Дата" desc, action'''
    df_lv = pandahouse.read_clickhouse(q, connection=connection)
    q = '''SELECT toStartOfDay(toDateTime(time)) AS "Дата",
       round(countIf(user_id, action='like')/countIf(user_id, action='view'), 4) AS "CTR"
    FROM {db}.feed_actions
    where toDate(time) between today() - 7 and today() - 1
    GROUP BY toStartOfDay(toDateTime(time))
    ORDER BY "Дата" DESC'''
    df_ctr = pandahouse.read_clickhouse(q, connection=connection)
    
    DAU = str(df.loc[6]['Уникальные пользователи'])
    likes = str(df_lv.loc[0]['Пользователи'])
    views = str(df_lv.loc[1]['Пользователи'])
    CTR = round(df_lv.loc[0]['Пользователи']/df_lv.loc[1]['Пользователи'], 4)
    date = str(df_lv.loc[0]['Дата'])[:10]
    
    msg = f'''Данные за {date}.
    DAU: {DAU}.
    Количество просомтров: {views}.
    Количество лайков: {likes}.
    CTR: {CTR}.'''
    bot.sendMessage(chat_id, text = msg)
    
    plt.figure(figsize=(15,8))
    sns.lineplot(data = df, x="Дата", y="Уникальные пользователи")
    plt.title('DAU за последние 7 дней')
    plot_object = io.BytesIO()
    plt.savefig(plot_object)
    plot_object.seek(0)
    plot_object.name = 'DAU.png'
    plt.close()
    bot.sendPhoto(chat_id=chat_id, photo=plot_object)
    
    plt.figure(figsize=(15,8))
    sns.lineplot(data = df_lv, x="Дата", y="Пользователи", hue='action')
    plt.title('Количетсво просомтров и лайокв за последние 7 дней')
    plot_object = io.BytesIO()
    plt.savefig(plot_object)
    plot_object.seek(0)
    plot_object.name = 'action.png'
    plt.close()
    bot.sendPhoto(chat_id=chat_id, photo=plot_object)
    
    plt.figure(figsize=(15,8))
    sns.lineplot(data = df_ctr, x="Дата", y="CTR")
    plt.title('CTR за последние 7 дней')
    plot_object = io.BytesIO()
    plt.savefig(plot_object)
    plot_object.seek(0)
    plot_object.name = 'ctr.png'
    plt.close()
    bot.sendPhoto(chat_id=chat_id, photo=plot_object)

try:
    test_report()
except Exception as e:
    print(e)
