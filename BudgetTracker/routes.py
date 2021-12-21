from flask import render_template, redirect, url_for, flash, request, abort, session
from BudgetTracker import app, db, bcrypt, mail
from BudgetTracker.forms import SignUpForm, LoginForm, TransactionForm, SearchForm, RequestResetForm, ResetPasswordForm, SetBudgetForm
from BudgetTracker.models import User, Income, Expense
from flask_login import login_user, current_user, logout_user, login_required
import datetime
from dateutil.relativedelta import relativedelta
import os
from flask_mail import Message


@app.route("/home", methods=['GET', 'POST'])
@login_required
def home():
	form = TransactionForm()
	form1 = SetBudgetForm()
	if request.method == 'POST':
		if len(request.form) == 3:
			if form1.validate_on_submit():
				current_user.budget=form1.budget.data
				db.session.commit()
				flash('Your budget has been set!', 'success')
				return redirect(url_for('home'))
		else:
			if form.validate_on_submit():
				if form.incomeAdd.data:
					my_income = Income(title=form.title.data, amount=form.amount.data, party=current_user)
					db.session.add(my_income)
					db.session.commit()
					flash('Your income has been added!', 'success')
				if form.expenseAdd.data:
					my_expense = Expense(title=form.title.data, amount=form.amount.data, party=current_user)
					db.session.add(my_expense)
					db.session.commit()
					flash('Your expense has been added!', 'success')
				return redirect(url_for('home'))
	
	offset=current_user.offset

	budget=0
	if current_user.budget:
		budget=current_user.budget

	first=datetime.datetime.today().date()+relativedelta(day=1)
	start=first+datetime.timedelta(milliseconds=offset)
	end=start+relativedelta(months=1)
	data=Expense.query.with_entities(db.func.sum(Expense.amount).label("mySum")).filter_by(user_id=current_user.id).filter(Expense.date_posted.between(start,end)).first()
	expense=0
	if data[0]:
		expense=data[0]

	print(expense)

	budgetLeft=0
	if budget:
		budgetLeft=budget-expense

	start=datetime.datetime.today().date()
	end=start+relativedelta(days=1)
	
	incomes=Income.query.filter_by(user_id=current_user.id).filter(Income.date_posted.between(start,end)).all()
	expenses=Expense.query.filter_by(user_id=current_user.id).filter(Expense.date_posted.between(start,end)).all()

	return render_template('home.html', form=form, form1=form1, incomes=incomes, expenses=expenses, budget=budget, budgetLeft=budgetLeft)

@app.route("/insights", methods=['GET', 'POST'])
@login_required
def insights():

	form = SetBudgetForm()

	if request.method == 'POST':
		if form.validate_on_submit():
			current_user.budget=form.budget.data
			db.session.commit()
			flash('Your budget has been set!', 'success')
			return redirect(url_for('insights'))

	offset=current_user.offset

	#For getting info of whole month and whole year
	today=datetime.datetime.today().date()
	monthlyData=[]
	first=datetime.datetime(today.year,today.month,1,0,0,0,0)
	last=first+relativedelta(months=1)-relativedelta(days=1)
	days=last.day-first.day+1
	start=first+datetime.timedelta(milliseconds=offset)

	for i in range(days):
		end=start+relativedelta(days=1)
		data=Expense.query.with_entities(db.func.sum(Expense.amount).label("mySum")).filter_by(user_id=current_user.id).filter(Expense.date_posted.between(start,end)).first()
		if data[0]:
			monthlyData.append([data[0],start.date()-datetime.timedelta(milliseconds=offset)])
		else:
			monthlyData.append([0,start.date()-datetime.timedelta(milliseconds=offset)])
		start=end

	yearlyData=[]
	start=datetime.datetime(today.year,1,1,0,0,0,0)+datetime.timedelta(milliseconds=offset)
	monthNames=['January','February','March','April','May','June','July','August','September','October','November','December']
	for i in range(12):
		end=start+relativedelta(months=1)
		data=Expense.query.with_entities(db.func.sum(Expense.amount).label("mySum")).filter_by(user_id=current_user.id).filter(Expense.date_posted.between(start,end)).first()
		if data[0]:
			yearlyData.append([data[0],monthNames[i]])
		else:
			yearlyData.append([0,monthNames[i]])
		start=end

	start=datetime.datetime(today.year,today.month,1,0,0,0,0)+datetime.timedelta(milliseconds=offset)
	end=start+relativedelta(months=1)
	print(start)
	print(end)
	data=Expense.query.with_entities(db.func.sum(Expense.amount).label("mySum")).filter_by(user_id=current_user.id).filter(Expense.date_posted.between(start,end)).first()
	totalSpent=0
	if data[0]:
		totalSpent=data[0]
	
	print(totalSpent)

	earned=Income.query.with_entities(db.func.sum(Income.amount).label("mySum")).filter_by(user_id=current_user.id).filter(Income.date_posted.between(start,end)).first()
	totalEarned=0
	if earned[0]:
		totalEarned=earned[0]

	budgetUsedPercentage=0
	if current_user.budget:
		budgetUsedPercentage=int((totalSpent*100)/current_user.budget)

	incomes=Income.query.filter_by(user_id=current_user.id).filter(Income.date_posted.between(start,end)).all()
	expenses=Expense.query.filter_by(user_id=current_user.id).filter(Expense.date_posted.between(start,end)).all()
	
	for income in incomes:
		income.date_posted=income.date_posted-datetime.timedelta(milliseconds=offset)

	for expense in expenses:
		expense.date_posted=expense.date_posted-datetime.timedelta(milliseconds=offset)

	return render_template('insights.html', form=form, monthlyData=monthlyData, yearlyData=yearlyData, incomes=incomes, expenses=expenses, totalSpent=totalSpent, totalEarned=totalEarned, percentage=budgetUsedPercentage)	


