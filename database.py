import os
import uuid
from datetime import datetime, date

import MySQLdb
from dotenv import load_dotenv
from flask_login import UserMixin
from sqlalchemy import create_engine, text, insert
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from werkzeug.utils import secure_filename

# from supabase import create_client, Client

load_dotenv()

TODAY = datetime.today().strftime("%Y-%m-%d")

url: str = os.environ.get("SUPABASE_URL")
password: str = os.environ.get("SUPABASE_PWD")
db_name: str = os.environ.get("SUPABASE_DB_NAME")
host: str = os.environ.get("SUPABASE_HOST")

DB_CONNECTION_STRING = f"postgresql+psycopg2://{url}:{password}@{host}:5432/{db_name}"
engine = create_engine(DB_CONNECTION_STRING)

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
        # cursor = connection.cursor(MySQLdb.cursors.DictCursor)
        # cursor.execute(sqlQuery)
        # results = cursor.fetchall()

        with engine.connect() as connection:
            results = connection.execute(text(f"{sqlQuery}")).all()
        return results
    except Exception as e:
        print("Database Error:", e)
        return ""


############## User Queries ##############
def get_user(user_id):
    try:
        sqlQuery = f"""
                SELECT * FROM users WHERE users.user_id = '{user_id}'; 
            """

        with engine.connect() as connection:
            user = connection.execute(text(f"{sqlQuery}")).first()

        return user
    except Exception as e:
        print("Database Error:", e)
        return ""


def get_user_password(email):
    try:
        sqlQuery = f"""
                SELECT password
                FROM users
                WHERE users.email = '{email}'
            """

        with engine.connect() as connection:
            password = connection.execute(text(f"{sqlQuery}")).first()[0]

        return password
    except Exception as e:
        print("Database Error:", e)
        return ""


def get_user_from_email(email):
    try:
        sqlQuery = f"""
                SELECT *
                FROM users
                WHERE users.email = '{email}'
            """

        with engine.connect() as connection:
            results = connection.execute(text(f"{sqlQuery}"))
            user_dict = results.mappings().all()[0]

        return user_dict
    except Exception as e:
        print("Database Error:", e)
        return ""


