# Построение ETL-пайплайна

Описание задачи:

Необходимо создать DAG в Apache Airflow.
- Параллельно будем обрабатывать две таблицы. В feed_actions для каждого юзера посчитаем число просмотров и лайков контента. В message_actions для каждого юзера считаем, сколько он получает и отсылает сообщений, скольким людям он пишет, сколько людей пишут ему.
- Объединяем две таблицы.
- Для получившейся таблицы считаем все эти метрики в срезе по полу, возрасту и ОС.
- Финальные данные со всеми метриками записываем в отдельную таблицу в ClickHouse.
