from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth import get_user_model
from dashboard.models import ChatMessage
from asgiref.sync import sync_to_async

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.room_group_name = f"chat_{self.user.id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"✅ WebSocket connected: {self.user.username}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"❌ WebSocket disconnected: {self.user.username}")

    async def receive(self, text_data):
        data = json.loads(text_data)

        sender = self.user
        receiver_id = data.get("receiver_id")
        message = data.get("message")

        print(f"📩 Received message: {message} from {sender} to {receiver_id}")

        try:
            receiver = await sync_to_async(User.objects.get)(id=receiver_id)

            chat_message = await sync_to_async(ChatMessage.objects.create)(
                sender=sender,
                receiver=receiver,
                message=message,
                is_read=False
            )

            await self.channel_layer.group_send(
                f"chat_{sender.id}",
                {
                    "type": "chat_message",
                    "sender": sender.username,
                    "message": message,
                    "timestamp": chat_message.timestamp.strftime("%H:%M"),
                    "is_read": chat_message.is_read,
                }
            )

            await self.channel_layer.group_send(
                f"chat_{receiver.id}",
                {
                    "type": "chat_message",
                    "sender": sender.username,
                    "message": message,
                    "timestamp": chat_message.timestamp.strftime("%H:%M"),
                    "is_read": chat_message.is_read,
                }
            )

        except User.DoesNotExist:
            print(f"❌ Receiver with ID {receiver_id} not found.")

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def mark_as_read(self, data):
        """This method will be used when the receiver opens the chat to mark messages as read."""
        receiver_id = data.get("receiver_id")
        messages = await sync_to_async(ChatMessage.objects.filter)(
            receiver_id=receiver_id,
            is_read=False
        )
        for message in messages:
            message.is_read = True
            message.save()

        await self.channel_layer.group_send(
            f"chat_{receiver_id}",
            {
                "type": "mark_read",
                "message": "All unread messages have been marked as read."
            }
        )
    
    async def mark_read(self, event):
        """Handles the frontend update when messages are marked as read."""
        await self.send(text_data=json.dumps({
            "type": "message_read_update",
            "message": event["message"]
        }))

