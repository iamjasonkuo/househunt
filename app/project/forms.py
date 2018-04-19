from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, SelectField, SelectMultipleField, DateField, IntegerField, HiddenField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length, Optional
from flask_uploads import UploadSet, IMAGES
from app.helper import clean_list, normalize, Select2MultipleField
from app.models import User, Project, Address
from app.selections import countries, states, tags, tags

images = UploadSet('images', IMAGES)

class ProjectCreateInitialForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    tags = Select2MultipleField('Tags', choices=tags, description=u"tags description goes here", render_kw={"multiple": "multiple", "data-tags": "1"})
    address1 = StringField('Address 1', validators=[DataRequired()])
    address2 = StringField('Address 2', validators=[Optional()])
    city = StringField('City', validators=[DataRequired()])
    state = SelectField('State', choices=states)
    zipcode = StringField('Zip/Postal Code', validators=[DataRequired(), Length(min=5)])
    country = SelectField('Country', choices=countries)
    submit = SubmitField('Create')

class EditProjectForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    headline = StringField('Headline', validators=[Optional()])
    description = TextAreaField('Project Description', validators=[Length(min=0, max=140)])
    completion_date = DateField('Completion Date', validators=[Optional()])
    tags = Select2MultipleField('Tags', choices=tags, description=u"tags description goes here", render_kw={"multiple": "multiple", "data-tags": "1"})
    address1 = StringField('Address 1', validators=[DataRequired()])
    address2 = StringField('Address 2', validators=[Optional()])
    city = StringField('City', validators=[DataRequired()])
    state = SelectField('State', choices=states)
    zipcode = StringField('Zip/Postal Code', validators=[DataRequired(), Length(min=5)])
    country = SelectField('Country', choices=countries)
    submit = SubmitField('Submit')

    # def __init__(self, original_name, *args, **kwargs):
    #     super(EditProjectForm, self).__init__(*args, **kwargs)
    #     self.original_name = original_name
    #
    # def validate_projectname(self, name):
    #     if name.data != self.original_name:
    #         project = Project.query.filter_by(name=self.name.data).first()
    #         if project is not None:
    #             raise ValidationError('Please use a different project name.')

class PhotoForm(FlaskForm):
    project_id = HiddenField('project_id')
    photo = FileField('Photo', validators=[FileRequired(),FileAllowed(images, 'Images only!')])
    description = StringField('Photo Description', validators=[Optional()])
    tags = Select2MultipleField('Tags', choices=tags, description=u"tags description goes here", render_kw={"multiple": "multiple", "data-tags": "1"})
    submit = SubmitField('Submit')

class ProjectFilterForm(FlaskForm):
    beds = IntegerField('Beds', validators=[DataRequired()])
    baths = IntegerField('Baths', validators=[DataRequired()])
    sqft_min = IntegerField('Sqft Min', validators=[DataRequired()])
    sqft_max = IntegerField('Sqft Max', validators=[DataRequired()])
    lotsqft_min = IntegerField('Lot Sqft Min', validators=[DataRequired()])
    lotsqft_max = IntegerField('Lot Sqft Max', validators=[DataRequired()])
    build_type = SelectField('Build Type', choices=tags)
    property_type = SelectField('Property Type', choices=tags)
    num_units = IntegerField('Lot Sqft Max', validators=[DataRequired()])
    year_built_min = IntegerField('Lot Sqft Max', validators=[DataRequired()])
    year_built_max = IntegerField('Lot Sqft Max', validators=[DataRequired()])
    year_renovated_min = IntegerField('Lot Sqft Max', validators=[DataRequired()])
    year_renovated_max = IntegerField('Lot Sqft Max', validators=[DataRequired()])
    tags = SelectMultipleField('Tags', choices=tags, validators=[DataRequired()])
