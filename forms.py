import datetime
import re
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    EmailField,
    FormField,
    HiddenField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    validators,
    IntegerField,
)
from flask_wtf.file import FileField, FileRequired
from wtforms.validators import (
    DataRequired,
    InputRequired,
    ValidationError,
    EqualTo,
    NumberRange,
)
from wtforms_sqlalchemy.fields import QuerySelectField

from database import (
    get_all_clients,
    get_document_types,
    get_project_statuses,
    get_fixtures,
    get_installment_categories,
    get_permit_add_information,
)

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
    login_submit = SubmitField("Login")


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
    sign_up_submit = SubmitField("Sign Up")


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
    client_submit = SubmitField("Create Client")
    client_edit_submit = SubmitField("Update Client")


# Create new project
class ProjectForm(FlaskForm):
    # client_options = []
    # for clients in get_all_clients():
    #     client_info = (clients["client_id"], clients["name"])
    #     client_options.append(client_info)

    project_id = StringField(
        "Project ID",
        validators=[DataRequired()],
        render_kw={"readonly": ""},
    )
    name = StringField(
        "Project Name",
        validators=[DataRequired()],
    )
    client = SelectField(
        "Client",
        validators=[DataRequired()],
        # choices=client_options,
    )
    address = StringField(
        "Address",
        validators=[DataRequired()],
    )
    city = StringField(
        "City",
        validators=[DataRequired()],
    )
    state = SelectField(
        "State",
        validators=[DataRequired()],
        choices=STATE_OPTIONS,
    )
    zip_code = StringField(
        "Zip Code",
        validators=[DataRequired()],
    )
    county = StringField(
        "County",
        validators=[DataRequired()],
    )
    project_add_submit = SubmitField("Add Project")

    @classmethod
    def new(cls):
        # Instantiate the form
        form = cls()

        # Update the choices for the agency field
        form.agency.choices = get_all_clients()
        return form


class ProjectNotesForm(FlaskForm):
    project_note = TextAreaField(
        "Note",
        render_kw={"style": "resize:none"},
    )
    project_note_submit = SubmitField("Submit")


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
    upload_document_submit = SubmitField("Upload")


class ProjectStatusForm(FlaskForm):
    project_status = SelectField(
        "Project Status",
        validators=[DataRequired()],
        choices=get_project_statuses(),
    )
    project_status_update_submit = SubmitField("Update")


class InvoicePaymentForm(FlaskForm):
    payment_method = SelectField(
        "Payment Method",
        choices=["Check", "Direct Deposit"],
        default="Check",
    )
    check_number = StringField("Check #")
    payment_amount = DecimalField(
        "Amount",
        places=2,
        rounding=None,
        default=0.0,
    )
    date_received = DateField(
        "Date Received",
        default=datetime.date.today(),
    )
    note = TextAreaField("Note")


class InvoiceStatusUpdateForm(FlaskForm):
    invoice_status = SelectField(
        "Invoice Status",
        validators=[DataRequired()],
        choices=["Billed", "Paid"],
    )
    installment_number = HiddenField()
    installment_amount = HiddenField()
    invoice_id = HiddenField()
    payment_details = FormField(InvoicePaymentForm)
    invoice_status_update = SubmitField("Apply")


class InvoiceCreateForm(FlaskForm):
    installment_select = BooleanField()
    installment_number = HiddenField()
    billed_percentage = DecimalField()
    billed_amount = DecimalField("$", render_kw={"readonly": True})
    invoice_create_submit = SubmitField("Create")


class ApplyPaymentForm(FlaskForm):
    invoice_id = HiddenField(
        "Invoice ID",
    )
    payment_method = SelectField(
        "Payment Method",
        validators=[DataRequired()],
        choices=["Check", "Direct Deposit"],
    )
    check_number = StringField(
        "Check Number",
        validators=[DataRequired()],
    )
    payment_amount = DecimalField(
        "Payment Amount",
        validators=[DataRequired()],
    )
    date_received = DateField(
        "Date Received",
        validators=[DataRequired()],
        default=datetime.date.today(),
    )
    amount_applied = HiddenField(
        "Amount Applied",
        default=0.00,
    )
    amount_remaining = HiddenField(
        "Amount Remaining",
        default=0.00,
    )
    invoice_status = HiddenField(
        "Invoice Status",
    )

    payment_applied = HiddenField(
        "Payment Applied",
        default=False,
    )

    payment_note = TextAreaField("Note")
    # invoice_select = BooleanField()
    apply_payment = SubmitField("Submit")


class ProposalFixturesForm(FlaskForm):
    project_id = HiddenField(
        "Project ID",
    )
    fixture_id = HiddenField(
        "Fixture ID",
    )
    fixtures = SelectField(
        "Fixtures",
        validators=[DataRequired()],
        choices=get_fixtures(),
    )
    fixture_quantity = IntegerField(
        "Quantity",
        validators=[DataRequired()],
    )
    fixture_cost = DecimalField(
        "Cost (Per Fixture) $",
        validators=[DataRequired()],
    )


class ProposalInstallmentsForm(FlaskForm):
    project_id = HiddenField(
        "Project ID",
    )
    installment_number = IntegerField(
        "#",
        validators=[DataRequired()],
        default=1,
        render_kw={"readonly": ""},
    )
    installments = SelectField(
        "Installment Category",
        validators=[DataRequired()],
        choices=get_installment_categories(),
    )
    installment_amount = DecimalField(
        "Installment Amount $",
        validators=[DataRequired()],
    )
    installment_amount_remaining = DecimalField(
        "Amount Remaining $",
        validators=[DataRequired()],
        render_kw={"readonly": ""},
    )


class ProposalNotesForm(FlaskForm):
    project_id = HiddenField(
        "Project ID",
    )
    note_id = HiddenField(
        "Note ID",
    )
    note = StringField("Note")


class PermitsAddForm(FlaskForm):
    permit_number = StringField(
        "Permit #",
    )
    permit_type = SelectField(
        "Type",
        validators=[DataRequired()],
        choices=["Plumbing", "Master"],
    )
    permit_status = SelectField(
        "Status",
        validators=[DataRequired()],
        choices=["Requested", "Pending", "Approved", "Rejected"],
    )
    permit_status_date = DateField(
        "Status Date",
        validators=[DataRequired()],
        default=datetime.date.today(),
    )
    permit_note = TextAreaField(
        "Note",
        render_kw={"style": "resize:none"},
    )
    city_county = QuerySelectField(
        "City/County",
        query_factory=get_permit_add_information,  # Function to retrieve choices
        get_label="city_county",  # Attribute to use for displaying options
        allow_blank=False,
        blank_text="Select City/County",
        get_pk=lambda x: x.id,
    )
    permit_add_submit = SubmitField("Submit")


class CityCountyAddNewForm(FlaskForm):
    city_county = StringField(
        "City/County Name",
    )
    website = StringField(
        "Website",
    )
    follow_up_days = IntegerField(
        "Follow-Up Days",
        [NumberRange(min=0)],
    )
    city_county_submit = SubmitField("Add New")
