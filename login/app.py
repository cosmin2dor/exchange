import os
import hashlib
import uuid
import json

from flask import Flask, abort, request, jsonify, g, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

# extensions
db = SQLAlchemy(app)
auth = HTTPBasicAuth()
tokens = { 1:'test'.encode('utf-8', 'ignore')}
users = {'test'.encode('utf-8', 'ignore'):1}

def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]


def init_db():
    """For use on command line for setting up
    the database.
    """

    db.drop_all()
    db.create_all()

    test_user = User(username='test', 
                     usd_balance=10000,
                     password_hash=hashlib.sha512('test'.encode('utf-8')).hexdigest())
    db.session.add(test_user)
    db.session.commit()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(32), index = True)
    password_hash = db.Column(db.String(128))
    eth_balance = db.Column(db.Float, default=0)
    btc_balance = db.Column(db.Float, default=0)
    usd_balance = db.Column(db.Float, default=0)

    def hash_password(self, password):
        import hashlib, uuid
        hashed_password = hashlib.sha512(password.encode('utf-8')).hexdigest()
        self.password_hash = hashed_password

    def verify_password(self, password):
        hashed_password = hashlib.sha512(password.encode('utf-8')).hexdigest()
        return hashed_password == self.password_hash

    def generate_auth_token(self, expiration = 600):
        s = Serializer(app.config['SECRET_KEY'], expires_in = expiration)
        return s.dumps({ 'id': self.id })

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        user = User.query.get(data['id'])
        return user

class ExchangeTransaction(db.Model):
    __tablename__ = 'exchange_transactions'
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.String(32), index = True)
    from_coin = db.Column(db.String(32), index = True)
    to_coin = db.Column(db.String(32), index = True)
    amount = db.Column(db.Float, default=0)
    time = db.Column(db.DateTime, default=db.func.current_timestamp())

    @property
    def serialize(self):
       """Return object data in easily serializable format"""
       return {
           'from_coin'         : self.from_coin,
           'to_coin'           : self.to_coin,
           'amount'         : self.amount,
           'time'              : dump_datetime(self.time),
       }


class TransferTransaction(db.Model):
    __tablename__ = 'transfer_transactions'
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.String(32), index = True)
    username = db.Column(db.String(32), index = True)
    coin = db.Column(db.String(32), index = True)
    amount = db.Column(db.Float, default=0)
    time = db.Column(db.DateTime, default=db.func.current_timestamp())

    @property
    def serialize(self):
       """Return object data in easily serializable format"""
       return {
           'username'       : self.username,
           'coin'           : self.coin,
           'amount'         : self.amount,
           'time'           : dump_datetime(self.time),
       }


