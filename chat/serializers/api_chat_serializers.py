# chat/serializer/api__chat_serializers.py
from rest_framework import serializers
from chat.models import Message, Room, Participant

from django.contrib.auth import get_user_model

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    # add new fields manually
    sender_name = serializers.SerializerMethodField()
    sender_phone = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'content', 'sender_id', 'sender_name', 'sender_phone',
                  'timestamp', 'is_read']
        read_only_fields = ['-timestamp']

    def get_sender_name(self, obj):
        #  Service layer add the sender object into message
        if hasattr(obj, 'sender') and obj.sender:
            return obj.sender.username
        return 'Unknown'

    def get_sender_phone(self, obj):
        if hasattr(obj, 'sender') and obj.sender:
            return obj.sender.phone_number
        return 'Unknown'


class RoomSerializer(serializers.ModelSerializer):
    participants_count = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ['room_id', 'participants_count', 'created_at']
        read_only_fields = ['created_at']

    def get_participants_count(self, obj):
        # Participant model
        return Participant.objects.using('chat_database').filter(room=obj).count()

class ParticipantSerializer(serializers.ModelSerializer):
    """Participants Serializer"""
    user_name = serializers.SerializerMethodField()
    user_phone = serializers.SerializerMethodField()

    class Meta:
        model = Participant
        fields = ['user_id', 'user_name', 'user_phone']

    def get_user_name(self, obj):
        # user info from Service
        if hasattr(obj, 'user') and obj.user:
            return obj.user.username
        return f'User {obj.user_id}'

    def get_user_phone(self, obj):
        if hasattr(obj, 'user') and obj.user:
            return obj.user.phone_number
        return None


