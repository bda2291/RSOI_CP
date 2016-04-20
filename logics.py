import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.httpclient
import tornado.gen
import simplejson
import json
import tornado.web
import memcache

from tornado.options import define, options
define("port", default=8001, help="run on the given port", type=int)

url_for_session = 'http://localhost:5004/'
url_for_taxi = 'http://localhost:5002/'
url_for_passenger = 'http://localhost:5001/'
url_for_order = 'http://localhost:5003/'

memc = memcache.Client(['127.0.0.1:11212'], debug=1)

class RegistrationHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        if data['type'] == 'passenger':
            try:
                data.pop('type')
                client = tornado.httpclient.AsyncHTTPClient()
                response = yield tornado.gen.Task(client.fetch, url_for_passenger + 'register', method='POST',
                                                  headers={'Content-Type': 'application/json; charset=UTF-8'},
                                                  body = simplejson.dumps(data))
                if response.error:
                    self.send_error(response.error)
                elif response.code == 201:
                    self.set_status(201)
                self.finish()
            except:
                self.send_error(response.error)
        elif data['type'] == 'taxi':
            try:
                data.pop('type')
                client = tornado.httpclient.AsyncHTTPClient()
                response = yield tornado.gen.Task(client.fetch, url_for_taxi + 'register', method='POST',
												  headers={'Content-Type': 'application/json; charset=UTF-8'},
                                                  body=simplejson.dumps(data))
                if response.error:
                    self.send_error(response.error)
                elif response.code == 201:
                    self.set_status(201)
                self.finish()
            except:
                self.send_error(response.error)

class LoginHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self):
        Taxi = True
        data = tornado.escape.json_decode(self.request.body)
        try:
            client = tornado.httpclient.AsyncHTTPClient()
            response = yield tornado.gen.Task(client.fetch, url_for_taxi + 'login', method='POST',
                                              headers={"Content-Type": "application/json; charset=UTF-8"},
                                              body=simplejson.dumps(data))
            if response.code == 404:
                Taxi = False
            elif response.code == 200:
                user_id = json.loads(response.body)['taxi_id']
                token = self.login_for_session(user_id)
                self.write(json.dumps(dict(status=200, token=token, user_type='taxi')))
        except:
            self.send_error(response.error)
        if Taxi == False:
            try:
                client = tornado.httpclient.AsyncHTTPClient()
                response = yield tornado.gen.Task(client.fetch, url_for_passenger + 'login', method='POST',
												  headers={"Content-Type": "application/json; charset=UTF-8"},
                                                  body=simplejson.dumps(data))
                if response.code == 404:
                    self.set_status(404)
                elif response.code == 200:
                    user_id = json.loads(response.body)['pass_id'][0]
                    token = self.login_for_session(user_id)
                    self.write(json.dumps(dict(status=200, token=token, user_type='passenger')))
            except:
                self.send_error(response.error)
        self.finish()

    def login_for_session(self, user_id=None):
        if user_id is not None:
            try:
                client = tornado.httpclient.HTTPClient()
                response = client.fetch(url_for_session + 'login', method='POST',
                                        headers={"Content-Type": "application/json; charset=UTF-8"},
                                        body=json.dumps(dict(user_id=user_id)))
                token = json.loads(response.body)['token']
                return token
            except:
                self.send_error(response.error)
        else:
            return None

class Check_sessionHandler(tornado.web.RequestHandler):
    #@tornado.web.asynchronous
    #@tornado.gen.engine
    def post(self):
        token = tornado.escape.json_decode(self.request.body)['token']
        try:
            client = tornado.httpclient.HTTPClient()
            response = client.fetch(url_for_session + 'token', method='POST',
									headers={"Content-Type": "application/json; charset=UTF-8"},
                                    body=json.dumps(dict(token=token)))
            if response.code == 404:
                self.set_status(404)
            elif response.code == 200:
                user_id = json.loads(response.body)['user_id']
                self.write(json.dumps(dict(status=200, user_id=user_id)))
            #self.finish()
        except:
            self.send_error(response.error)

