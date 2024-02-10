import os
import uuid
from datetime import datetime, date

import MySQLdb
from dotenv import load_dotenv
from flask_login import UserMixin
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

load_dotenv()

TODAY = datetime.today().strftime("%Y-%m-%d")

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
    # connection2 = engine.connect()
    return engine


def create_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()

    return session


def get_results(sqlQuery):
    try:
        cursor = connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(sqlQuery)
        results = cursor.fetchall()

        return results
    except MySQLdb.Error as e:
        print("MySQL Error:", e)


############## User Queries ##############
def get_user(user_id):
    try:
        return get_results(
            f"""
                SELECT * FROM users WHERE users.user_id = '{user_id}' 
            """
        )[0]
    except:
        return ""


def get_user_password(email):
    try:
        return get_results(
            f"""
                SELECT password
                FROM users
                WHERE users.email = '{email}'
            """
        )
    except:
        return ""


def get_user_from_email(email):
    try:
        return get_results(
            f"""
                SELECT *
                FROM users
                WHERE users.email = '{email}'
            """
        )[0]
    except:
        return ""


def create_user(user_info):
    try:
        mycursor = connection.cursor()
        query = f"""INSERT INTO users (user_id, first_name, last_name, email, password)
                VALUES (%s, %s, %s, %s, %s)"""

        query_params = (
            str(uuid.uuid4()),
            user_info["first_name"],
            user_info["last_name"],
            user_info["email"],
            user_info["password"],
        )

        mycursor.execute(query, query_params)
        connection.commit()
        print("User created")

    except MySQLdb.Error as e:
        print("MySQL Error:", e)


############## Client Queries ##############
def get_client(client_id):
    try:
        return get_results(
            f"""
                SELECT *
                FROM clients
                WHERE client_id = {client_id};
            """
        )[0]
    except:
        return ""


def get_client_poc(client_id):
    try:
        poc = get_results(
            f"""
                SELECT *
                FROM client_poc
                WHERE client_id = {client_id};
            """
        )[0]
    except:
        poc = ""

    return poc


def get_all_clients():
    try:
        return get_results(
            f"""
                SELECT clients.*, count(project_id) AS project_count
                FROM clients
                LEFT JOIN projects ON clients.client_id = projects.client_id
                GROUP BY clients.client_id
            """
        )
    except:
        return ""


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

        create_client_poc(client_info)

    except MySQLdb.Error as e:
        print("MySQL Error:", e)


def create_client_poc(client_info):
    try:
        mycursor = connection.cursor()
        query = f"""
                    INSERT INTO client_poc (client_id, name, telephone, email)
                    VALUES (%s, %s, %s, %s)
                """

        query_params = (
            int(client_info["client_id"]),
            client_info["poc_name"],
            client_info["poc_phone_number"],
            client_info["poc_email"],
        )

        mycursor.execute(query, query_params)
        connection.commit()
        print("Client POC created")

    except MySQLdb.Error as e:
        print("MySQL Error:", e)


def update_client(client_info):
    try:
        # Client Update
        mycursor = connection.cursor()
        query = f"""UPDATE clients
                    SET name = %s, address = %s, city = %s, state = %s, zip_code = %s, website = %s, phone_number = %s
                    WHERE client_id = %s;
                """
        query_params = (
            client_info["name"],
            client_info["address"],
            client_info["city"],
            client_info["state"],
            client_info["zip_code"],
            client_info["website"],
            client_info["phone_number"],
            client_info["client_id"],
        )
        mycursor.execute(query, query_params)
        connection.commit()

        # POC Update
        if client_info["poc_exists"]:
            query = f"""UPDATE client_poc
                        SET name = %s, telephone = %s, email = %s
                        WHERE client_id = %s;
                    """
            query_params = (
                client_info["poc_name"],
                client_info["poc_phone_number"],
                client_info["poc_email"],
                client_info["client_id"],
            )
            mycursor.execute(query, query_params)
            connection.commit()
            print("Client POC updated")
        else:
            create_client_poc(client_info)

    except MySQLdb.Error as e:
        print("MySQL Error:", e)


############## Project Queries ##############
def get_all_projects():
    try:
        return get_results(
            f"""
                SELECT projects.*, clients.name
                FROM projects
                INNER JOIN clients
                ON projects.client_id = clients.client_id;
            """
        )
    except:
        return ""