@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/users/register', methods = ['POST','GET'])
def new_user():
    username = request.args.get('username')
    password = request.args.get('password')
    if username is None or password is None:
        return 'Invalid request'
    if User.query.filter_by(username = username).first() is not None:
        return 'User exists'
    user = User(username = username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    token = user.generate_auth_token()
    tokens[user.id] = token
    users[token] = user.id
    print(tokens)
    return token

@app.route('/users/login', methods = ['POST','GET'])
def login_user():
    username = request.args.get('username')
    password = request.args.get('password')
    if username is None or password is None:
        return 'Invalid request'
    user = User.query.filter_by(username = username).first()
    if user is None:
        return 'User does not exists'
    if not user.verify_password(password):
        return 'Incorrect Password'
    if user.id in tokens.keys():
        return tokens[user.id]
    token = user.generate_auth_token()
    tokens[user.id] = token
    users[token] = user.id
    print(tokens)
    return token

@app.route('/users/<string:token>')
def get_user(token):
    token = token.encode('utf-8', 'ignore')
    print(users)
    if token not in users:
        print("Invalid token:" + str(token))
        return 'Invalid token'
    user = User.query.get(users[token])
    if not user:
        abort(400)

    exchange_transactions = list(ExchangeTransaction.query.filter_by(user_id=user.id).all())
    transfer_transactions = list(TransferTransaction.query.filter_by(user_id=user.id).all())
    transfer_transactions = [i.serialize for i in transfer_transactions]
    exchange_transactions = [i.serialize for i in exchange_transactions]

    return jsonify({'username': user.username,
                    'eth': user.eth_balance,
                    'btc': user.btc_balance,
                    'usd': user.usd_balance,
                    'exchange':exchange_transactions, 
                    'transfer':transfer_transactions,
                    })

def send_coin(to_user, from_user, coin, amount):
    if to_user.id == from_user.id:
        return 'Are you playing with me?'
    if coin == 'eth':
        if from_user.eth_balance < amount:
            return 'Insufficient funds.'
        from_user.eth_balance -= amount
        to_user.eth_balance += amount
        return 
    if coin == 'btc':
        if from_user.btc_balance < amount:
            return 'Insufficient funds.'
        from_user.btc_balance -= amount
        to_user.btc_balance += amount
    if coin == 'usd':
        if from_user.usd_balance < amount:
            return 'Insufficient funds.'
        from_user.usd_balance -= amount
        to_user.usd_balance += amount

    transaction = TransferTransaction(
        user_id = from_user.id,
        coin = coin, username = to_user.username, amount = -amount)
    
    db.session.add(transaction)

    transaction = TransferTransaction(
        user_id = to_user.id,
        coin = coin, username = from_user.username, amount = amount)

    db.session.add(transaction)
    db.session.commit()
    return 'Transfer made.'

@app.route('/users/send/<string:token>')
def send(token):
    token = token.encode('utf-8', 'ignore')
    if token is None:
        return 'Invalid request'
    if token not in users:
        print(users)
        return 'Invalid token'
    to_username = request.args.get('username')
    coin = request.args.get('coin')
    amount = request.args.get('amount')
    if to_username is None or coin is None or amount is None:
        return 'Invalid request'
    coin = coin.lower()
    accepted_coins = ['usd', 'eth', 'btc']

    try:
        amount = float(amount)
    except:
        print(amount)
        return 'Invalid amount'

    if amount < 0 or coin not in accepted_coins:
        return 'Invalid request'
    to_user = User.query.filter_by(username = to_username).first()
    if to_user is None:
        return 'User does not exists'
    from_user = User.query.get(users[token])
    return send_coin(to_user, from_user, coin, amount)

def exg_coin(user, to_coin, from_coin, amount):
    if to_coin == from_coin:
        return 'Bye'
    if from_coin == 'eth':
        if user.eth_balance < amount:
            return 'Insufficient funds.'
        user.eth_balance -= amount
    if from_coin == 'btc':
        if user.btc_balance < amount:
            return 'Insufficient funds.'
        user.btc_balance -= amount
    if from_coin == 'usd':
        if user.usd_balance < amount:
            return 'Insufficient funds.'
        user.usd_balance -= amount

    if to_coin == 'usd':
        coin_price = float(requests.get('http://54.93.120.171:8081/{}'.format(from_coin)).text)
        recv_amount = amount * coin_price
    elif from_coin == 'usd':
        to_price = float(requests.get('http://54.93.120.171:8081/{}'.format(to_coin)).text)
        rate = 1/to_price
        recv_amount = amount * rate
    else:
        to_price = float(requests.get('http://54.93.120.171:8081/{}'.format(to_coin)).text)
        from_price = float(requests.get('http://54.93.120.171:8081/{}'.format(from_coin)).text)
        rate = from_price/to_price
        recv_amount = amount * rate

    if to_coin == 'eth':
        user.eth_balance += recv_amount
    if to_coin == 'btc':
        user.btc_balance += recv_amount
    if to_coin == 'usd':
        user.usd_balance += recv_amount

    transaction = ExchangeTransaction(
                               user_id = user.id,
                               from_coin = from_coin, to_coin = to_coin,
                               amount = amount)
    db.session.add(transaction)
    db.session.commit()

    return 'Exchange made.'
    
@app.route('/users/exchange/<string:token>')
def exchange(token):
    token = token.encode('utf-8', 'ignore')
    from_coin = request.args.get('from_coin')
    to_coin = request.args.get('to_coin')
    amount = request.args.get('amount')
    if from_coin is None or to_coin is None or amount is None:
        return 'Invalid request'
    to_coin = to_coin.lower()
    from_coin = from_coin.lower()
    accepted_coins = ['usd', 'eth', 'btc']
    try:
        amount = float(amount)
    except:
        return 'Invalid amount'
    if amount < 0 or from_coin not in accepted_coins or to_coin not in accepted_coins:
        return 'Invalid request'
    user = User.query.get(users[token])
    return exg_coin(user, to_coin, from_coin, amount)
    