class Check_statusHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        user_id = data['user_id']
        user_type = data['user_type']
        if user_type == 'taxi':
            try:
                client = tornado.httpclient.AsyncHTTPClient()
                response = yield tornado.gen.Task(client.fetch, url_for_taxi + 'check_status', method='POST',
                                              headers={"Content-Type": "application/json; charset=UTF-8"},
                                              body=json.dumps(dict(user_id=user_id)))

                status = json.loads(response.body)['status']
                self.write(status)
            except:
                self.send_error(response.error)
        elif user_type == 'passenger':
            try:
                client = tornado.httpclient.AsyncHTTPClient()
                response = yield tornado.gen.Task(client.fetch, url_for_passenger + 'check_status', method='POST',
                                              headers={"Content-Type": "application/json; charset=UTF-8"},
                                              body=json.dumps(dict(user_id=user_id)))
                status = json.loads(response.body)['status']
                self.write(status)
            except:
                self.send_error(response.error)
        self.finish()

class Change_statusHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def change_status(self, user_type, status, user_id):
        if user_type == 'taxi':
            try:
                client = tornado.httpclient.AsyncHTTPClient()
                response = yield tornado.gen.Task(client.fetch, url_for_taxi + 'change_status', method='POST',
												headers={"Content-Type": "application/json; charset=UTF-8"},
                                                body=json.dumps(dict(status=status, user_id=user_id)))
                if response.code == 200:
                    self.set_status(200)
            except:
                self.send_error(response.error)
        elif user_type == 'passenger':
            try:
                client = tornado.httpclient.AsyncHTTPClient()
                response = yield tornado.gen.Task(client.fetch, url_for_passenger + 'change_status', method='POST',
												headers={"Content-Type": "application/json; charset=UTF-8"},
                                                body=json.dumps(dict(status=status, user_id=user_id)))
                if response.code == 200:
                    self.set_status(200)
            except:
                self.send_error(response.error)
        self.finish()

