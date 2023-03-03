import psycopg2
import dbconfig

#define DB Connection
SQLConnection1 = psycopg2.connect(dbname = config.sql_dbname_viz, host = config.sql_host_viz, port = config.sql_port_viz, user = config.sql_user_viz, password = config.sql_password_viz)
cursor = SQLConnection1.cursor()

# cricket_fixtures_roanuz = table name
#insert data into DB
postgres_insert_query = '''insert into test_postgres (
                            id,
                            name1)
                            VALUES (%s,%s);
                            '''
record_to_insert = (        str(1),
                            str("aniru"))
cursor.execute(postgres_insert_query, record_to_insert)
SQLConnection1.commit()

#for read
