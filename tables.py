# what the form helps us write forms in python code
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, DateTimeField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length
from datetime import datetime

class Call_log(FlaskForm):
    operator = StringField('Operator Name', validators=[DataRequired(), Length(min=2,max=20)])
    caller = StringField('Caller Name', validators=[DataRequired(), Length(min=2,max=20)])
    call_time = DateTimeField('Current Date', default = datetime.now)
    serial_number = StringField('Equipment Number', validators=[DataRequired()])
    call_note = TextAreaField('Note')
    problem_id = IntegerField('Problem ID')
    submit = SubmitField("Save call log")
    
class Create_Problem_Form(FlaskForm):
    problem_title = StringField('Problem Title', validators=[DataRequired(), Length(min=2,max=20)])
    description = TextAreaField('Description', validators=[DataRequired()])
    problem_type = SelectField('Problem Type:', choices=[])
    caller = StringField('Caller Name')
    submit = SubmitField("Save problem")

class Specialist_Assigned(FlaskForm):
    specialist = SelectField('Assigned to: ',validators=[DataRequired()])
    assigned_time = DateTimeField('assigned Date', default = datetime.now)
    submit = SubmitField("Assign Specialist")

class Solution(FlaskForm):
    is_solved = BooleanField('Is solved?')
    solution = TextAreaField('solution')
    finished_time = DateTimeField('assigned Date', default = datetime.now)
    submit = SubmitField("Save solution")