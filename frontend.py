# -*- coding: utf-8 -*-
import os
import base64
import uuid
import tornado.httpserver
import tornado.httpclient
import tornado.ioloop
import tornado.options
import tornado.gen
import urllib
from tornado import web, escape
import pickle
from tornado.escape import to_unicode
from wtforms_tornado import Form
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo

from tornado.options import define, options
define("port", default=8000, help="run on the given port", type=int)

url_for_logics = r'http://localhost:8001/'

class LoginForm(Form):
	email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
	password = PasswordField('Password', validators=[Required()])
	submit = SubmitField('Sign in')

class RegistrationForm(Form):
	email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
	username = StringField('Username', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
												'Usernames must have only letters, numbers, dots or underscores.')])
	password = PasswordField('Password', validators=[Required(), EqualTo('password2', message='Passwords must match.')])
	password2 = PasswordField('Confirm password', validators=[Required()])
	submit = SubmitField('Sign up')

class RegistrationForm2(Form):
	email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
	username = StringField('Username', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
												'Usernames must have only letters, numbers, dots or underscores.')])
	mark = StringField('Car make', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z]*$', 0,
													'Car make must have only letters.')])
	model = StringField('Car model', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z0-9]*$', 0,
															'Car make must have only letters or numbers.')])
	state_number = StringField('State number', validators=[Required(), Length(1, 64), Regexp('^[A-Z][0-9]{3}[A-Z]{2}$', 0,
																						'State number must be as A000AA.')])
	region = StringField('Region', validators=[Required(), Length(1, 64), Regexp('^\d{2,3}$', 0, 'Region as 77 or 177')])
	password = PasswordField('Password', validators=[Required(), EqualTo('password2', message='Passwords must match.')])
	password2 = PasswordField('Confirm password', validators=[Required()])
	submit = SubmitField('Sign up')

class Flash(object):
	def __init__(self, message, data=None):
		self.message = message
		self.data = data

class MyHandler(tornado.web.RequestHandler):
	def cookie_name(self, key):
		return key + 'flash_cookie'

	def get_flash_cookie(self, key):
		return self.get_cookie(self.cookie_name(key))

	def has_flash(self, key):
		return self.get_flash_cookie(key) is not None

	def get_flash(self, key):
		if not self.has_flash(key):
			return None
		flash = tornado.escape.url_unescape(self.get_flash_cookie(key))
		try:
			flash_data = pickle.loads(flash)
			self.clear_cookie(self.cookie_name(key))
			return flash_data
		except:
			return None

	def set_flash(self, flash, key='error'):
		flash = pickle.dumps(flash)
		self.set_cookie(self.cookie_name(key), tornado.escape.url_escape(flash))


class IndexHandler(MyHandler):
	def get(self):
		if self.has_flash('error'):
			flash = self.get_flash('error')
			self.render('index.html', form=flash.data, flash_msg=flash.message)
		else:
			self.render('index.html',flash_msg=None)

class Type_choiceHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("type.html")

class RegistrationHandler(MyHandler):
	def get(self):
		form = RegistrationForm()
		if self.has_flash('error'):
			flash = self.get_flash('error')
			self.render('register.html', form=form, flash_msg=flash.message)
		else:
			self.render('register.html', form=form, flash_msg=None)

	@tornado.web.asynchronous
	@tornado.gen.engine
	def post(self):
		form = RegistrationForm(self.request.arguments)
		if form.validate():
			new_user = {
				'email': form.email.data,
				'password': form.password.data,
				'username': form.username.data,
				'type': 'passenger'
			}

			try:
				client = tornado.httpclient.AsyncHTTPClient()
				response = yield tornado.gen.Task (client.fetch, 'http://localhost:8001/register', method='POST',
												   body=urllib.urlencode(new_user))
				if response.error:
					self.write("Error: %s" % response.error)
				elif '201' in str(response):
					flash = Flash('You can now login.')
					self.set_flash(flash)
					self.redirect('login')
				self.finish()
			except:
				flash = Flash('Serves is temporarily unavailable')
				self.set_flash(flash)
				self.redirect("/")
		else:
			flash = Flash(form.errors)
			self.set_flash(flash)
			self.redirect('/register')

