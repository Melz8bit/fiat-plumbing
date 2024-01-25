import os
import uuid
from datetime import datetime

import MySQLdb
from dotenv import load_dotenv

# from flask_login import UserMixin
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# DB_CONNECTION_STRING = f"mysql+pymysql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}?charset=utf8mb4"

DB_CONNECTION_STRING = f"mysql+pymysql://{os.getenv('DATABASE_USERNAME')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOST')}/{os.getenv('DATABASE_NAME')}?charset=utf8mb4"
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


def get_user_password(email):
    return get_results(
        f"""
            SELECT password
            FROM users
            WHERE users.email = '{email}'
        """
    )[0]


def get_user_from_email(email):
    return get_results(
        f"""
            SELECT *
            FROM users
            WHERE users.email = '{email}'
        """
    )[0]


############## Client Queries ##############
def get_all_clients():
    return get_results(
        f"""
            SELECT clients.*, count(project_id) AS project_count
            FROM clients
            LEFT JOIN projects ON clients.client_id = projects.client_id
            GROUP BY clients.client_id
        """
    )


def create_client(client_info):
    try:
        mycursor = connection.cursor()
        query = f"""INSERT INTO clients (name, address, city, state, zip_code, website, phone_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s)"""

        query_params = (
            client_info["name"],
            client_info["address"],
            client_info["city"],
            client_info["state"],
            client_info["zip_code"],
            client_info["website"],
            client_info["phone_number"],
        )

        mycursor.execute(query, query_params)
        connection.commit()
        print("Client created")

    except MySQLdb.Error as e:
        print("MySQL Error:", e)


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


def get_project(project_id):
    return get_results(
        f"""
            SELECT projects.*, clients.name
            FROM projects
            INNER JOIN clients
            ON projects.client_id = clients.client_id
            WHERE projects.project_id = '{project_id}';
        """
    )[0]


############## Notes Queries ##############
def get_notes(project_id):
    return get_results(
        f"""
            SELECT project_notes.*, users.first_name, users.last_name
            FROM project_notes
            INNER JOIN users
            ON project_notes.user_id = users.user_id
            WHERE project_notes.project_id = '{project_id}';
        """
    )


############## Notes Queries ##############
def get_invoices(project_id):
    return get_results(
        f"""
            SELECT * 
            FROM project_invoices
            WHERE project_id = '{project_id}';
        """
    )


############## Search Queries ##############
def search(search_by, search_criteria):
    # default search is project number
    query = f"""
        SELECT projects.*, clients.name
        FROM projects
        INNER JOIN clients
        ON projects.client_id = clients.client_id
        WHERE project_id = '{search_criteria}';
    """

    if search_by == "client name":
        query = f"""
            SELECT projects.*, clients.name
            FROM projects
            INNER JOIN clients
            ON projects.client_id = clients.client_id
            WHERE clients.name LIKE '%{search_criteria}%';
        """

    if query:
        return get_results(query)

    return None
