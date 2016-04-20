import os
from hashlib import sha256
from uuid import uuid4
from flask import Flask, jsonify, request
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask.ext.moment import Moment
from flask.ext.script import Manager, Server
import memcache

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = 'you-will-never-guess'
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config["JSON_SORT_KEYS"] = True
db = SQLAlchemy(app)

manager = Manager(app)
manager.add_command("runserver", Server(host='127.0.0.1', port=5004))
moment = Moment(app)

memc = memcache.Client(['127.0.0.1:11211'], debug=0)

class Session(db.Model):
    __tablename__ = 'session'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, unique=True, index=True)
    token = db.Column(db.String(128), unique=True,index=True)
    expire_time = db.Column(db.DateTime, unique=True,index=True)

    def to_json(self):
        session_in_json = {
            'token': self.token,
            'user_id': self.user_id
        }
        return session_in_json

    def __repr__(self):
        return '<User_id {} Token {}>'.format(self.user_id, self.token)

@app.route('/login/', methods=['POST'])
def login():
    try:
        user_id = request.json.get('user_id')
        #ses = memc.get(user_id)
        #if ses is None:
        ses = Session.query.filter_by(user_id=user_id).first()
        if ses is None:
            token = sha256(str(uuid4()).encode('UTF-8')).hexdigest()
            expire_time = datetime.now() + timedelta(days=30)
            ses = Session(user_id=user_id, token=token, expire_time=expire_time)
            db.session.add(ses)
            db.session.commit()
            memc.set(token, [user_id, expire_time], time=3000)
            return jsonify(ses.to_json()), 200
        else:
            if ses.expire_time > datetime.now():
                ses.expire_time = (datetime.now() + timedelta(days=30))
                token = ses.token
                db.session.add(ses)
                db.session.commit()
                memc.set(token, [user_id, ses.expire_time], time=3000)
                return jsonify(ses.to_json()), 200
            else:
                memc.delete(user_id)
                db.session.delete(ses)
                db.session.commit()
                return '', 404
    except:
        return '', 500

@app.route('/token/', methods=['POST'])
def token():
    try:
        token = request.json.get('token')
        ses = memc.get(token)
        if ses is not None:
            user_id = ses[0]
            expire_time = ses[1]
        else:
            ses = Session.query.filter_by(token=token).first()
            user_id = ses.user_id
            expire_time = ses.expire_time
        if ses is not None and expire_time > datetime.now():
            return jsonify(dict(user_id=user_id)), 200
        return '', 404
    except:
        return '', 500

if __name__ == '__main__':
    manager.run()