class Registration2Handler(MyHandler):
	def get(self):
		form = RegistrationForm2()
		if self.has_flash('error'):
			flash = self.get_flash('error')
			self.render('register2.html', form=form, flash_msg=flash.message)
		else:
			self.render('register2.html', form=form, flash_msg=None)

	@tornado.web.asynchronous
	@tornado.gen.engine
	def post(self):
		form = RegistrationForm2(self.request.arguments)
		if form.validate():
			new_user = {
            	'email': form.email.data,
                'password': form.password.data,
                'username': form.username.data,
				'mark': form.mark.data,
				'model': form.model.data,
				'state_number': form.state_number.data,
				'region': form.region.data,
                'type': 'taxi'
            }

			try:
				client = tornado.httpclient.AsyncHTTPClient()
				response = yield tornado.gen.Task(client.fetch, url_for_logics + 'register', method='POST',
												  body=urllib.urlencode(new_user))
				if response.error:
					self.write("Error: %s" % response.error)
				elif '201' in str(response):
					self.flash('You can now login.')
					self.redirect('login')
				self.finish()
			except:
				flash = Flash('Serves is temporarily unavailable')
				self.set_flash(flash)
				self.redirect("/")
		else:
			flash = Flash(form.errors)
			self.set_flash(flash)
			self.redirect('/register2')

class LoginHandler (tornado.web.RequestHandler):
	def get(self):
		form = LoginForm()
		self.render('login.html', form=form)

	@tornado.web.asynchronous
	@tornado.gen.engine
	def post(self):
		form = LoginForm(self.request.arguments)
		if form.validate_on_submit():
			login_information = {
            	'email': form.email.data,
            	'password': form.password.data
        	}
			try:
				client = tornado.httpclient.AsyncHTTPClient()
				response = yield tornado.gen.Task(client.fetch, url_for_logics + 'login', method='POST',
												  headers={"Content-Type": "application/json"}, body=login_information)
				if response.error:
					self.write("Error: %s" % response.error)
				elif '404' in str(response):
					self.flash('Invalid email or password')
				elif '200' in str(response):
					token = json.loads(response.body)['token'][0]
					user_type = json.loads(response.body)['user_type'][0]
					self.set_secure_cookie('my_session', value=token)
					self.set_secure_cookie('my_type', value=user_type)
					self.redirect('/')
				self.finish()
			except:
				self.flash('Serves is temporarily unavailable')
		else:
			self.render('login.html', form=form)

class LogoutHandler (tornado.web.RequestHandler):
	def get(self):
		self.clear_cookie('my_session')
		self.clear_cookie('my_type')
		self.redirect('/')

class Check_sessionHandler(tornado.web.RequestHandler):
	def check_session(self):
		token = self.get_secure_cookie('my_session')
		client = tornado.httpclient.HTTPClient()
		response = client.fetch(url_for_logics + 'token',method='POST', headers={"Content-Type": "application/json"}, body={'token': token})
		if '200' in str(response):
			return json.loads(response.body)['username'][0]['text']
		else:
			return 'unregistered'

class Make_orderHandler(Check_sessionHandler):
	def post(self):
		try:
			user_name = self.check_session()
		except:
			user_name = 'unregistered'
		if user_name != 'unregistered':
			try:
				client = tornado.httpclient.HTTPClient()
				response = client.fetch(url_for_logics + 'make_order', method='POST', headers={"Content-Type": "application/json"}, body={'user_name': user_name})
				result = json.loads(response.body)
				self.flash('Your order is accepted')
				###############
			except:
				self.flash('Serves is temporarily unavailable')
			self.redirect('/')
		else:
			self.flash('You must sign in')
			self.redirect('/login')

#class Get_infoHandler(Check_sessionHandler):
#	def post(self):
#		try:
#			user_name = self.check_session()
#		except:
#			user_name = 'unregistered'
#		if user_name != 'unregistered':
#			try:
#				client = tornado.httpclient.HTTPClient()
#				response = client.fetch(url_for_logics + 'get_info', method='POST', headers={"Content-Type": "application/json"}, body={'user_name': user_name})
#				result = json.loads(response.body)
#				username = result['username']
#				mark = result['mark']
#				model = result['model']
#				state_number = result['state_number']
#				region = result['region']
 #               ###############
