import re
from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    DecimalField,
    EmailField,
    HiddenField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    validators,
)
from flask_wtf.file import FileField, FileRequired
from wtforms.validators import DataRequired, InputRequired, ValidationError, EqualTo

from database import get_all_clients, get_document_types, get_project_statuses

STATE_OPTIONS = [
    ("AL", "Alabama"),
    ("AK", "Alaska"),
    ("AZ", "Arizona"),
    ("AR", "Arkansas"),
    ("CA", "California"),
    ("CO", "Colorado"),
    ("CT", "Connecticut"),
    ("DE", "Delaware"),
    ("DC", "District Of Columbia"),
    ("FL", "Florida"),
    ("GA", "Georgia"),
    ("HI", "Hawaii"),
    ("ID", "Idaho"),
    ("IL", "Illinois"),
    ("IN", "Indiana"),
    ("IA", "Iowa"),
    ("KS", "Kansas"),
    ("KY", "Kentucky"),
    ("LA", "Louisiana"),
    ("ME", "Maine"),
    ("MD", "Maryland"),
    ("MA", "Massachusetts"),
    ("MI", "Michigan"),
    ("MN", "Minnesota"),
    ("MS", "Mississippi"),
    ("MO", "Missouri"),
    ("MT", "Montana"),
    ("NE", "Nebraska"),
    ("NV", "Nevada"),
    ("NH", "New Hampshire"),
    ("NJ", "New Jersey"),
    ("NM", "New Mexico"),
    ("NY", "New York"),
    ("NC", "North Carolina"),
    ("ND", "North Dakota"),
    ("OH", "Ohio"),
    ("OK", "Oklahoma"),
    ("OR", "Oregon"),
    ("PA", "Pennsylvania"),
    ("RI", "Rhode Island"),
    ("SC", "South Carolina"),
    ("SD", "South Dakota"),
    ("TN", "Tennessee"),
    ("TX", "Texas"),
    ("UT", "Utah"),
    ("VT", "Vermont"),
    ("VA", "Virginia"),
    ("WA", "Washington"),
    ("WV", "West Virginia"),
    ("WI", "Wisconsin"),
    ("WY", "Wyoming"),
]


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField("Login")


class SignUpForm(FlaskForm):
    def password_check(form, field):
        password = form.password.data
        if len(password) < 4:
            raise ValidationError("Password must be at lest 8 letters long")
        elif re.search("[0-9]", password) is None:
            raise ValidationError("Password must contain a number")
        elif re.search("[A-Z]", password) is None:
            raise ValidationError("Password must have one uppercase letter")
        elif re.search("[-\#\$\.\%\&\*\!]", password) is None:
            raise ValidationError(
                "Password must have at least one special character '- # $ . % & * !' "
            )

    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField(
        "Password",
        validators=[
            InputRequired(),
            password_check,
        ],
    )
    confirm = PasswordField(
        "Confirm Password",
        validators=[
            InputRequired(),
            EqualTo("password", message="Passwords must match"),
        ],
    )
    sign_up = SubmitField("Sign Up")


class ClientForm(FlaskForm):
    name = StringField("Client Name", validators=[DataRequired()])
    address = StringField("Address", validators=[DataRequired()])
    city = StringField("City", validators=[DataRequired()])
    state = SelectField(
        "State",
        validators=[DataRequired()],
        choices=STATE_OPTIONS,
    )
    # state = StringField("State", validators=[DataRequired()])
    zip_code = StringField("Zip Code", validators=[DataRequired()])
    website = StringField("Website")
    phone_number = StringField("Phone Number")
    poc_name = StringField("Name")
    poc_phone_number = StringField("Phone Number")
    poc_email = EmailField("Email")
    submit = SubmitField("Create Client")
    edit = SubmitField("Update Client")


class ProjectForm(FlaskForm):
    client_options = []
    for clients in get_all_clients():
        client_info = (clients["client_id"], clients["name"])
        client_options.append(client_info)

    project_id = StringField("Project ID", validators=[DataRequired()])
    name = StringField("Project Name", validators=[DataRequired()])
    client = SelectField(
        "Client",
        validators=[DataRequired()],
        choices=client_options,
    )
    address = StringField("Address", validators=[DataRequired()])
    city = StringField("City", validators=[DataRequired()])
    state = SelectField(
        "State",
        validators=[DataRequired()],
        choices=STATE_OPTIONS,
    )
    zip_code = StringField("Zip Code", validators=[DataRequired()])
    county = StringField("County", validators=[DataRequired()])
    submit = SubmitField("Add Project")


class MasterPermitForm(FlaskForm):
    master_permit = StringField("Master Permit", validators=[DataRequired()])
    add = SubmitField("Add")


class PlumbingPermitForm(FlaskForm):
    plumbing_permit = StringField("Plumbing Permit")
    add = SubmitField("Add")


class DocumentUploadForm(FlaskForm):
    document_type = SelectField(
        "Type",
        validators=[DataRequired()],
        choices=get_document_types(),
    )
    upload_file = FileField(validators=[FileRequired()])
    comment = StringField("Comment")
    upload = SubmitField("Upload")


class ProjectStatusForm(FlaskForm):
    project_status = SelectField(
        "Project Status",
        validators=[DataRequired()],
        choices=get_project_statuses(),
    )
    update = SubmitField("Update")


class InvoiceStatusUpdateForm(FlaskForm):
    # Payment Information
    invoice_status = SelectField(
        "Invoice Status",
        validators=[DataRequired()],
        choices=["Billed", "Paid"],
    )
    installment_number = HiddenField()
    installment_amount = HiddenField()
    invoice_id = HiddenField()

    # Payment Information
    payment_method = SelectField(
        "Payment Method",
        validators=[DataRequired()],
        choices=["Check", "Direct Deposit"],
    )
    check_number = StringField("Check #")
    payment_amount = DecimalField(
        "Amount",
        validators=[DataRequired()],
        places=2,
        rounding=None,
    )
    date_received = DateField("Date Received")
    note = TextAreaField("Note")

    update = SubmitField("Apply")
