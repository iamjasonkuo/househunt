from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, SelectField, SelectMultipleField, FloatField, HiddenField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length, Optional
from app.helper import clean_list, normalize, Select2MultipleField
from app.models import User, Project, Address
from app.selections import countries, states, tags


class PostForm(FlaskForm):
    body = TextAreaField('Say something', validators=[
        DataRequired(), Length(min=1, max=140)])
    parent_id = HiddenField('parent_id')
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
    property_type = SelectMultipleField('Property Type', choices=tags)

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

class TaggingForm(FlaskForm):
    tags = Select2MultipleField(u'Tags', [],
            choices=tags,
            description=u"tags description goes here",
            render_kw={"multiple": "multiple", "data-tags": "1"})
    submit = SubmitField()

class DemoForm(FlaskForm):
    single_select = SelectField(u"单选", [DataRequired()],
            choices=[("py", "python"), ("rb", "ruby"), ("js", "javascript")],
            description=u"有限选项。无效化。",
            render_kw={"disabled": "true"})
    single_dynamic_select = SelectField(u"单选", [DataRequired()],
            choices=[("0", "")],
            description=u"动态加载选项。",
            render_kw={})
    multi_select = Select2MultipleField(u"选择框", [],
            choices=[("py", "python"), ("rb", "ruby"), ("js", "javascript")],
            description=u"多选。有限选项。",
            render_kw={"multiple": "multiple"})
    tags = Select2MultipleField(u'标签', [],
            choices=[("py", "python"), ("rb", "ruby"), ("js", "javascript")],
            description=u"多选。无限选项。",
            render_kw={"multiple": "multiple", "data-tags": "1"})
    submit = SubmitField()
