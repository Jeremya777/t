import json
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import JsonResponse
from django.middleware import csrf
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views import View
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from formtools.wizard.views import SessionWizardView
from django.views.decorators.http import require_GET
from .models import Profile
from .forms import RegisterStep1Form, RegisterStep2Form, RegisterStep3Form, LoginStep1Form, LoginStep2Form
from .tasks import send_verification_email
from django.utils.crypto import get_random_string
from .forms import PersonalDataForm, CharacteristicsForm
from django.http import JsonResponse
from django.views.decorators.csrf import CsrfViewMiddleware, csrf_protect



@csrf_protect
class RegisterWizard(View):
    template_name = 'accounts/register_wizard.html'
    form_list = [RegisterStep1Form, RegisterStep2Form, RegisterStep3Form]

    def done(self, form_list, **kwargs):
        form_data = [form.cleaned_data for form in form_list]
        username = form_data[0]['username']
        email = form_data[1]['email']
        password = form_data[2]['password']

        # Creazione dell'utente (inizialmente inattivo)
        user = User.objects.create_user(username=username, email=email, password=password, is_active=True)
        user.save()

      # Generazione token di verifica e invio dell'email
        verification_token = get_random_string(32)
        user.profile.verification_token = verification_token
        user.profile.save()

        #send_verification_email.delay(email, username, verification_token)

        messages.success(self.request, "Registrazione completata! Controlla la tua email per verificare l'account.")
        return redirect('accounts:login_wizard')

def verify_email(request, token):
    try:
        profile = Profile.objects.get(verification_token=token)
        profile.user.is_active = True
        profile.user.save()
        profile.verification_token = ""
        profile.save()
        messages.success(request, "Email verificata con successo!")
        return redirect('accounts:login_wizard')
    except Profile.DoesNotExist:
        messages.error(request, "Token di verifica non valido.")
        return redirect('accounts:register')


# Funzione di Login aggiornata
@csrf_protect
class LoginWizard(SessionWizardView):
    template_name = 'accounts/login_wizard.html'
    form_list = [LoginStep1Form, LoginStep2Form]

    def done(self, form_list, **kwargs):
        form_data = [form.cleaned_data for form in form_list]
        username = form_data[0]['username']
        password = form_data[1]['password']

        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
            messages.success(self.request, f"Sei ora loggato come {username}.")
            
            return redirect('accounts:dashboard')
        else:
            messages.error(self.request, "Username o password errati.")
            return redirect('accounts:login_wizard')
logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        # Potrebbe non essere necessario, poiché il profilo viene creato tramite signals.
        profile = Profile.objects.create(user=request.user)

    user = request.user

    if not profile.is_profile_complete:
        if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if 'personal_data_submit' in request.POST:
                personal_form = PersonalDataForm(request.POST, request.FILES, instance=profile)
                if personal_form.is_valid():
                    personal_form.save()
                    messages.success(request,
                                     "Dati personali aggiornati con successo. Ora inserisci le tue caratteristiche.")
                    logger.info("Personal data updated successfully.")
                    return JsonResponse({'success': True})
                else:
                    errors = {field: [{'message': str(error)} for error in error_list] for field, error_list in
                              personal_form.errors.items()}
                    logger.warning(f"Personal form errors: {errors}")
                    return JsonResponse({'success': False, 'errors': errors})

            elif 'characteristics_submit' in request.POST:
                characteristics_form = CharacteristicsForm(request.POST, instance=profile)
                if characteristics_form.is_valid():
                    characteristics_form.save()
                    profile.is_profile_complete = True
                    profile.save()
                    messages.success(request, "Profilo completato con successo!")
                    logger.info("Profile completed successfully.")
                    return JsonResponse({'success': True})
                else:
                    errors = {field: [{'message': str(error)} for error in error_list] for field, error_list in
                              characteristics_form.errors.items()}
                    logger.warning(f"Characteristics form errors: {errors}")
                    return JsonResponse({'success': False, 'errors': errors})

            else:
                logger.error("Invalid form submission.")
                return JsonResponse({'success': False, 'error': 'Invalid form submission.'})

        else:
            personal_form = PersonalDataForm(instance=profile)
            characteristics_form = CharacteristicsForm(instance=profile)

            context = {
                'personal_form': personal_form,
                'characteristics_form': characteristics_form,
                'is_profile_complete': profile.is_profile_complete,
                'user': user,
                'profile': profile,
            }
            return render(request, 'accounts/dashboard.html', context)

    return render(request, 'accounts/dashboard.html', {'user': user, 'profile': profile})

