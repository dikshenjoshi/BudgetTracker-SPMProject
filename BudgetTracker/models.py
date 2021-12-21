from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from BudgetTracker import db, login_manager, app
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	first_name = db.Column(db.String(20), nullable=False)
	last_name = db.Column(db.String(20), nullable=False)
	email = db.Column(db.String(100), unique=True, nullable=False)
	password = db.Column(db.String(60), nullable=False)
	incomes = db.relationship('Income', backref='party', lazy=True)
	expenses = db.relationship('Expense', backref='party', lazy=True)
	offset = db.Column(db.Integer, nullable=True)
	budget = db.Column(db.Integer, nullable=True)

	def get_reset_token(self, expires_sec=1800):
		s = Serializer(app.config['SECRET_KEY'], expires_sec)
		return s.dumps({'user_id': self.id}).decode('utf-8')

	@staticmethod
	def verify_reset_token(token):
		s = Serializer(app.config['SECRET_KEY'])
		try:
			user_id = s.loads(token)['user_id']
		except:
			return None
		return User.query.get(user_id)
	
	def __repr__(self):
		return f"User('{self.first_name}', '{self.last_name}', '{self.email}')"

class Income(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(100), nullable=False)
	amount = db.Column(db.Integer, nullable=False)
	date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

	def __repr__(self):
		return f"Income('{self.title}', '{self.amount}', {self.date_posted}')"

class Expense(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(100), nullable=False)
	amount = db.Column(db.Integer, nullable=False)
	date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

	def __repr__(self):
		return f"Expense('{self.title}', '{self.amount}', {self.date_posted}')"