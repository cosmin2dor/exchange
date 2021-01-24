from django.http import HttpResponseRedirect
from django.shortcuts import render
from .forms import SignupForm, LoginForm, ExchangeForm, SendForm
import traceback 

import requests
import json

def get_user(request):
    token = request.session.get('token', False)
    if token is False:
        print("Token is false.")
        return None
    print('http://localhost:8000/users/{}'.format(token))
    response = requests.get('http://localhost:8000/users/{}'.format(token))
    
    if "Invalid token" in response.text:
        delete_session(request)
        return HttpResponseRedirect('/login/')
    try:
        print(json.loads(response.text))
        return json.loads(response.text)
    except Exception as e:
        traceback.print_exc() 
        return None

def login_user(token, request):
    request.session['token'] = token
    request.session['logged_in'] = True

    user = get_user(request)

    if user is None:
        print("Cannot login user.")
        return

    request.session['user'] = user

def delete_session(request):
    del request.session['token']
    del request.session['user']
    del request.session['logged_in']

def logout_user(request):
    try:
        delete_session(request)
    except KeyError:
        pass

def is_authenticated(request):
    #TODO This should check with the api also
    return request.session.get("token", False) is not False

def get_prices():
    eth_price = 0
    btc_price = 0
    try:
        eth_price = float(requests.get('http://54.93.120.171:8081/eth').text)
        btc_price = float(requests.get('http://54.93.120.171:8081/btc').text)
    except:
        traceback.print_exc()
    return eth_price, btc_price

def send_request(form, token):
    response = requests.get(
        'http://localhost:8000/users/send/{}'.format(token),
        params = {
            'username': form.cleaned_data['username'],
            'coin': form.cleaned_data['coin'],
            'amount': form.cleaned_data['amount'],
        }
    )
    return response.text

def exchange_request(form, token):
    response = requests.get(
        'http://localhost:8000/users/exchange/{}'.format(token),
        params = {
            'from_coin': form.cleaned_data['from_coin'],
            'to_coin': form.cleaned_data['to_coin'],
            'amount': form.cleaned_data['amount'],
        }
    )
    return response.text

def is_successful(response):
    return 'made' in response

def home(request):
    info_message = None
    error_message = None
    if request.method == 'POST':
        token = request.session.get('token', None)
        if not token:
            return HttpResponseRedirect('/login')
        response = ""
        form = SendForm(request.POST)
        if form.is_valid():
            print('Sent valid send form.')
            response = send_request(form, token)

        form = ExchangeForm(request.POST)
        if form.is_valid():
            print('Sent valid exchange form.')
            response = exchange_request(form, token)
        if is_successful(response):
            info_message = response
        else:
            error_message = response

    if is_authenticated(request):
        user = get_user(request)
        eth_price, btc_price = get_prices()
        return render(request, 'authenticated_home.html', {'user': user, 'eth_price': eth_price,
                                                           'btc_price': btc_price,
                                                           'send_form': SendForm(),
                                                           'exchange_form': ExchangeForm(),
                                                           'info_message': info_message,
                                                           'error_message': error_message})
    else:
        print("User not authenticated.")
        return HttpResponseRedirect('/login/')

def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            response = requests.get(
                'http://localhost:8000/users/login',
                params = {
                    'username': form.cleaned_data['username'],
                    'password': form.cleaned_data['password'],
                }
            )

            if response.status_code == 200:
                message = response.text

                if (message == "User does not exists" or message == "Incorrect Password"):
                    print("no user found")
                    return render(request, 'login.html', {'error_message': "Incorrect Password or User does not exists."})
                else:
                    token = message
                    login_user(token, request)
            else:
                print('Login API call failed.')
            return HttpResponseRedirect('/')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():

            if form.cleaned_data['password'] != form.cleaned_data['password2']:
                return render(request, 'signup.html', {'error_message': "Passwords don't match."}) 

            response = requests.get(
                'http://localhost:8000/users/register',
                params = {
                    'username':     form.cleaned_data['username'],
                    'password':     form.cleaned_data['password'],
                    'firstname':    form.cleaned_data['firstname'],
                    'lastname':     form.cleaned_data['lastname'],
                }
            )

            if response.status_code == 200:
                message = response.text

                if message == "User exists":
                    return render(request, 'signup.html', {'error_message': "User already exists."})
                else:
                    token = message
                    login_user(token, request)
            else:
                print('Register API call failed.')
            return HttpResponseRedirect('/')
    else:
        form = SignupForm()

    return render(request, 'signup.html', {'form': form})

def logout(request):
    logout_user(request)
    return HttpResponseRedirect('/')
