from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
)
from wtforms.validators import DataRequired, Email, Length, EqualTo


class UserForm(FlaskForm):
    next_url = StringField("next_url")
    user_id = StringField("user_id", [DataRequired()])
    email = StringField("email", [DataRequired(), Email()])
    fullname = StringField("fullname", [DataRequired()])
    first_name = StringField("first_name", [DataRequired()])
    last_name = StringField("last_name", [DataRequired()])
    phone = StringField("phone", [DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(6, 30)])
    password_confirmation = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Password do not match."),
        ],
    )
    submit = SubmitField("Save")


class CreateUserForm(FlaskForm):
    fullname = StringField("fullname", [DataRequired()])
    first_name = StringField("first_name", [DataRequired()])
    last_name = StringField("last_name", [DataRequired()])
    phone = StringField("phone", [DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(6, 30)])
    password_confirmation = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Password do not match."),
        ],
    )
    submit = SubmitField("Save")
