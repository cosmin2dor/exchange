from django import forms

class SignupForm(forms.Form):
    firstname = forms.CharField(label='Firstname', max_length=100)
    lastname = forms.CharField(label='Lastname', max_length=100)
    username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password', max_length=250)
    password2 = forms.CharField(label='Password', max_length=250)

class LoginForm(forms.Form):
    username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password', max_length=250)

class SendForm(forms.Form):
    username = forms.CharField(label='Username', max_length=100)
    coin = forms.ChoiceField(label='Coin/Fiat', choices = (("USD", "USD"), 
                                        ("BTC", "BTC"), 
                                        ("ETH", "ETH")))
    amount = forms.FloatField(label='Amount')

class ExchangeForm(forms.Form):
    from_coin = forms.ChoiceField(label='From Coin/Fiat', choices = (("USD", "USD"), 
                                        ("BTC", "BTC"), 
                                        ("ETH", "ETH")))
    to_coin = forms.ChoiceField(label='To Coin/Fiat', choices = (("USD", "USD"), 
                                        ("BTC", "BTC"), 
                                        ("ETH", "ETH")))                                  
    amount = forms.FloatField(label='Amount')