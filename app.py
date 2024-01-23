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

import database
from database import create_session, db_connect

# from flask_login import (
#     LoginManager,
#     login_required,
#     current_user,
#     login_user,
#     logout_user,
# )
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, EqualTo, Length


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("APP_KEY")

# engine, connection = db_connect()
# session = create_session(engine)

USER_ID = "525bc4ea-b0f7-482d-a954-db517e6b5b89"

# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = "login"

# class LoginForm(FlaskForm):
#     username = StringField("Username:", validators=[DataRequired()])
#     password = PasswordField("Password:", validators=[DataRequired()])
#     submit = SubmitField("Login")


# @login_manager.user_loader
# def load_user(user_id):
#     user_id_query = (
#         select(users.Users).select_from(users.Users).filter(users.Users.id == user_id)
#     )
#     return session.execute(user_id_query).first()[0]

# @app.route("/login", methods=["GET", "POST"])
# def login():
#     form = LoginForm()

#     if form.validate_on_submit():
#         username = form.username.data
#         password = form.password.data

#         form.username.data = ""
#         form.password.data = ""

#         password_query = (
#             select(users.Users.userPassword)
#             .select_from(users.Users)
#             .filter(users.Users.username == username)
#         )
#         user_db_password = session.execute(password_query).first()
#         if user_db_password:
#             if check_password_hash(user_db_password[0], password):
#                 user_id_query = (
#                     select(users.Users)
#                     .select_from(users.Users)
#                     .filter(users.Users.username == username)
#                 )
#                 user = session.execute(user_id_query).first()[0]

#                 login_user(user)

#                 global USER_ID
#                 USER_ID = session.execute(user_id_query).first()[0].id

#                 # flash("Login successful")
#                 return redirect(url_for("home"))
#             else:
#                 flash("Incorrect username or password!")
#         else:
#             flash("User does not exist!")
#     return render_template("login.html", form=form)


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
