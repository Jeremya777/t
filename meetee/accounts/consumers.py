# consumers.py

import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
        else:
            self.group_name = f'notifications_{self.user.id}'
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    # Questo consumer non riceve messaggi dal client
    async def receive(self, text_data):
        pass

    # Metodo per inviare notifiche
    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event['content']))

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Aggiungi l'utente al gruppo della chat
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        await self.set_user_busy_status(True)

    async def disconnect(self, close_code):
        # Rimuovi l'utente dal gruppo della chat
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        # Imposta is_busy = False quando l'utente lascia la chat
        await self.set_user_busy_status(False)

    # Ricevi messaggi dal WebSocket

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = str(data['type'])  # Default 'message'
        print(message_type)
        if message_type == 'chat_message':
            print(message_type)
            message = data['message']
            user = self.scope['user'].username

            # Invia il messaggio al gruppo della chat
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'user': user,
                }
            )
        elif message_type == 'close_session':
            print(message_type)
            # Imposta is_busy = False per l'utente corrente
            await self.set_user_busy_status(False)

            # Invia un messaggio all'altro utente per chiudere la sessione
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'session_closed',
                    'message': 'La sessione è stata chiusa dall\'altro utente.'

                }
            )
            # Chiudi la connessione
            await self.close()

    # Ricevi messaggi dal gruppo della chat
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'user': event['user'],
        }))
    @database_sync_to_async
    def set_user_busy_status(self, status):
        profile = self.scope['user'].profile
        profile.is_busy = status
        profile.save()

    async def session_closed(self, event):
        # Ricevi il messaggio di chiusura sessione
        await self.send(text_data=json.dumps({
            'type': 'session_closed',
            'message': event['message'],
        }))
        # Chiudi la connessione
        await self.close()