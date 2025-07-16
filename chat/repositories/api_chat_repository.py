##chat/repository/api_ChatRepository.py
from django.db import transaction

from chat.models import Message,Room,Participant
from django.core.exceptions import ObjectDoesNotExist
#psudo code
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatRepository:


    @staticmethod
    def get_room_messages(room_id, limit=50):
        """get the last msg with the sender name """
        try:
            messages = Message.objects.using('chat_database').filter(
                room__room_id=room_id
            ).order_by('timestamp')[:limit]

            #get the sender_ids
            sender_ids = [msg.sender_id for msg in messages]

            # get the info of the user fromـ default database
            users = User.objects.filter(id__in=sender_ids)
            users_dict = {user.id: user for user in users}

            # merge the user inf. with the msg
            messages_with_users = []
            for msg in messages:
                msg.sender = users_dict.get(msg.sender_id)
                messages_with_users.append(msg)

            return messages_with_users

        except Exception as e:
            print(f"Error getting messages: {e}")
            return []


    @staticmethod
    def get_user_rooms(user_id):
        """get the rooms for specific user"""
        room_ids = Participant.objects.using('chat_database').filter(
            user_id=user_id
        ).values_list('room_id', flat=True)

        return Room.objects.using('chat_database').filter(
            room_id__in=room_ids
        ).order_by('-created_at')



    @staticmethod
    def save_message(sender_id, room_id, content):
        """save in database"""
        try:
            room = Room.objects.using('chat_database').get(room_id=room_id)
            message = Message.objects.using('chat_database').create(
                room=room,
                sender_id=sender_id,
                content=content
            )

            # get the user details
            try:
                sender = User.objects.get(id=sender_id)
                message.sender = sender
            except User.DoesNotExist:
                pass

            return message
        except Exception as e:
            print(f"Error saving message: {e}")
            raise e

    @staticmethod
    @transaction.atomic
    def create_order_room(order_id, participants_ids):
        # 1. إنشاء الغرفة وربطها بالطلب
        room = Room.objects.create(related_order_id=order_id)

        # 2. إضافة المشاركين (البائع والمشتري) إلى الغرفة
        for user_id in participants_ids:
            Participant.objects.create(room=room, user_id=user_id)

        return room