#			except:
#				self.flash('Serves is temporarily unavailable')
#				self.redirect('/')

class Check_statusHandler(Check_sessionHandler):
	@tornado.web.asynchronous
	@tornado.gen.engine
	def post(self):
		client = tornado.httpclient.AsyncHTTPClient()
		try:
			user_id = yield tornado.gen.Task(self.check_session())
		except:
			user_id = 'unregistered'
		if user_id != 'unregistered':
			try:
				user_type = self.get_secure_cookie('my_type')
				response = yield tornado.gen.Task(client.fetch, url_for_logics + 'status', method='POST',
											    headers={"Content-Type": "application/json"},
                                                body=json.dumps(dict(user_type=user_type, user_id=user_id)))
				status = json.loads(response.body)['status'][0]
				self.write(status)
			except:
				self.send_error(response.error)
			self.finish()
		else:
			self.flash('You must sign in')
			self.redirect('/login')

class Concel_orderHandler(Check_sessionHandler):
	@tornado.web.asynchronous
	@tornado.gen.engine
	def post(self):
		client = tornado.httpclient.AsyncHTTPClient()
		try:
			user_id = yield tornado.gen.Task(self.check_session())
		except:
			user_id = 'unregistered'
		if user_id != 'unregistered':
			try:
				response = yield tornado.gen.Task(client.fetch, url_for_logics + 'concel', method='POST',
											    headers={"Content-Type": "application/json"},
                                                body=json.dumps(dict(user_id=user_id)))
				if '200' in str(response):
					self.flash('Your order has been canceled')
					self.redirect('/')
				self.finish()
			except:
				self.flash('Serves is temporarily unavailable')

class Start_calculationHandler(Check_sessionHandler):
	@tornado.web.asynchronous
	@tornado.gen.engine
	def post(self):
		client = tornado.httpclient.AsyncHTTPClient()
		try:
			user_id = yield tornado.gen.Task(self.check_session())
		except:
			user_id = 'unregistered'
		if user_id != 'unregistered':
			try:
				response = yield tornado.gen.Task(client.fetch, url_for_logics + 'start_calc', method='POST',
											    headers={"Content-Type": "application/json"},
                                                body=json.dumps(dict(user_id=user_id)))
				if '200' in str(response):
					self.flash('Have a nice trip')
					self.redirect('/')
				self.finish()
			except:
				self.flash('Serves is temporarily unavailable')

class Stop_calculationHandler(Check_sessionHandler):
	@tornado.web.asynchronous
	@tornado.gen.engine
	def post(self):
		client = tornado.httpclient.AsyncHTTPClient()
		try:
			user_id = yield tornado.gen.Task(self.check_session())
		except:
			user_id = 'unregistered'
		if user_id != 'unregistered':
			try:
				response = yield tornado.gen.Task(client.fetch, url_for_logics + 'stop_calc', method='POST',
											    headers={"Content-Type": "application/json"},
                                                body=json.dumps(dict(user_id=user_id)))
				if '200' in str(response):
					self.write('Trip cost is ' + json.loads(response.body)['cost'][0])
					#self.redirect('/')
				self.finish()
			except:
				self.flash('Serves is temporarily unavailable')

if __name__ == "__main__":
	tornado.options.parse_command_line()
	app = tornado.web.Application(
		handlers=[
			(r'/register', RegistrationHandler), (r'/', IndexHandler), (r'/type', Type_choiceHandler),
			(r'/register2', Registration2Handler), (r'/login', LoginHandler), (r'/logout', LogoutHandler)
		],
	template_path = os.path.join(os.path.dirname(__file__), "templates"),
	static_path = os.path.join(os.path.dirname(__file__), "static"),
	cookie_secret = base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes), debug=True, xsrf_cookies=False)
	http_server = tornado.httpserver.HTTPServer(app)
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()	

			
			
		


		
	