def get_project(project_id):
    try:
        return get_results(
            f"""
                SELECT projects.*, clients.name
                FROM projects
                INNER JOIN clients
                ON projects.client_id = clients.client_id
                WHERE projects.project_id = '{project_id}';
            """
        )[0]
    except:
        return ""


def create_project(project_info):
    try:
        mycursor = connection.cursor()
        query = f"""INSERT INTO projects (project_id, client_id, name, address, city, state, zip_code, county)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

        query_params = (
            project_info["project_id"],
            project_info["client"],
            project_info["name"],
            project_info["address"],
            project_info["city"],
            project_info["state"],
            project_info["zip_code"],
            project_info["county"],
        )

        mycursor.execute(query, query_params)
        connection.commit()
        print("Project created")

    except MySQLdb.Error as e:
        print("MySQL Error:", e)


def get_client_projects(client_id):
    try:
        return get_results(
            f"""
                SELECT *
                FROM projects
                WHERE client_id = {client_id};
            """
        )
    except:
        return ""


############## Permits Queries ##############
def get_master_permit(project_id):
    try:
        master_permit = get_results(
            f"""
                SELECT *
                FROM permits
                WHERE project_id = '{project_id}' AND permit_type = 'MASTER';
            """
        )[0]

        return master_permit

    except:
        return ""


def get_plumbing_permit(project_id):
    try:
        plumbing_permit = get_results(
            f"""
                SELECT *
                FROM permits
                WHERE project_id = '{project_id}' AND permit_type != 'MASTER';
            """
        )[0]

        return plumbing_permit
    except:
        return ""


def insert_master_permit(project_id, permit_number):
    try:
        mycursor = connection.cursor()
        query = f"""INSERT INTO permits (project_id, permit_number, permit_type, assigned_date, status, status_date)
                VALUES (%s, %s, %s, %s, %s, %s)"""

        query_params = (
            project_id,
            permit_number,
            "MASTER",
            TODAY,
            "ASSIGNED",
            TODAY,
        )

        mycursor.execute(query, query_params)
        connection.commit()
        print("Permit inserted")

    except MySQLdb.Error as e:
        print("MySQL Error:", e)


############## Notes Queries ##############
def get_notes(project_id):
    try:
        return get_results(
            f"""
                SELECT project_notes.*, users.first_name, users.last_name
                FROM project_notes
                INNER JOIN users
                ON project_notes.user_id = users.user_id
                WHERE project_notes.project_id = '{project_id}';
            """
        )
    except:
        return ""


def insert_note(project_id, note, user_id):
    try:
        mycursor = connection.cursor()
        query = f"""INSERT INTO project_notes (project_id, comment, comment_date, user_id)
                VALUES (%s, %s, %s, %s)"""

        query_params = (
            project_id,
            note,
            datetime.today(),
            user_id,
        )

        mycursor.execute(query, query_params)
        connection.commit()
        print("Note addded")

    except MySQLdb.Error as e:
        print("MySQL Error:", e)


############## Invoices Queries ##############
def get_invoices(project_id):
    try:
        return get_results(
            f"""
                SELECT * 
                FROM project_invoices
                WHERE project_id = '{project_id}';
            """
        )
    except:
        return ""


############## Document Queries ##############
def get_project_docs(project_id):
    try:
        return get_results(
            f"""
                SELECT project_documents.*, users.first_name, users.last_name
                FROM project_documents
                INNER JOIN users
                ON project_documents.user_id = users.user_id
                WHERE project_documents.project_id = {project_id}
            """
        )
    except:
        return ""


def upload_document(project_id, document_type, comment, user_id, filename):
    try:
        mycursor = connection.cursor()
        query = f"""INSERT INTO project_documents (project_id, type, comment, user_id, filename)
                VALUES (%s, %s, %s, %s, %s)"""

        query_params = (
            project_id,
            document_type,
            comment,
            user_id,
            filename,
        )

        mycursor.execute(query, query_params)
        connection.commit()
        print("Document addded")

    except MySQLdb.Error as e:
        print("MySQL Error:", e)


############## Search Queries ##############
def search(search_by, search_criteria):
    try:
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
    except:
        return None


############## Misc. Queries ##############
def get_city_state_county(zip_code):
    try:
        return get_results(
            f"""
                SELECT primary_city, state, county
                FROM zip_code_county
                WHERE zip = {zip_code};
            """
        )
    except:
        return ""
