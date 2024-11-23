from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# Imposta il nome del modulo delle impostazioni di Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meetee.settings')

# Inizializza l'applicazione Celery
app = Celery('meetee')

# Carica le impostazioni dal file settings.py, utilizzando il prefisso `CELERY`
app.config_from_object('django.conf:settings', namespace='CELERY')

# Carica i task dalle app registrate
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
