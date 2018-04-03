from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, SelectField, SelectMultipleField, FloatField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length, Optional
from app.helper import clean_list, normalize
from app.models import User, Project, Address
from app.selections import countries, states, tags, statuses, build_types, property_types


class PostForm(FlaskForm):
    body = TextAreaField('Say something', validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Submit')

class SearchForm(FlaskForm):
    q = StringField('Search', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
            super(SearchForm, self).__init__(*args, **kwargs)

class FeedFilterForm(FlaskForm):
    city = StringField('City', validators=[DataRequired()])
    property_type = SelectMultipleField('Property Type', choices=property_types)

class EditAddressForm(FlaskForm):
    address1 = StringField('Address 1', validators=[DataRequired()])
    address2 = StringField('Address 2', validators=[Optional()])
    city = StringField('City', validators=[DataRequired()])
    state = SelectField('State', choices=states)
    zipcode = StringField('Zip/Postal Code', validators=[DataRequired(), Length(min=5)])
    country = SelectField('Country', choices=countries)
    submit = SubmitField('Submit')
    full_address = address2 = StringField('Full Address', validators=[Optional()])
    lat = FloatField('Latitude', validators=[Optional()])
    lng = FloatField('Longitude', validators=[Optional()])
