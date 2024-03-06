import os
import uuid
from datetime import datetime, date

import MySQLdb
from dotenv import load_dotenv
from flask_login import UserMixin
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from werkzeug.utils import secure_filename

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


############## Project Status Queries ##############
def update_project_status(project_id, project_status, user_id):
    try:
        # Client Update
        mycursor = connection.cursor()
        query = f"""UPDATE projects
                    SET status = %s, status_date = %s
                    WHERE project_id = %s;
                """
        query_params = (
            project_status,
            datetime.now().strftime("%Y-%m-%d"),
            project_id,
        )
        mycursor.execute(query, query_params)
        connection.commit()

        insert_note(project_id, f"Project status updated: {project_status}", user_id)

        if "Phase" in project_status:
            installment_number = int(project_status[-1]) - 1

            if installment_number <= 0:
                return

            # TODO: Replace this call if needed
            # update_installment_status(
            #     project_id, installment_number, "Ready", user_id, True
            # )

    except MySQLdb.Error as e:
        print("MySQL Error:", e)


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


############## Invoices/Installment Queries ##############
def get_invoices(project_id):
    try:
        return get_results(
            f"""
                SELECT * 
                FROM project_invoices
                WHERE project_id = '{project_id}'
                ORDER BY invoice_number;
            """
        )
    except:
        return ""


def get_open_invoices(project_id, installment_number):
    try:
        open_invoices = get_results(
            f"""
                SELECT * 
                FROM project_invoices
                WHERE project_id = '{project_id}' AND installment_number <= {installment_number} AND installment_status != "Paid";
            """
        )
        for invoice in open_invoices:
            if int(invoice["installment_number"]) < int(installment_number):
                invoice["installment_description"] += " (Past Due)"

        return open_invoices
    except:
        return ""


def get_invoice(project_id, installment_number):
    try:
        return get_results(
            f"""
                SELECT * 
                FROM project_invoices
                WHERE project_id = '{project_id}' and installment_number = {installment_number};
            """
        )[0]
    except:
        return ""


def get_invoice_items(project_id, installment_number):
    try:
        return get_results(
            f"""
                SELECT * 
                FROM project_invoice_items
                WHERE project_id = '{project_id}' and installment_number = {installment_number};
            """
        )
    except:
        return ""


def get_open_invoice_items(project_id, installment_number):
    try:
        return get_results(
            f"""
                SELECT * 
                FROM project_invoice_items
                WHERE project_id = '{project_id}' AND installment_number <= {installment_number};
            """
        )
    except:
        return ""


def get_invoice_payments_total(invoice_id):
    try:
        x = get_results(
            f"""
                SELECT SUM(payment_amount)
                FROM invoice_payments
                WHERE invoice_id = {invoice_id};
            """
        )
        return float(x[0]["sum(payment_amount)"])
    except:
        return ""


def insert_payment(payment_info):
    try:
        mycursor = connection.cursor()
        query = f"""INSERT INTO invoice_payments (invoice_id, payment_method, check_number, payment_amount, date_received, payment_note)
                VALUES (%s, %s, %s, %s, %s, %s)"""

        query_params = (
            payment_info["invoice_id"],
            payment_info["payment_method"],
            payment_info["check_number"],
            payment_info["payment_amount"],
            payment_info["date_received"],
            payment_info["payment_note"],
        )

        mycursor.execute(query, query_params)
        connection.commit()
        print("Payment addded")

    except MySQLdb.Error as e:
        print("MySQL Error:", e)


def get_invoice_payments(invoice_id):
    try:
        return get_results(
            f"""
                SELECT *
                FROM invoice_payments
                WHERE invoice_id = {invoice_id};
            """
        )
    except:
        return ""


def get_next_invoice_number(project_id):
    try:
        max_invoice = get_results(
            f"""
                SELECT MAX(invoice_id) as curr_inv
                FROM project_invoices
                WHERE project_id = '{project_id}';
            """
        )[0]["curr_inv"]

        if not max_invoice:
            max_invoice = 0

        return max_invoice + 1
    except:
        return ""