@app.route("/search", methods=['GET', 'POST'])
@login_required
def search():
	form = SearchForm()
	form1 = SetBudgetForm()
	listOfExpenses=[]
	offset=current_user.offset

	if request.method == 'POST':
		if 'budget' in request.form:
			if form1.validate_on_submit():
				current_user.budget=form1.budget.data
				db.session.commit()
				flash('Your budget has been set!', 'success')
				return redirect(url_for('search'))
		else:
			if form.validate_on_submit():
				date=form.date.data
				day=date.day
				year=date.year
				month=date.month
				start=datetime.datetime(year,month,day,0,0,0,0)+datetime.timedelta(milliseconds=offset)
				end=start+relativedelta(days=1)
				listOfExpenses = Expense.query.filter_by(user_id=current_user.id).filter(Expense.date_posted.between(start,end)).all()

	for expense in listOfExpenses:
		expense.date_posted=expense.date_posted-datetime.timedelta(milliseconds=offset)

	print(listOfExpenses)

	return render_template('search.html', form=form, form1=form1, listOfExpenses=listOfExpenses, len=len(listOfExpenses))

@app.route("/signup", methods=['GET', 'POST'])
def signup():
	form=SignUpForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user = User(first_name=form.first_name.data, last_name=form.last_name.data, email=form.email.data, password=hashed_password, offset=session['offset'])
		db.session.add(user)
		db.session.commit()
		flash(f'Your account has been created! Welcome {form.first_name.data}', 'success')
		login_user(user, remember=False)
		return redirect(url_for('home'))
	return render_template('signup.html', title='Sign-up Page', form=form)

@app.route("/setOffset", methods=['GET', 'POST'])
def setOffset():
	#Get timezone offset for each user
	if request.method == 'GET':
		return redirect(url_for('home'))
	else:
		if request.json:
			offset=request.json['offset']
			session['offset']=offset
	return ('',200)

@app.route("/", methods=['GET', 'POST'])
@app.route("/login", methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form=LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password, form.password.data):
			setattr(user, 'offset', session['offset'])
			db.session.commit()
			login_user(user, remember=form.remember_me.data)
			flash(f'You are succesfully logged in! Welcome {user.first_name}', 'success')
			next_page = request.args.get('next')
			if next_page:
				return redirect(next_page)
			else:
				return redirect(url_for('home'))
		else:
			flash('Login failed. Please check your email and password', 'danger')
	return render_template('login.html', title='Login Page', form=form)

@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for('login'))

