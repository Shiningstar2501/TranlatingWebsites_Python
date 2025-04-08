from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField
from wtforms.validators import DataRequired

class TranslationForm(FlaskForm):
    url = StringField('Enter Website URLs (comma-separated)', validators=[DataRequired()])
    language = SelectField('Select Language Code', choices=[], validators=[DataRequired()])
    php_template = TextAreaField('Enter PHP Template', validators=[DataRequired()])
    css_class = StringField('Enter the CSS Class (e.g., "container")', validators=[DataRequired()])
    domain = StringField("Enter the Domain URL", validators=[DataRequired()])
