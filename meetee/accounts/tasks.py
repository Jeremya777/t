from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_verification_email(email, username, token):
    subject = "Conferma la tua registrazione"
    message = f"Ciao {username},\n\nPer completare la registrazione, clicca sul link seguente:\nhttp://localhost:8000/verify/{token}/\n\nGrazie!"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