def logout_view(request):
    logout(request)
    messages.info(request, "Sei stato disconnesso.")
    return redirect('accounts:login_wizard')

def test_template(request):
    return render(request, 'accounts/test_template.html')

@login_required
@require_GET
def search_users(request):
    query = request.GET.get('q', '').strip()
    if query:
        # Filtra gli utenti per username che contiene la query, case-insensitive
        users = User.objects.filter(username__icontains=query).values('username')
        users_list = list(users)
    else:
        users_list = []

    return JsonResponse({'users': users_list})


@login_required
def find_active_user(request):
    # Cerca un utente online che non sia il richiedente stesso
    active_user = Profile.objects.filter(status='online').exclude(user=request.user).first()

    if active_user:
        return JsonResponse({'status': 'success', 'user_id': active_user.user.id})
    else:
        return JsonResponse({'status': 'fail', 'message': 'No active users available'})

@csrf_protect
@login_required
def send_connection_request(request):
    if request.method == 'POST':
        # Trova un utente online non impegnato
        online_users = Profile.objects.filter(status='online', is_busy=False).exclude(user=request.user)
        if online_users.exists():
            target_profile = online_users.first()
            target_user = target_profile.user

            # Invia una notifica all'utente target
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'notifications_{target_user.id}',
                {
                    'type': 'send_notification',
                    'content': {
                        'type': 'connection_request',
                        'from_user': request.user.username,
                        'from_user_id': request.user.id,
                    }
                }
            )
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'message': 'Nessun utente online disponibile o tutti gli utenti sono impegnati.'})
    return JsonResponse({'success': False, 'message': 'Metodo non supportato.'})


@csrf_protect
@login_required
def accept_connection(request, from_user_id):
    if request.method == 'POST':
        from_user = User.objects.get(id=from_user_id)
        to_user = request.user

        # Verifica se l'utente che accetta è impegnato
        to_profile = Profile.objects.get(user=to_user)
        if to_profile.is_busy:
            return JsonResponse({'success': False, 'message': 'Sei già impegnato in una chat.'})

        # Verifica se l'utente che ha inviato la richiesta è impegnato
        from_profile = Profile.objects.get(user=from_user)
        if from_profile.is_busy:
            return JsonResponse({'success': False, 'message': f'{from_user.username} è già impegnato in una chat.'})

        # Imposta is_busy = True per entrambi gli utenti
        to_profile.is_busy = True
        to_profile.save()
        from_profile.is_busy = True
        from_profile.save()

        room_name = f'chat_{min(to_user.id, from_user_id)}_{max(to_user.id, from_user_id)}'

        # Invia una notifica all'altro utente che la connessione è stata accettata
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{from_user_id}',
            {
                'type': 'send_notification',
                'content': {
                    'type': 'connection_accepted',
                    'room_name': room_name,
                }
            }
        )
        return JsonResponse({'success': True, 'room_name': room_name})
    return JsonResponse({'success': False, 'message': 'Metodo non supportato.'})

@csrf_protect
@login_required
def reject_connection(request, from_user_id):
    if request.method == 'POST':
        # Invia una notifica all'utente che ha inviato la richiesta
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{from_user_id}',
            {
                'type': 'send_notification',
                'content': {
                    'type': 'connection_rejected',
                    'message': f"{request.user.username} ha rifiutato la tua richiesta di chat.",
                }
            }
        )
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'message': 'Metodo non supportato.'})


'''@csrf_exempt  # Se gestisci CSRF correttamente, puoi rimuovere questo decoratore
@login_required
def close_session(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        room_name = data.get('room_name')

        # Estrai gli ID degli utenti dalla room_name
        try:
            user_ids = room_name.replace('chat_', '').split('_')
            user_ids = [int(uid) for uid in user_ids]
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Room name non valida.'})

        # Verifica che l'utente corrente sia uno dei partecipanti
        if request.user.id not in user_ids:
            return JsonResponse({'success': False, 'message': 'Operazione non autorizzata.'}, status=403)

        # Imposta is_busy = False per entrambi gli utenti
        for uid in user_ids:
            user = User.objects.get(id=uid)
            profile = user.profile
            profile.is_busy = False
            profile.save()

            # Invia una notifica all'altro utente
            if user.id != request.user.id:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'notifications_{user.id}',
                    {
                        'type': 'send_notification',
                        'content': {
                            'type': 'session_closed',
                            'message': 'La sessione è stata chiusa dall\'altro utente.'
                        }
                    }
                )

        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'message': 'Metodo non supportato.'})'''

