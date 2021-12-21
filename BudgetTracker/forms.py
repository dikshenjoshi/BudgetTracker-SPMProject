from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms.fields.html5 import DateField
from BudgetTracker.models import User

class SignUpForm(FlaskForm):
	first_name=StringField('First Name', validators=[DataRequired(), Length(min=3,max=20)])
	last_name=StringField('Last Name', validators=[DataRequired(), Length(min=3,max=20)])
	email=StringField('Email-ID', validators=[DataRequired(),Email()])
	password=PasswordField('Password', validators=[DataRequired()])
	re_enter_password=PasswordField('Re-enter Password', validators=[DataRequired(), EqualTo('password')])
	submit=SubmitField('Sign Up')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user:
			raise ValidationError('Email-ID already taken. Please choose another.')

class LoginForm(FlaskForm):
	email=StringField('Email-ID', validators=[DataRequired(),Email()])
	password=PasswordField('Password', validators=[DataRequired()])
	remember_me=BooleanField('Remember Me')
	submit=SubmitField('Login')

class TransactionForm(FlaskForm):
	title=StringField('Title', validators=[DataRequired()])
	amount=IntegerField('Amount', validators=[DataRequired()])
	incomeAdd=SubmitField('Add Income')
	expenseAdd=SubmitField('Add Expense')
	incomeUpdate=SubmitField('Update Income')
	expenseUpdate=SubmitField('Update Expense')

class SearchForm(FlaskForm):
	date=DateField('Date',format='%Y-%m-%d')
	submit=SubmitField('Search')

class RequestResetForm(FlaskForm):
	email = StringField('Email',validators=[DataRequired(), Email()])
	submit = SubmitField('Request Password Reset')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user is None:
			raise ValidationError('There is no account with that email. You must sign up first.')


class ResetPasswordForm(FlaskForm):
	password = PasswordField('Password', validators=[DataRequired()])
	re_enter_password = PasswordField('Re-enter Password', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Reset Password')

class SetBudgetForm(FlaskForm):
	budget=IntegerField('Budget', validators=[DataRequired()])
	submit=SubmitField('Set Budget')