def create_invoice(selected_installments, project_id):
    next_invoice_number = get_next_invoice_number(project_id)
    invoice_total = 0

    print(f"{next_invoice_number=}")
    print(f"{selected_installments=}")

    for installment in selected_installments:
        try:
            # Installment Update
            mycursor = connection.cursor()
            query = f"""UPDATE project_installments
                        SET invoice_number = %s, installment_status = %s, installment_status_date = %s
                        WHERE project_id = %s AND installment_id = %s;
                    """
            query_params = (
                next_invoice_number,
                "Billed",
                datetime.now().strftime("%Y-%m-%d"),
                project_id,
                int(installment),
            )

            mycursor.execute(query, query_params)
            connection.commit()

            # insert_note(
            #     project_id,
            #     f"Installment #{installment_number} status updated: {installment_status}",
            #     user_id,
            # )

        except MySQLdb.Error as e:
            print("MySQL Error:", e)

    # Get Invoice Total
    invoice_total = get_results(
        f"""
            SELECT SUM(installment_amount) as inv_total
            FROM project_installments
            WHERE project_id = '{project_id}' AND invoice_number = {next_invoice_number}; 
        """
    )[0]["inv_total"]

    print(f"{invoice_total=}")

    # Invoice Create
    try:
        mycursor = connection.cursor()
        query = f"""
                    INSERT INTO project_invoices (project_id, invoice_number, billed_date, invoice_amount, invoice_status)
                    VALUES (%s, %s, %s, %s, %s)
                """

        query_params = (
            project_id,
            next_invoice_number,
            datetime.now().strftime("%Y-%m-%d"),
            invoice_total,
            "Billed",
        )

        mycursor.execute(query, query_params)
        connection.commit()
        print("Invoice Created")

    except MySQLdb.Error as e:
        print("MySQL Error:", e)


def get_installments(project_id):
    try:
        return get_results(
            f"""
                SELECT *
                FROM project_installments
                WHERE project_id = '{project_id}';
            """
        )
    except:
        return ""


def update_installment_status(
    project_id, installment_number, installment_status, user_id, phase_update=False
):
    try:
        # Client Update
        mycursor = connection.cursor()
        query = f"""UPDATE project_invoices
                    SET installment_status = %s, installment_status_date = %s
                    WHERE project_id = %s AND installment_number = %s;
                """
        query_params = (
            installment_status,
            datetime.now().strftime("%Y-%m-%d"),
            project_id,
            installment_number,
        )

        if phase_update:
            query = f"""UPDATE project_invoices
                        SET installment_status = %s, installment_status_date = %s
                        WHERE project_id = %s AND installment_number = %s AND installment_status = %s;
                    """
            query_params = (
                installment_status,
                datetime.now().strftime("%Y-%m-%d"),
                project_id,
                installment_number,
                "Pending",
            )
        mycursor.execute(query, query_params)
        connection.commit()

        # insert_note(
        #     project_id,
        #     f"Installment #{installment_number} status updated: {installment_status}",
        #     user_id,
        # )

    except MySQLdb.Error as e:
        print("MySQL Error:", e)


############## Document Queries ##############
def get_project_docs(project_id):
    try:
        return get_results(
            f"""
                SELECT project_documents.*, users.first_name, users.last_name
                FROM project_documents
                INNER JOIN users
                ON project_documents.user_id = users.user_id
                WHERE project_documents.project_id = '{project_id}'
                ORDER BY project_documents.upload_date DESC;
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
            secure_filename(filename),
        )

        mycursor.execute(query, query_params)
        connection.commit()

        # insert_note(
        #     project_id, f"{document_type} has been uploaded (Auto Note)", user_id
        # )

        print("Document addded")

    except MySQLdb.Error as e:
        print("MySQL Error:", e)


def get_document_types():
    try:
        get_types = get_results(
            f"""
                SELECT document_type
                FROM matrix_document_types
                ORDER BY document_type;
            """
        )
        doc_types = [doc_type["document_type"] for doc_type in get_types]
        return doc_types
    except:
        return ""


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


def get_project_statuses():
    try:
        get_statuses = get_results(
            f"""
                SELECT project_status, order_number
                FROM matrix_project_statuses
                WHERE project_status != 'Project Created'
                ORDER BY order_number;
            """
        )
        statuses = [status["project_status"] for status in get_statuses]
        return statuses
    except:
        return ""
