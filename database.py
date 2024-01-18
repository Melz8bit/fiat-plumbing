import os
import uuid
from datetime import datetime

import MySQLdb
from dotenv import load_dotenv

# from flask_login import UserMixin
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

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

        # if len(results) == 1:
        #     return results[0]

        return results
    except MySQLdb.Error as e:
        print("MySQL Error:", e)


############## User Queries ##############
def get_user(user_id):
    return get_results(
        f"""
            SELECT * FROM users WHERE users.user_id = '{user_id}' """
    )[0]


############## Client Queries ##############
def get_all_clients():
    return get_results(
        f"""
            SELECT clients.*, projects.client_id, count(project_id) AS project_count
            FROM projects
            INNER JOIN clients ON projects.client_id = clients.client_id
            GROUP BY projects.client_id
        """
    )


############## Project Queries ##############
def get_all_projects():
    return get_results(
        f"""
            SELECT projects.*, clients.name
            FROM projects
            INNER JOIN clients
            ON projects.client_id = clients.client_id;
        """
    )


############## Search Queries ##############
def search(search_by, search_criteria):
    return get_results(
        f"""
            SELECT * FROM projects
            WHERE project_id = '{search_criteria}';
        """
    )
