from django import forms

class SignupForm(forms.Form):
    firstname = forms.CharField(label='Firstname', max_length=100)
    lastname = forms.CharField(label='Lastname', max_length=100)
    username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password', max_length=250)

class LoginForm(forms.Form):
    username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password', max_length=250)