class Make_orderHandler(Change_statusHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        pass_id = data['user_id']
        coordinate = data['coordinates']
        try:
            client = tornado.httpclient.AsyncHTTPClient()
            response = yield tornado.gen.Task(client.fetch, url_for_order + 'make_order', method='POST',
											    headers={"Content-Type": "application/json; charset=UTF-8"},
                                                body=json.dumps(dict(pass_id=pass_id, coordinate=coordinate)))
            radius = 0
            taxi_info = ''
            while taxi_info == '':
                radius += 100
                taxi_info = self.check_taxi(coordinate, radius)
                taxi_id = taxi_info['taxi_id']
            self.add_taxi_to_order(pass_id, taxi_id)
            self.change_status('passenger', 'accepted', pass_id)
            self.write(taxi_info)
        except:
            self.send_error(response.error)
        self.finish()

    def check_taxi(self, coordinate, radius):
        try:
            client = tornado.httpclient.HTTPClient()
            response = client.fetch(url_for_taxi + 'check_taxi', method='POST',
												headers={"Content-Type": "application/json; charset=UTF-8"},
                                                body=json.dumps(dict(radius=radius, coordinate=coordinate)))
            taxi = json.loads(response.body)
            return taxi
        except:
            self.send_error(response.error)


    def add_taxi_to_order(self, pass_id, taxi_id):
        try:
            print(json.dumps(dict(pass_id=pass_id, taxi_id=taxi_id)))
            client = tornado.httpclient.HTTPClient()
            response = client.fetch(url_for_order + 'add_taxi', method='POST',
												headers={"Content-Type": "application/json; charset=UTF-8"},
                                                body=json.dumps(dict(pass_id=pass_id, taxi_id=taxi_id)))
            self.set_status(200)
        except:
            self.send_error(response.error)


#class Check_aordHandler(tornado.web.RequestHandler):

#class Get_infoHandler(tornado.web.RequestHandler):

class Concel_orderHandler(Change_statusHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self):
        pass_id = tornado.escape.json_decode(self.request.body)['user_id']
        try:
            client = tornado.httpclient.AsyncHTTPClient()
            response = yield tornado.gen.Task(client.fetch, url_for_order + 'concel_order', method='POST',
											    headers={"Content-Type": "application/json; charset=UTF-8"},
                                                body=json.dumps(dict(pass_id=pass_id)))
            taxi_id = json.loads(response.body)['taxi_id']
            self.change_status('taxi', 'free', taxi_id)
            self.change_status('passenger', 'free', pass_id)
            self.set_status(200)
            self.finish()
        except:
            self.send_error(response.error)

class Start_calculationHandler(Change_statusHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self):
        taxi_id = tornado.escape.json_decode(self.request.body)['user_id']
        try:
            client = tornado.httpclient.AsyncHTTPClient()
            response = yield tornado.gen.Task(client.fetch, url_for_order + 'start_calculation', method='POST',
											    headers={"Content-Type": "application/json; charset=UTF-8"},
                                                body=json.dumps(dict(taxi_id=taxi_id)))
            if response.code == 200:
                self.change_status('taxi', 'transit', taxi_id)
                self.set_status(200)
            else:
                self.send_error(500)
            self.finish()
        except:
            self.send_error(response.error)

class Stop_calculationHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self):
        taxi_id = tornado.escape.json_decode(self.request.body)['user_id']
        try:
            client = tornado.httpclient.AsyncHTTPClient()
            response = yield tornado.gen.Task(client.fetch, url_for_order + 'stop_calculation', method='POST',
											    headers={"Content-Type": "application/json; charset=UTF-8"},
                                                body=json.dumps(dict(taxi_id=taxi_id)))
            if response.code == 200:
                self.change_status('taxi', 'free', taxi_id)
                cost = json.loads(response.body)['cost']
                pass_id = json.loads(response.body)['pass_id']
                self.write(json.dumps(dict(status=200, pass_id=pass_id, cost=cost)))
            else:
                self.send_error(500)
            self.finish()
        except:
            self.send_error(response.error)

#class Post_priceHandler(tornado.web.RequestHandler):

#class Block_userHandler(tornado.web.RequestHandler):

class Post_coordinatesHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self):
        taxi_id = tornado.escape.json_decode(self.request.body)['user_id']
        coordinate = tornado.escape.json_decode(self.request.body)['coordinates']
        try:
            client = tornado.httpclient.AsyncHTTPClient()
            response = yield tornado.gen.Task(client.fetch, url_for_taxi + 'post_coordinates', method='POST',
											    headers={"Content-Type": "application/json; charset=UTF-8"},
                                                body=json.dumps(dict(user_id=taxi_id, coordinate=coordinate)))
            taxi_status = json.loads(response.body)['taxi_status']
            if taxi_status == 'transit':
                response = yield tornado.gen.Task(client.fetch, url_for_order + 'post_coordinates', method='POST',
											    headers={"Content-Type": "application/json; charset=UTF-8"},
                                                body=json.dumps(dict(taxi_id=taxi_id, coordinate=coordinate)))
            else:
                self.set_status(200)
            self.finish()
        except:
            self.send_error(response.error)


if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(
	handlers=[
		(r'/register', RegistrationHandler), (r'/login', LoginHandler),
		(r'/make_order', Make_orderHandler), (r'/token', Check_sessionHandler),
        (r'/status', Check_statusHandler), (r'/change_status', Change_statusHandler),
        (r'/concel', Concel_orderHandler), (r'/coordinates', Post_coordinatesHandler),
        (r'/start_calc', Start_calculationHandler), (r'/stop_calc', Stop_calculationHandler)
	]
)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
