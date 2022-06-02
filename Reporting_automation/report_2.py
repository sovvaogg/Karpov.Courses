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
    q = '''SELECT toStartOfDay(toDateTime(time)) AS date,
           count(distinct user_id) AS dau_feed,
           countIf(user_id, action='like') as likes,
           countIf(user_id, action='view') AS views,
           countIf(user_id, action='like')/countIf(user_id, action='view') AS CTR,
           countIf(DISTINCT user_id, os='iOS') AS ios,
           countIf(DISTINCT user_id, os='Android') AS android,
           count(DISTINCT post_id) as posts
    FROM simulator_20220420.feed_actions
    where toDate(time) between today() - 7 and today() - 1
    GROUP BY toStartOfDay(toDateTime(time))
    order by date'''
    df_feed = pandahouse.read_clickhouse(q, connection=connection)

    q = '''SELECT toStartOfDay(toDateTime(time)) AS date,
           count(distinct user_id) AS dau_msg,
           count(*) as msg_cnt,
           countIf(DISTINCT user_id, os='iOS') AS ios,
           countIf(DISTINCT user_id, os='Android') AS android       
    FROM simulator_20220420.message_actions
    where toDate(time) between today() - 7 and today() - 1
    GROUP BY toStartOfDay(toDateTime(time))
    order by date'''
    df_msgs = pandahouse.read_clickhouse(q, connection=connection)

    q = '''SELECT toStartOfDay(toDateTime(time)) AS date,
           count(DISTINCT user_id) AS user_cnt
           FROM (select * from
             (select user_id, time
           from simulator_20220420.feed_actions) t1
           join
         (select user_id, time
          from simulator_20220420.message_actions) t2 using (user_id)
            where toStartOfDay(t1.time) = toStartOfDay(t2.time)) AS t3
    where toDate(time) between today() - 7 and today() - 1
    GROUP BY toStartOfDay(toDateTime(time))
    ORDER BY date'''
    df_feed_msgs = pandahouse.read_clickhouse(q, connection=connection)

    date = str(df_feed.loc[6]['date'])[:10]
    dau_feed = str(df_feed.loc[6]['dau_feed'])
    likes = str(df_feed.loc[6]['likes'])
    views = str(df_feed.loc[6]['views'])
    ctr = str(round(df_feed.loc[6]['CTR'], 4))
    ios = str(df_feed.loc[6]['ios'])
    android = str(df_feed.loc[6]['android'])
    posts = str(df_feed.loc[6]['posts'])
    dau_msgs = str(df_msgs.loc[6]['dau_msg'])
    cnt_msgs = str(df_msgs.loc[6]['msg_cnt'])
    feed_msg_cnt = str(df_feed_msgs.loc[6]['user_cnt'])

    msg = f'''Данные за {date}.
    \nDAU ленты новостей: {dau_feed}.
    \nПри этом количество пользоватлей OS iOS: {ios},
    \nКоличество пользователей OS Android: {android}.
    \nКоличество просомтров: {views}.
    \nКоличество лайков: {likes}.
    \nCTR: {ctr}.
    \nКоличетсво активных постов: {posts}.
    \nDAU пользователей мессенджера: {dau_msgs}.
    \nКоличество отправленных сообщений: {cnt_msgs}.
    \nКоличество пользователей, использующих и ленту и мессенджер: {feed_msg_cnt}.
        '''
    bot.sendMessage(chat_id, text = msg)

    plt.figure(figsize=(15,8))
    sns.lineplot(data = df_feed, x="date", y="posts")
    plt.title('Количество активных постов за последние 7 дней')
    plot_object = io.BytesIO()
    plt.savefig(plot_object)
    plot_object.seek(0)
    plot_object.name = 'plot.png'
    plt.close()
    bot.sendPhoto(chat_id=chat_id, photo=plot_object)

    plt.figure(figsize=(15,8))
    sns.lineplot(data = df_msgs.pivot_table(df_msgs.iloc[:,3:], index = ['date']))
    plt.title('Количество уникальных пользователей, использующих сообщения, в разбивке по ОС, за последние 7 дней')
    plot_object = io.BytesIO()
    plt.savefig(plot_object)
    plot_object.seek(0)
    plot_object.name = 'plot.png'
    plt.close()
    bot.sendPhoto(chat_id=chat_id, photo=plot_object)

    plt.figure(figsize=(15,8))
    sns.lineplot(data = df_msgs, x="date", y="msg_cnt")
    plt.title('Количество отправленных сообщений за последние 7 дней')
    plt.ylim(df_msgs['msg_cnt'].min()-5, df_msgs['msg_cnt'].max()+5)
    plot_object = io.BytesIO()
    plt.savefig(plot_object)
    plot_object.seek(0)
    plot_object.name = 'plot.png'
    plt.close()
    bot.sendPhoto(chat_id=chat_id, photo=plot_object)

    plt.figure(figsize=(15,8))
    sns.lineplot(data = df_feed_msgs, x="date", y="user_cnt")
    plt.title('Число пользователей, пользующихся и лентой и сообщениями одновременно за последние 7 дней');
    plot_object = io.BytesIO()
    plt.savefig(plot_object)
    plot_object.seek(0)
    plot_object.name = 'plot.png'
    plt.close()
    bot.sendPhoto(chat_id=chat_id, photo=plot_object)
    
try:
    test_report()
except Exception as e:
    print(e)
