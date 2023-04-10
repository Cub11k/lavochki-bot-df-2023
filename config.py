import os

if os.environ.get('TEST') == 'True':
    import test_config
    test_config.setup_db_environ()

database_log_file = os.environ.get('DATABASE_LOG_FILE')

token = os.environ.get('TOKEN')
admin_id = os.environ.get('ADMIN_ID')

dbms_name = os.environ.get('DBMS_NAME')
dbms_driver = os.environ.get('DBMS_DRIVER')
dbms_user = os.environ.get('DBMS_USER')
dbms_password = os.environ.get('DBMS_PASSWORD')
dbms_host = os.environ.get('DBMS_HOST')
dbms_port = os.environ.get('DBMS_PORT')
db_name = os.environ.get('DB_NAME')
db_echo = os.environ.get('DB_ECHO') in ["True", "true", "1", "t", "y", "yes"]
