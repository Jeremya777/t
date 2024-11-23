# accounts/forms.py

from django import forms
from django.contrib.auth.models import User
import re
from .models import Profile
class RegisterStep1Form(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Nickname",
        widget=forms.TextInput(attrs={'class': 'form-control','id':'username'}),
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 3:
            raise forms.ValidationError("Il nickname deve essere lungo almeno 3 caratteri.")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Questo nickname è già in uso. Scegline un altro.")
        return username

class RegisterStep2Form(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'id':'email'}),
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            raise forms.ValidationError("Per favore, inserisci un'email valida.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Questa email è già in uso. Usa un'altra email.")
        return email

class RegisterStep3Form(forms.Form):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id':'password'}),
    )
    password_confirm = forms.CharField(
        label="Conferma Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control','id':'password2'}),
    )

    def clean_password(self):
        password = self.cleaned_data.get('password')
        password_regex = r'^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{7,}$'
        if not re.match(password_regex, password):
            raise forms.ValidationError(
                "La password deve essere lunga almeno 7 caratteri, contenere un numero, un carattere speciale e una lettera maiuscola."
            )
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Le password non coincidono.")

class LoginStep1Form(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Username",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

class LoginStep2Form(forms.Form):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
class PersonalDataForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_image', 'first_name', 'last_name', 'age']
        widgets = {
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cognome'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Età'}),
        }

class CharacteristicsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'interests', 'gender', 'looking_for', 'location']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Breve bio...'}),
            'interests': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Interessi'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'looking_for': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Località'}),
        }
