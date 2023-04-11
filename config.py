import os

test = os.environ.get('TEST') == 'True'
if test:
    import test_config
    test_config.setup_db_environ()
    test_config.setup_tg_environ()

bot_log_file = os.environ.get('BOT_LOG_FILE')
database_log_file = os.environ.get('DATABASE_LOG_FILE')

token = os.environ.get('TOKEN', '')
admin_ids = list(map(int, (os.environ.get('ADMIN_IDS', '0').split(','))))
channel_id = os.environ.get('CHANNEL_ID', '0')

dbms_name = os.environ.get('DBMS_NAME')
dbms_driver = os.environ.get('DBMS_DRIVER')
dbms_user = os.environ.get('DBMS_USER')
dbms_password = os.environ.get('DBMS_PASSWORD')
dbms_host = os.environ.get('DBMS_HOST')
dbms_port = os.environ.get('DBMS_PORT')
db_name = os.environ.get('DB_NAME')
db_echo = os.environ.get('DB_ECHO') in ["True", "true", "1", "t", "y", "yes"]

redis_host = os.environ.get('REDISHOST')
redis_password = os.environ.get('REDISPASSWORD')
redis_port = os.environ.get('REDISPORT')
redis_user = os.environ.get('REDISUSER')