#@app.route("/transaction/add", methods=['GET', 'POST'])
#@login_required
#def add_transaction():
#	form = TransactionForm()
#	if request.method == 'POST':
#		if form.validate_on_submit():
#			if form.incomeAdd.data:
#				my_income = Income(title=form.title.data, amount=form.amount.data, party=current_user)
#				db.session.add(my_income)
#				db.session.commit()
#				flash('Your income has been added!', 'success')
#			if form.expenseAdd.data:
#				my_expense = Expense(title=form.title.data, amount=form.amount.data, party=current_user)
#				db.session.add(my_expense)
#				db.session.commit()
#				flash('Your expense has been added!', 'success')
#			return redirect(url_for('add_transaction'))
#	return render_template('update_transaction.html', title='Add Transaction', form=form, legend='Add Transaction')


@app.route("/transaction/<string:transaction_type>/<int:transaction_id>", methods=['GET', 'POST'])
def transaction(transaction_type, transaction_id):
	form1 = SetBudgetForm()
	if request.method == 'POST':
		if form1.validate_on_submit():
			current_user.budget=form1.budget.data
			db.session.commit()
			flash('Your budget has been set!', 'success')
			return redirect(url_for('transaction'))
	if transaction_type == 'income':
		transaction = Income.query.get_or_404(transaction_id)
		if transaction.party != current_user:
			abort(403)
	elif transaction_type == 'expense':
		transaction = Expense.query.get_or_404(transaction_id)
		if transaction.party != current_user:
			abort(403)
	else:
		abort(404)
	return render_template('transaction.html', form1=form1, transaction_type=transaction_type, title=transaction.title, transaction=transaction)


@app.route("/transaction/<string:transaction_type>/<int:transaction_id>/update", methods=['GET', 'POST'])
@login_required
def update_transaction(transaction_type, transaction_id):
	if transaction_type == 'income':
		transaction = Income.query.get_or_404(transaction_id)
		if transaction.party != current_user:
			abort(403)
	elif transaction_type == 'expense':
		transaction = Expense.query.get_or_404(transaction_id)
		if transaction.party != current_user:
			abort(403)
	else:
		abort(404)
	form = TransactionForm()
	form1 = SetBudgetForm()
	if request.method == 'POST':
		if 'budget' in request.form:
			if form1.validate_on_submit():
				current_user.budget=form1.budget.data
				db.session.commit()
				flash('Your budget has been set!', 'success')
				return redirect(url_for('search'))
		else:
			if form.validate_on_submit():
				transaction.title = form.title.data
				transaction.amount = form.amount.data
				db.session.commit()
				flash(f'Your {transaction_type} has been updated!', 'success')
				return redirect(url_for('transaction', transaction_type=transaction_type, transaction_id=transaction.id))
	elif request.method == 'GET':
		form.title.data = transaction.title
		form.amount.data = transaction.amount
	return render_template('update_transaction.html', form1=form1, transaction_type=transaction_type, title='Update Transaction', form=form, legend='Update Transaction')


@app.route("/transaction/<string:transaction_type>/<int:transaction_id>/delete", methods=['GET', 'POST'])
@login_required
def delete_transaction(transaction_type, transaction_id):
	if transaction_type == 'income':
		transaction = Income.query.get_or_404(transaction_id)
		if transaction.party != current_user:
			abort(403)
	elif transaction_type == 'expense':
		transaction = Expense.query.get_or_404(transaction_id)
		if transaction.party != current_user:
			abort(403)
	else:
		abort(404)
	db.session.delete(transaction)
	db.session.commit()
	flash(f'Your {transaction_type} has been deleted!', 'success')
	return redirect(url_for('home'))

def send_reset_email(user):
	token = user.get_reset_token()
	msg = Message('Password Reset Request', sender='budgetapp4all@gmail.com', recipients=[user.email])
	msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.'''
	mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = RequestResetForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		send_reset_email(user)
		flash('An email has been sent on your account to reset your password.', 'info')
		return redirect(url_for('login'))
	return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	user = User.verify_reset_token(token)
	if user is None:
		flash('That is an invalid or expired token', 'warning')
		return redirect(url_for('reset_request'))
	form = ResetPasswordForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user.password = hashed_password
		db.session.commit()
		flash('Your password has been updated!', 'success')
		return redirect(url_for('login'))
	return render_template('reset_token.html', title='Reset Password', form=form)