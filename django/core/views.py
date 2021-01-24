from django.http import HttpResponseRedirect
from django.shortcuts import render
from .forms import SignupForm, LoginForm

import requests
import json

def get_user(request):
    token = request.session.get('token', False)
    print(token)

    if token is False:
        return

    response = requests.get('http://localhost:8000/users/{}'.format(token))
    print('http://localhost:8000/users/{}'.format(token))
    try:
        return json.loads(response.text)
    except:
        return

def login_user(token, request):
    request.session['token'] = token
    request.session['logged_in'] = True

    user = get_user(request)

    if user is None:
        print("Cannot login user.")
        return

    request.session['user'] = user

def logout_user(request):
    try:
        del request.session['token']
        del request.session['user']
        del request.session['logged_in']
    except KeyError:
        pass

def is_authenticated(request):
    #TODO This should check with the api also
    return request.session.get("token", False) is not False

def home(request):
    if is_authenticated(request):
        user = get_user(request)
        return render(request, 'authenticated_home.html', {'user': user})
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
                token = response.text
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
                token = response.text
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