def create_user(user_info):
    try:
        sqlQuery = (
            "INSERT INTO users (user_id, first_name, last_name, email, password)"
            + " VALUES (:user_id, :first_name, :last_name, :email, :password)"
        )

        query_params = {
            "user_id": str(uuid.uuid4()),
            "first_name": user_info["first_name"],
            "last_name": user_info["last_name"],
            "email": user_info["email"],
            "password": user_info["password"],
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("User created")

    except Exception as e:
        print("Database Error:", e)
        return ""


############## Client Queries ##############
def get_client(client_id):
    try:
        sqlQuery = "SELECT * FROM clients WHERE client_id = :client_id;"

        queryParams = {
            "client_id": client_id,
        }

        with engine.connect() as connection:
            client = connection.execute(text(f"{sqlQuery}"), queryParams)
            client_dict = dict(client.mappings().all()[0])

        return client_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_client_poc(client_id):
    try:
        sqlQuery = "SELECT * FROM client_poc WHERE client_id = :client_id;"
        query_params = {
            "client_id": client_id,
        }

        with engine.connect() as connection:
            poc = connection.execute(text(f"{sqlQuery}"), query_params)

            poc_dict = poc.mappings().all()[0]

        return poc_dict
    except Exception as e:
        print("get_client_poc() - Database Error:", e)
        return ""


def get_all_clients():
    try:
        sqlQuery = (
            "SELECT clients.*, count(project_id) AS project_count"
            + " FROM clients"
            + " LEFT JOIN projects ON clients.client_id = projects.client_id"
            + " GROUP BY clients.client_id"
            + " ORDER BY name"
        )

        with engine.connect() as connection:
            clients = connection.execute(text(f"{sqlQuery}"))
            clients_dict = clients.mappings().all()

        return clients_dict
    except Exception as e:
        print("Database Error:", e)
        return ""


def create_client(client_info):
    try:
        sqlQuery = (
            "INSERT INTO clients (name, address, city, state, zip_code, website, phone_number)"
            + " VALUES (:name, :address, :city, :state, :zip_code, :website, :phone_number)"
        )

        query_params = {
            "name": client_info["name"],
            "address": client_info["address"],
            "city": client_info["city"],
            "state": client_info["state"],
            "zip_code": client_info["zip_code"],
            "website": client_info["website"],
            "phone_number": client_info["phone_number"],
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Client created")

        # create_client_poc(client_info)

    except Exception as e:
        print("Database Error:", e)
        return ""


def create_client_poc(client_info):
    try:
        sqlQuery = (
            "INSERT INTO client_poc (client_id, name, telephone, email)"
            + " VALUES (:client_id, :name, :telephone, :email)"
        )

        query_params = {
            "client_id": client_info["client_id"],
            "name": client_info["poc_name"],
            "telephone": client_info["poc_phone_number"],
            "email": client_info["poc_email"],
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Client POC created")

    except Exception as e:
        print("Database Error:", e)
        return ""


def update_client(client_info):
    try:
        sqlQuery = (
            "UPDATE clients"
            + " SET name = :name, address = :address, city = :city, state = :state, zip_code = :zip_code, website = :website, phone_number = :phone_number"
            + " WHERE client_id = :client_id;"
        )

        query_params = {
            "name": client_info["name"],
            "address": client_info["address"],
            "city": client_info["city"],
            "state": client_info["state"],
            "zip_code": client_info["zip_code"],
            "website": client_info["website"],
            "phone_number": client_info["phone_number"],
            "client_id": client_info["client_id"],
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Client updated")

        # POC Update
        if client_info["poc_exists"]:
            sqlQuery = (
                "UPDATE client_poc"
                + " SET name = :name, telephone = :telephone, email = :email"
                + " WHERE client_id = :client_id;"
            )

            query_params = {
                "name": client_info["poc_name"],
                "telephone": client_info["poc_phone_number"],
                "email": client_info["poc_email"],
                "client_id": client_info["client_id"],
            }

            with engine.connect() as connection:
                result = connection.execute(text(f"{sqlQuery}"), query_params)
                connection.commit()

            print("Client POC updated")
        else:
            create_client_poc(client_info)

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_project_client(project_id):
    project = get_project(project_id)
    return get_client(project["client_id"])


############## Project Queries ##############
def get_all_projects():
    try:
        sqlQuery = f"""
                SELECT projects.*, clients.name as client_name
                FROM projects
                INNER JOIN clients
                ON projects.client_id = clients.client_id;
            """

        with engine.connect() as connection:
            projects = connection.execute(text(f"{sqlQuery}"))
            projects_dict = projects.mappings().all()

        return projects_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_project(project_id):
    try:
        sqlQuery = (
            "SELECT projects.*, clients.name as client_name"
            + " FROM projects"
            + " INNER JOIN clients"
            + " ON projects.client_id = clients.client_id"
            + " WHERE projects.project_id = :project_id;"
        )

        query_params = {
            "project_id": project_id,
        }

        with engine.connect() as connection:
            project = connection.execute(text(f"{sqlQuery}"), query_params)
            project_dict = dict(project.mappings().all()[0])

        return project_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def create_project(project_info):
    try:
        sqlQuery = (
            "INSERT INTO projects (project_id, client_id, name, address, city, state, zip_code, county)"
            + " VALUES (:project_id, :client_id, :name, :address, :city, :state, :zip_code, :county)"
        )

        query_params = {
            "project_id": project_info["project_id"],
            "client_id": project_info["client"],
            "name": project_info["name"],
            "address": project_info["address"],
            "city": project_info["city"],
            "state": project_info["state"],
            "zip_code": project_info["zip_code"],
            "county": project_info["county"],
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Project created")

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_client_projects(client_id):
    try:
        sqlQuery = "SELECT *" + " FROM projects" + " WHERE client_id = :client_id;"

        query_params = {
            "client_id": client_id,
        }

        with engine.connect() as connection:
            projects = connection.execute(text(f"{sqlQuery}"), query_params)
            projects_dict = ""
            if projects:
                projects_dict = projects.mappings().all()

        return projects_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_max_project_id():
    try:
        sqlQuery = f"""
                SELECT MAX(project_id)
                FROM projects
                WHERE project_id != '24-9999';
            """

        with engine.connect() as connection:
            max_id = connection.execute(text(f"{sqlQuery}"))
            max_id = max_id.mappings().first()["max"]

        return max_id

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_next_project_id():
    current_max_id = get_max_project_id()
    curr_year = str(datetime.now().strftime("%y"))
    next_id = int(current_max_id.split("-")[1]) + 1
    next_id_complete = curr_year + "-" + str(next_id)
    return next_id_complete


############## Project Status Queries ##############
def update_project_status(project_id, project_status, user_id):
    try:
        sqlQuery = (
            "UPDATE projects"
            + " SET status = :status, status_date = :status_date"
            + " WHERE project_id = :project_id;"
        )

        query_params = {
            "status": project_status,
            "status_date": datetime.now().strftime("%Y-%m-%d"),
            "project_id": project_id,
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Project status updated")

        #     insert_note(project_id, f"Project status updated: {project_status}", user_id)

        #     if "Phase" in project_status:
        #         installment_number = int(project_status[-1]) - 1

        #         if installment_number <= 0:
        #             return

        #         # TODO: Replace this call if needed
        #         # update_installment_status(
        #         #     project_id, installment_number, "Ready", user_id, True
        #         # )

    except Exception as e:
        print("Database Error:", e)
        return ""


############## Permits Queries ##############
def get_master_permit(project_id):
    try:
        sqlQuery = (
            "SELECT *"
            + " FROM permits"
            + " WHERE project_id = :project_id AND permit_type = 'MASTER';"
        )

        queryParams = {
            "project_id": project_id,
        }

        with engine.connect() as connection:
            master_permit = connection.execute(text(f"{sqlQuery}"), queryParams)
            try:
                master_permit_dict = master_permit.mappings().all()[0]
            except:
                master_permit_dict = ""

        return master_permit_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_plumbing_permit(project_id):
    try:
        sqlQuery = (
            "SELECT *"
            + " FROM permits"
            + " WHERE project_id = :project_id AND permit_type != 'MASTER';"
        )

        queryParams = {
            "project_id": project_id,
        }

        with engine.connect() as connection:
            plumbing_permit = connection.execute(text(f"{sqlQuery}"), queryParams)
            try:
                plumbing_permit_dict = plumbing_permit.mappings().all()[0]
            except:
                plumbing_permit_dict = ""

        return plumbing_permit_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def insert_master_permit(project_id, permit_number):
    try:
        sqlQuery = (
            "INSERT INTO permits (project_id, permit_number, permit_type, assigned_date, status, status_date)"
            + " VALUES (:project_id, :permit_number, :permit_type, :assigned_date, :status, :status_date)"
        )

        query_params = {
            "project_id": project_id,
            "permit_number": permit_number,
            "permit_type": "MASTER",
            "assigned_date": TODAY,
            "status": "ASSIGNED",
            "status_date": TODAY,
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Master permit inserted")

    except Exception as e:
        print("Database Error:", e)
        return ""


############## Notes Queries ##############
def get_notes(project_id):
    try:
        sqlQuery = (
            "SELECT project_notes.*, users.first_name, users.last_name"
            + " FROM project_notes"
            + " INNER JOIN users"
            + " ON project_notes.user_id = users.user_id"
            + " WHERE project_notes.project_id = :project_id;"
        )

        query_params = {
            "project_id": project_id,
        }

        with engine.connect() as connection:
            notes = connection.execute(text(f"{sqlQuery}"), query_params)
            try:
                notes_dict = notes.mappings().all()
            except:
                notes_dict = ""

        return notes_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def insert_note(project_id, note, user_id):
    try:
        sqlQuery = (
            "INSERT INTO project_notes (project_id, comment, comment_date, user_id)"
            + " VALUES (:project_id, :comment, :comment_date, :user_id)"
        )

        query_params = {
            "project_id": project_id,
            "comment": note,
            "comment_date": datetime.today(),
            "user_id": user_id,
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Comment added")

    except Exception as e:
        print("Database Error:", e)
        return ""


############## Invoices/Installment Queries ##############
def get_invoices(project_id):
    try:
        sqlQuery = (
            "SELECT *"
            + " FROM project_invoices"
            + " WHERE project_id = :project_id"
            + " ORDER BY invoice_number;"
        )

        query_params = {
            "project_id": project_id,
        }

        with engine.connect() as connection:
            invoices = connection.execute(text(f"{sqlQuery}"), query_params)
            try:
                invoices_dict = invoices.mappings().all()
            except:
                invoices_dict = ""

        return invoices_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_open_invoices(project_id, invoice_number):
    try:
        sqlQuery = (
            "SELECT *"
            + " FROM project_invoices"
            + " WHERE project_id = :project_id AND invoice_number <= :invoice_number AND invoice_status != 'Paid';"
        )

        query_params = {
            "project_id": project_id,
            "invoice_number": int(invoice_number),
        }

        with engine.connect() as connection:
            invoices = connection.execute(text(f"{sqlQuery}"), query_params)
            try:
                invoices_dict = invoices.mappings().all()
            except:
                invoices_dict = ""

        return invoices_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_invoice(project_id, invoice_number):
    try:
        sqlQuery = (
            "SELECT * "
            + " FROM project_invoices"
            + " WHERE project_id = :project_id and invoice_number = :invoice_number;"
        )

        query_params = {
            "project_id": project_id,
            "invoice_number": int(invoice_number),
        }

        with engine.connect() as connection:
            invoice = connection.execute(text(f"{sqlQuery}"), query_params)
            invoice_dict = invoice.mappings().all()[0]

        return invoice_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_invoice_items(project_id, invoice_number):
    try:
        sqlQuery = (
            "SELECT project_invoice_items.*, project_installments.installment_description, project_installments.installment_amount"
            + " FROM project_invoice_items"
            + " INNER JOIN project_installments"
            + " ON (project_invoice_items.project_id = project_installments.project_id AND project_invoice_items.installment_number = project_installments.installment_number)"
            + " WHERE project_invoice_items.project_id = :project_id and project_invoice_items.invoice_number = :invoice_number;"
        )

        query_params = {
            "project_id": project_id,
            "invoice_number": int(invoice_number),
        }

        with engine.connect() as connection:
            project = connection.execute(text(f"{sqlQuery}"), query_params)
            project_dict = project.mappings().all()

        return project_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_open_invoice_items(project_id, invoice_number):
    try:
        sqlQuery = (
            "SELECT * "
            + " FROM project_invoice_items"
            + " WHERE project_id = :project_id and invoice_number <= :invoice_number;"
        )

        query_params = {
            "project_id": project_id,
            "invoice_number": int(invoice_number),
        }

        with engine.connect() as connection:
            invoice_items = connection.execute(text(f"{sqlQuery}"), query_params)
            invoice_items_dict = invoice_items.mappings().all()

        return invoice_items_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_open_invoices(project_id):
    try:
        sqlQuery = (
            "SELECT *"
            + " FROM project_invoices"
            + " WHERE project_id = :project_id and invoice_status != 'Paid'"
            + " ORDER BY invoice_id;"
        )

        query_params = {
            "project_id": project_id,
        }

        with engine.connect() as connection:
            open_invoices = connection.execute(text(f"{sqlQuery}"), query_params)
            open_invoices_dict = open_invoices.mappings().all()

        return open_invoices_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_invoice_payments_total(invoice_id):
    # print(f"{invoice_id=}")
    try:
        # sqlQuery = (
        #     "SELECT invoice_payments.*, project_payments.*"
        #     + " FROM invoice_payments"
        #     + " INNER JOIN project_payments ON invoice_payments.project_id = project_payments.project_id"
        #     + " WHERE invoice_payments.invoice_id = :invoice_id"
        # )

        sqlQuery = (
            "SELECT SUM(amount_applied)"
            + " FROM invoice_payments"
            + " WHERE invoice_id = :invoice_id"
        )

        query_params = {
            "invoice_id": invoice_id,
        }

        with engine.connect() as connection:
            invoice_items = connection.execute(text(f"{sqlQuery}"), query_params)
            invoice_items_dict = invoice_items.mappings().all()[0]

            # print(f"{invoice_items_dict=}")

            return float(invoice_items_dict["sum"])
            # return invoice_items_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def insert_payment(payment_info):
    try:
        sqlQuery = (
            "INSERT INTO project_payments (project_id, payment_method, check_number, payment_amount, date_received, payment_note)"
            + " VALUES (:project_id, :payment_method, :check_number, :payment_amount, :date_received, :payment_note)"
        )

        query_params = {
            "project_id": payment_info["project_id"],
            "payment_method": payment_info["payment_method"],
            "check_number": payment_info["check_number"],
            "payment_amount": payment_info["payment_amount"],
            "date_received": payment_info["date_received"],
            "payment_note": payment_info["payment_note"],
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Payment added")

    except Exception as e:
        print("Database Error:", e)
        return ""


def invoice_received_amount(invoice_id):
    try:
        sqlQuery = (
            "SELECT payment_received"
            + " FROM project_invoices"
            + " WHERE invoice_id = :invoice_id"
        )

        query_params = {
            "invoice_id": invoice_id,
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params).first()
            connection.commit()
            return result[0]

    except Exception as e:
        print("Database Error:", e)


def apply_payment(invoice_info):
    amount_received = invoice_received_amount(invoice_info["invoice_id"])
    # Update the invoice information
    try:
        sqlQuery = (
            "UPDATE project_invoices"
            + " SET payment_received = :payment_received, payment_remaining = :payment_remaining, invoice_status = :invoice_status, invoice_status_date = :invoice_status_date"
            + " WHERE invoice_id = :invoice_id;"
        )

        query_params = {
            "invoice_id": invoice_info["invoice_id"],
            "payment_received": invoice_info["payment_received"] + amount_received,
            "payment_remaining": invoice_info["payment_remaining"],
            "invoice_status": invoice_info["invoice_status"],
            "invoice_status_date": invoice_info["date_received"],
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        # print("Payment added")

    except Exception as e:
        print("Database Error:", e)
        return ""

    # Insert the payment line items
    project_payment_id = get_project_payment_id(invoice_info)

    sqlQuery = (
        "INSERT INTO invoice_payments (invoice_id, amount_applied, project_id, check_number, project_payment_id)"
        + " VALUES (:invoice_id, :amount_applied, :project_id, :check_number, :project_payment_id)"
    )
    try:
        query_params = {
            "invoice_id": invoice_info["invoice_id"],
            "amount_applied": invoice_info["payment_received"],
            "project_id": invoice_info["project_id"],
            "check_number": invoice_info["check_number"],
            "project_payment_id": project_payment_id,
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Payment added")

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_project_payment_id(invoice_info):
    sqlQuery = "SELECT project_payment_id FROM project_payments WHERE check_number = :check_number AND project_id = :project_id;"
    try:
        query_params = {
            "check_number": invoice_info["check_number"],
            "project_id": invoice_info["project_id"],
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params).first()
            return result[0]

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_project_payments(project_id):
    try:
        sqlQuery = (
            "SELECT * "
            + " FROM project_payments"
            + " WHERE project_id = :project_id"
            + " ORDER BY date_received;"
        )

        query_params = {
            "project_id": project_id,
        }

        with engine.connect() as connection:
            project_payments = connection.execute(text(f"{sqlQuery}"), query_params)
            project_payments_dict = project_payments.mappings().all()

        return project_payments_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_payment_installments(project_id):
    try:
        # sqlQuery = "SELECT * FROM project_installments INNER JOIN project_payments ON project_installments.project_id = project_payments.project_id WHERE project_payments.project_id = :project_id;"
        sqlQuery = "select * from invoice_payments inner join project_invoices on invoice_payments.invoice_id = project_invoices.invoice_id where invoice_payments.project_id = :project_id;"

        query_params = {
            "project_id": project_id,
        }

        with engine.connect() as connection:
            payment_installments = connection.execute(text(f"{sqlQuery}"), query_params)
            payment_installments_dict = payment_installments.mappings().all()

        return payment_installments_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_invoice_payments(invoice_id):
    try:
        # sqlQuery = (
        #     "SELECT * " + " FROM invoice_payments" + " WHERE invoice_id = :invoice_id;"
        # )
        sqlQuery = "SELECT * FROM invoice_payments INNER JOIN project_payments ON invoice_payments.project_payment_id = project_payments.project_payment_id WHERE invoice_payments.invoice_id = :invoice_id;"

        query_params = {
            "invoice_id": invoice_id,
        }

        with engine.connect() as connection:
            invoice_payments = connection.execute(text(f"{sqlQuery}"), query_params)
            invoice_payments_dict = invoice_payments.mappings().all()

        return invoice_payments_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_installment_number(project_id, installment_id):
    try:
        sqlQuery = (
            "SELECT installment_number "
            + " FROM project_installments"
            + " WHERE project_id = :project_id AND installment_id = :installment_id;"
        )

        query_params = {
            "project_id": project_id,
            "installment_id": installment_id,
        }

        with engine.connect() as connection:
            installment_number = connection.execute(text(f"{sqlQuery}"), query_params)

        return installment_number.first()[0]

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_next_invoice_number(project_id):
    try:
        sqlQuery = (
            "SELECT MAX(invoice_number) AS curr_inv"
            + " FROM project_invoices"
            + " WHERE project_id = :project_id;"
        )

        query_params = {
            "project_id": project_id,
        }

        with engine.connect() as connection:
            max_invoice = connection.execute(text(f"{sqlQuery}"), query_params)
            max_invoice = max_invoice.mappings().all()[0]["curr_inv"]

            if not max_invoice:
                max_invoice = 0

        # return invoice_payments_dict
        return max_invoice + 1

    except Exception as e:
        print("Database Error:", e)
        return ""


def create_invoice(selected_invoices, project_id):
    next_invoice_number = get_next_invoice_number(project_id)
    invoice_total = 0

    for installment in selected_invoices:
        installment_id = installment[0]
        user_amount = installment[1]
        installment_amount = installment[2]
        billed_amount = installment[3]

        installment_number = get_installment_number(project_id, installment_id)

        installment_status = (
            "Billed"
            if (billed_amount + user_amount) == installment_amount
            else "Partial Billed"
        )

        # Installment Update
        try:
            sqlQuery = (
                "UPDATE project_installments"
                + " SET invoice_number = :invoice_number, installment_status = :installment_status, installment_status_date = :installment_status_date, billed_amount = :billed_amount"
                + " WHERE project_id = :project_id AND installment_id = :installment_id;"
            )

            query_params = {
                "invoice_number": next_invoice_number,
                "installment_status": installment_status,
                "installment_status_date": datetime.now().strftime("%Y-%m-%d"),
                "project_id": project_id,
                "installment_id": installment_id,
                "billed_amount": billed_amount + user_amount,
            }

            with engine.connect() as connection:
                result = connection.execute(text(f"{sqlQuery}"), query_params)
                connection.commit()

            print("Installment updated")

        except Exception as e:
            print("Database Error:", e)

        # Invoice Items Append
        try:
            sqlQuery = (
                "INSERT INTO project_invoice_items (project_id, installment_number, item_amount, invoice_number)"
                + " VALUES (:project_id, :installment_number, :item_amount, :invoice_number)"
            )

            query_params = {
                "project_id": project_id,
                "installment_number": installment_number,
                "item_amount": user_amount,
                "invoice_number": next_invoice_number,
            }

            with engine.connect() as connection:
                result = connection.execute(text(f"{sqlQuery}"), query_params)
                connection.commit()

            print("Invoice items appended")
        except Exception as e:
            print("Database Error:", e)

    # Get Invoice Total
    try:
        invoice_items = get_invoice_items(project_id, next_invoice_number)

        for item in invoice_items:
            invoice_total += item["item_amount"]

        print(f"{invoice_items=}")

    except Exception as e:
        print("Database Error:", e)

    # Invoice Create
    try:
        sqlQuery = (
            "INSERT INTO project_invoices (project_id, invoice_number, billed_date, invoice_amount, invoice_status, payment_remaining)"
            + " VALUES (:project_id, :invoice_number, :billed_date, :invoice_amount, :invoice_status, :payment_remaining)"
        )

        query_params = {
            "project_id": project_id,
            "invoice_number": next_invoice_number,
            "billed_date": datetime.now().strftime("%Y-%m-%d"),
            "invoice_amount": invoice_total,
            "invoice_status": "Billed",
            "payment_remaining": invoice_total,
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Invoice created")

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_installments(project_id):
    try:
        sqlQuery = (
            "SELECT *"
            + " FROM project_installments"
            + " WHERE project_id = :project_id"
            + " ORDER BY installment_number;"
        )

        query_params = {
            "project_id": project_id,
        }

        with engine.connect() as connection:
            installments = connection.execute(text(f"{sqlQuery}"), query_params)
            installments_dict = installments.mappings().all()

        return installments_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def update_installment_status(
    project_id, installment_number, installment_status, user_id, phase_update=False
):
    try:
        sqlQuery = (
            "UPDATE project_invoices"
            + " SET installment_status = :installment_status, installment_status_date = :installment_status_date"
            + " WHERE project_id = :project_id AND installment_number = :installment_number;"
        )

        query_params = {
            "installment_status": installment_status,
            "installment_status_date": datetime.now().strftime("%Y-%m-%d"),
            "project_id": project_id,
            "installment_number": installment_number,
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Installment updated")

    except Exception as e:
        print("Database Error:", e)
        return ""
    # try:
    #     if phase_update:
    #         query = f"""UPDATE project_invoices
    #                     SET installment_status = %s, installment_status_date = %s
    #                     WHERE project_id = %s AND installment_number = %s AND installment_status = %s;
    #                 """
    #         query_params = (
    #             installment_status,
    #             datetime.now().strftime("%Y-%m-%d"),
    #             project_id,
    #             installment_number,
    #             "Pending",
    #         )
    #     mycursor.execute(query, query_params)
    #     connection.commit()

    #     # insert_note(
    #     #     project_id,
    #     #     f"Installment #{installment_number} status updated: {installment_status}",
    #     #     user_id,
    #     # )

    # except MySQLdb.Error as e:
    #     print("MySQL Error:", e)


############## Document Queries ##############
def get_project_docs(project_id):
    try:
        sqlQuery = (
            "SELECT project_documents.*, users.first_name, users.last_name"
            + " FROM project_documents"
            + " INNER JOIN users"
            + " ON project_documents.user_id = users.user_id"
            + " WHERE project_documents.project_id = :project_id"
            + " ORDER BY project_documents.upload_date DESC;"
        )

        query_params = {
            "project_id": project_id,
        }

        with engine.connect() as connection:
            documents = connection.execute(text(f"{sqlQuery}"), query_params)
            documents_dict = documents.mappings().all()

        return documents_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def upload_document(project_id, document_type, comment, user_id, filename):
    try:
        sqlQuery = (
            "INSERT INTO project_documents (project_id, type, comment, user_id, filename)"
            + " VALUES (:project_id, :type, :comment, :user_id, :filename)"
        )

        query_params = {
            "project_id": project_id,
            "type": document_type,
            "comment": comment,
            "user_id": user_id,
            "filename": secure_filename(filename),
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Document uploaded")

    except Exception as e:
        print("Database Error:", e)
        return ""

    #     # insert_note(
    #     #     project_id, f"{document_type} has been uploaded (Auto Note)", user_id
    #     # )


def get_document_types():
    try:
        sqlQuery = (
            "SELECT document_type"
            + " FROM matrix_document_types"
            + " ORDER BY document_type;"
        )

        with engine.connect() as connection:
            doc_types = connection.execute(text(f"{sqlQuery}"))
            # doc_types_dict = doc_types.mappings().all()
            doc_types_list = [doc_type.document_type for doc_type in doc_types]

        return doc_types_list

    except Exception as e:
        print("Database Error:", e)
        return ""


############## Search Queries ##############
def search(search_by, search_criteria):
    try:
        # Default search is project number
        sqlQuery = (
            "SELECT projects.*, clients.name"
            + " FROM projects"
            + " INNER JOIN clients"
            + " ON projects.client_id = clients.client_id"
            + " WHERE project_id = :search_criteria;"
        )

        if search_by == "client name":
            sqlQuery = (
                "SELECT projects.*, clients.name"
                + " FROM projects"
                + " INNER JOIN clients"
                + " ON projects.client_id = clients.client_id"
                + " WHERE clients.name LIKE '%'||:search_criteria||'%';"
            )

        query_params = {
            "search_criteria": search_criteria,
        }

        with engine.connect() as connection:
            searh_results = connection.execute(text(f"{sqlQuery}"), query_params)
            searh_results_dict = searh_results.mappings().all()

        return searh_results_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


############## Proposal Queries ##############
def get_fixtures():
    try:
        sqlQuery = (
            "SELECT fixture_abbreviation, fixture_name"
            + " FROM matrix_fixtures"
            + " ORDER BY fixture_abbreviation;"
        )

        with engine.connect() as connection:
            fixtures = connection.execute(text(f"{sqlQuery}"))
            # fixtures_list = fixtures.mappings().all()
            fixtures_list = [
                f"{fixture.fixture_abbreviation} - {fixture.fixture_name}"
                for fixture in fixtures
            ]

        return fixtures_list

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_project_fixtures(project_id):
    try:
        query_params = {
            "project_id": project_id,
        }

        sqlQuery = (
            "SELECT project_proposal_fixtures.*, matrix_fixtures.fixture_name AS fixture_name"
            + " FROM project_proposal_fixtures"
            + " INNER JOIN matrix_fixtures ON project_proposal_fixtures.fixture_abbreviation = matrix_fixtures.fixture_abbreviation"
            + " WHERE project_id = :project_id"
            + " ORDER BY fixture_id;"
        )

        with engine.connect() as connection:
            fixtures = connection.execute(text(f"{sqlQuery}"), query_params)
            try:
                fixtures_dict = fixtures.mappings().all()
            except:
                fixtures_dict = ""

        return fixtures_dict

    except Exception as e:
        print("Database Error:", e)
        return None


def get_proposal_fixtures(project_id):
    try:
        sqlQuery = (
            "SELECT project_proposal_fixtures.*, matrix_fixtures.fixture_name AS fixture_name"
            + " FROM project_proposal_fixtures"
            + " INNER JOIN matrix_fixtures ON project_proposal_fixtures.fixture_abbreviation = matrix_fixtures.fixture_abbreviation"
            + " WHERE project_id = :project_id"
            + " AND proposal_id = 0 ORDER BY fixture_id;"
        )

        query_params = {
            "project_id": project_id,
        }

        with engine.connect() as connection:
            fixtures = connection.execute(text(f"{sqlQuery}"), query_params)
            try:
                fixtures_dict = fixtures.mappings().all()
            except:
                fixtures_dict = ""

        return fixtures_dict

    except Exception as e:
        print("Database Error:", e)
        return None


def add_proposal_fixture(fixture_data):
    total_per_fixture = fixture_data["fixture_quantity"] * fixture_data["fixture_cost"]
    try:
        sqlQuery = (
            "INSERT INTO project_proposal_fixtures (project_id, fixture_abbreviation, quantity, cost_per_fixture, total_per_fixture)"
            + " VALUES (:project_id, :fixture_abbreviation, :quantity, :cost_per_fixture, :total_per_fixture)"
        )

        query_params = {
            "project_id": fixture_data["project_id"],
            "fixture_abbreviation": fixture_data["fixture_select"],
            "quantity": fixture_data["fixture_quantity"],
            "cost_per_fixture": fixture_data["fixture_cost"],
            "total_per_fixture": total_per_fixture,
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Fixture added")

    except Exception as e:
        print("Database Error:", e)
        return ""


def delete_proposal_fixture(fixture_id):
    try:
        sqlQuery = (
            "DELETE FROM project_proposal_fixtures WHERE fixture_id = :fixture_id;"
        )

        query_params = {
            "fixture_id": int(fixture_id),
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Fixture deleted")

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_installment_categories():
    try:
        sqlQuery = (
            "SELECT installment_category"
            + " FROM matrix_installments"
            + " ORDER BY installment_category;"
        )

        with engine.connect() as connection:
            installments = connection.execute(text(f"{sqlQuery}"))
            # installments_list = installments.mappings().all()
            installments_list = [
                installment.installment_category for installment in installments
            ]

        return installments_list

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_proposal_installments(project_id):
    try:
        sqlQuery = (
            "SELECT *"
            + " FROM project_proposal_installments"
            + " WHERE project_id = :project_id AND proposal_id = 0 ORDER BY installment_id;"
        )

        query_params = {
            "project_id": project_id,
        }

        with engine.connect() as connection:
            installments = connection.execute(text(f"{sqlQuery}"), query_params)
            try:
                installments_dict = installments.mappings().all()
            except:
                installments_dict = ""

        return installments_dict

    except Exception as e:
        print("Database Error:", e)
        return None


def add_proposal_installment(installment_data):
    try:
        sqlQuery = (
            "INSERT INTO project_proposal_installments (project_id, installment_number, installment_category, installment_amount)"
            + " VALUES (:project_id, :installment_number, :installment_category, :installment_amount)"
        )

        query_params = {
            "project_id": installment_data["project_id"],
            "installment_number": int(installment_data["installment_number"]),
            "installment_category": installment_data["installment_select"],
            "installment_amount": installment_data["installment_amount"],
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Installment added")

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_proposal_notes(project_id):
    try:
        sqlQuery = (
            "SELECT *"
            + " FROM project_proposal_notes"
            + " WHERE project_id = :project_id"
            + " AND proposal_id = 0 ORDER BY note_id;"
        )

        query_params = {
            "project_id": project_id,
        }

        with engine.connect() as connection:
            notes = connection.execute(text(f"{sqlQuery}"), query_params)
            try:
                notes_dict = notes.mappings().all()
            except:
                notes_dict = ""

        return notes_dict

    except Exception as e:
        print("Database Error:", e)
        return None


def add_proposal_note(note_data):
    try:
        sqlQuery = (
            "INSERT INTO project_proposal_notes (project_id, note)"
            + " VALUES (:project_id, :note)"
        )

        query_params = {
            "project_id": note_data["project_id"],
            "note": note_data["note"],
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Note added")

    except Exception as e:
        print("Database Error:", e)
        return ""


def delete_proposal_note(note_id):
    try:
        sqlQuery = "DELETE FROM project_proposal_notes WHERE note_id = :note_id;"

        query_params = {
            "note_id": int(note_id),
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Note deleted")

    except Exception as e:
        print("Database Error:", e)
        return ""


def create_proposal(project_id):
    try:
        sqlQuery = "INSERT INTO project_proposal (project_id)" + " VALUES (:project_id)"

        query_params = {
            "project_id": project_id,
        }

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Proposal created")

        sqlQuery = (
            "SELECT MAX(proposal_id)"
            + " FROM project_proposal"
            + " WHERE project_id = :project_id;"
        )

        query_params = {
            "project_id": project_id,
        }

        with engine.connect() as connection:
            proposal_id = connection.execute(text(f"{sqlQuery}"), query_params)
            proposal_id = proposal_id.first()[0]

        return proposal_id

    except Exception as e:
        print("Database Error:", e)
        return ""


def update_proposal_items_id(project_id, proposal_id):
    try:
        query_params = {
            "project_id": project_id,
            "proposal_id": proposal_id,
        }

        # Update fixture table
        sqlQuery = (
            "UPDATE project_proposal_fixtures"
            + " SET proposal_id = :proposal_id"
            + " WHERE project_id = :project_id AND proposal_id = 0;"
        )

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        # Update installments table
        sqlQuery = (
            "UPDATE project_proposal_installments"
            + " SET proposal_id = :proposal_id"
            + " WHERE project_id = :project_id AND proposal_id = 0;"
        )

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        # Update notes table
        sqlQuery = (
            "UPDATE project_proposal_notes"
            + " SET proposal_id = :proposal_id"
            + " WHERE project_id = :project_id AND proposal_id = 0;"
        )

        with engine.connect() as connection:
            result = connection.execute(text(f"{sqlQuery}"), query_params)
            connection.commit()

        print("Proposal items updated")

    except Exception as e:
        print("Database Error:", e)
        return ""


############## Misc. Queries ##############
def get_city_state_county(zip_code):
    try:
        sqlQuery = (
            "SELECT primary_city, state, county"
            + " FROM zip_code_county"
            + " WHERE zip = :zip_code;"
        )

        query_params = {
            "zip_code": zip_code,
        }

        with engine.connect() as connection:
            city_state_zip = connection.execute(text(f"{sqlQuery}"), query_params)
            city_state_zip_dict = city_state_zip.mappings().all()[0]

        return city_state_zip_dict

    except Exception as e:
        print("Database Error:", e)
        return ""


def get_project_statuses():
    try:
        sqlQuery = (
            "SELECT project_status, order_number"
            + " FROM matrix_project_statuses"
            + " WHERE project_status != 'Project Created'"
            + " ORDER BY order_number;"
        )

        with engine.connect() as connection:
            project_statuses = connection.execute(text(f"{sqlQuery}"))
            statuses = [status.project_status for status in project_statuses]

        return statuses

    except Exception as e:
        print("Database Error:", e)
        return ""
