import os

from flask import (
    Flask,
    flash,
    get_flashed_messages,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from sqlalchemy import null, select
from werkzeug.security import check_password_hash, generate_password_hash

import database
from database import create_session, db_connect
from forms import ClientForm, LoginForm
from models import users

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("APP_KEY")

# engine, connection = db_connect()
# session = create_session(engine)

# USER_ID = "525bc4ea-b0f7-482d-a954-db517e6b5b89"
USER_ID = ""

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    # user_id_query = (
    #     select(users.Users).select_from(users.Users).filter(users.Users.id == user_id)
    # )
    # return session.execute(user_id_query).first()[0]
    return database.get_user(user_id)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        form.email.data = ""
        form.password.data = ""

        # password_query = (
        #     select(users.Users.password)
        #     .select_from(users.Users)
        #     .filter(users.Users.email == email)
        # )
        # print(f"{password_query=}")
        # user_db_password = session.execute(password_query).first()
        user_db_password = database.get_user_password(email)
        if user_db_password:
            if check_password_hash(user_db_password["password"], password):
                # user_id_query = (
                #     select(users.Users)
                #     .select_from(users.Users)
                #     .filter(users.Users.username == username)
                # )
                # user = session.execute(user_id_query).first()[0]
                user_dict = database.get_user_from_email(email)
                print(f"{user_dict=}")
                user = users.Users(user_dict)
                print(f"{user=}")
                login_user(user, remember=form.data.remember)

                global USER_ID
                # USER_ID = session.execute(user_id_query).first()[0].id
                USER_ID = user.user_id
                print(f"{USER_ID=}")

                # flash("Login successful")
                return redirect(url_for("main"))
            else:
                flash("Incorrect username or password!")
        else:
            flash("User does not exist!")
    return render_template("login.html", form=form)


# @app.route("/logout", methods=["GET", "POST"])
# @login_required
# def logout():
#     logout_user()
#     flash("You have been logged out.")
#     return redirect(url_for("login"))


@app.route("/")
def main():
    user = database.get_user(USER_ID)
    clients = database.get_all_clients()
    projects = database.get_all_projects()

    return render_template(
        "home.html",
        user=user,
        clients=clients,
        projects=projects,
    )


@app.route("/client_list")
def client_list():
    user = database.get_user(USER_ID)
    clients = database.get_all_clients()

    return render_template(
        "client_list.html",
        user=user,
        clients=clients,
    )


@app.route("/search")
def search():
    user = database.get_user(USER_ID)

    search_criteria = request.args["search_criteria"]
    search_by = request.args["search_by"].lower()

    if not search_by:
        search_by = "project number"

    results = database.search(search_by, search_criteria)
    print(results)

    return render_template(
        "search_results.html",
        user=user,
        results=results,
    )


@app.route("/project/<project_id>")
def project_view(project_id):
    user = database.get_user(USER_ID)
    project = database.get_project(project_id)
    notes = database.get_notes(project_id)
    invoices = database.get_invoices(project_id)

    return render_template(
        "project.html",
        user=user,
        project=project,
        notes=notes,
        invoices=invoices,
    )


@app.route("/client-add", methods=["GET", "POST"])
def create_client():
    user = database.get_user(USER_ID)

    name = None
    address = None
    city = None
    state = None
    zip_code = None
    website = None
    phone_number = None
    poc_name = None
    poc_phone_number = None
    poc_email = None

    form = ClientForm()

    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ""
        address = form.address.data
        form.address.data = ""
        city = form.city.data
        form.city.data = ""
        state = form.state.data
        form.state.data = ""
        zip_code = form.zip_code.data
        form.zip_code.data = ""
        website = form.website.data
        form.website.data = ""
        phone_number = form.phone_number.data
        form.phone_number.data = ""
        poc_name = form.poc_name.data
        form.poc_name.data = ""
        poc_phone_number = form.poc_phone_number.data
        form.poc_phone_number.data = ""
        poc_email = form.poc_email.data
        form.poc_email.data = ""

        client_info = {
            "name": name,
            "address": address,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "website": website,
            "phone_number": phone_number,
            "poc_name": poc_name,
            "poc_phone_number": poc_phone_number,
            "poc_email": poc_email,
        }

        database.create_client(client_info)

    return render_template(
        "client_add.html",
        user=user,
        form=form,
        name=name,
        address=address,
        city=city,
        state=state,
        zip_code=zip_code,
        website=website,
        phone_number=phone_number,
        poc_name=poc_name,
        poc_phone_number=poc_phone_number,
        poc_email=poc_email,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
