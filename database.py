import os
import uuid
from datetime import datetime

from dotenv import load_dotenv

# from flask_login import UserMixin
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

import MySQLdb

load_dotenv()

DB_CONNECTION_STRING = f"mysql://{os.getenv('DATABASE_USERNAME')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOST')}/{os.getenv('DATABASE_NAME')}?charset=utf8mb4"
connection = MySQLdb.connect(
    host=os.getenv("DATABASE_HOST"),
    user=os.getenv("DATABASE_USERNAME"),
    passwd=os.getenv("DATABASE_PASSWORD"),
    db=os.getenv("DATABASE"),
    autocommit=True,
    ssl_mode="VERIFY_IDENTITY",
    ssl={
        "ssl_ca": "/etc/ssl/cert.pem",
    },
)

engine = create_engine(
    DB_CONNECTION_STRING,
    connect_args={
        "ssl": {
            "ssl_ca": "/etc/ssl/cert.pem",
        }
    },
    echo=False,
)

Base = declarative_base()


def db_connect():
    connection = engine.connect()
    return engine, connection


def create_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()

    return session


def get_results(sqlQuery):
    try:
        cursor = connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(sqlQuery)
        results = cursor.fetchall()
        # cursor.close()
        # connection.close()
        return results
        # rows = []
        # for row in results:
        #     rows.append(row)

        # return rows
    except MySQLdb.Error as e:
        print("MySQL Error:", e)


def get_user(user_id):
    return get_results(f"select * from users where users.user_id = '{user_id}' ")[0]


# get_user("525bc4ea-b0f7-482d-a954-db517e6b5b89")


# try:  # Create a cursor to interact with the database
#     cursor = connection.cursor()  # Execute "SHOW TABLES" query
#     cursor.execute("SHOW TABLES")  # Fetch all the rows
#     tables = cursor.fetchall()  # Print out the tables

#     # print("Tables in the database:")
#     # for table in tables:
#     #     print(table[0])

#     # cursor.execute("SELECT * FROM users")
#     # users = cursor.fetchall()
#     # print("Users:")
#     # for user in users:
#     #     print(user)
# except MySQLdb.Error as e:
#     print("MySQL Error:", e)
# finally:  # Close the cursor and connection
#     cursor.close()
#     connection.close()
