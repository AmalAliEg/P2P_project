# chat/controller/api_Chat.py
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework.viewsets import ViewSet
from rest_framework import status

from chat.services.api_chat_services  import ChatService
from chat.serializers.api_chat_serializers import (
    MessageSerializer,
    RoomSerializer,
    ParticipantSerializer
)



class api_Chat(ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """GET chat/api/chat/ -get the room info for speci"""
        rooms = ChatService.get_user_rooms(request.user)
        serializer = RoomSerializer(rooms, many=True)
        return api_response(data=serializer.data)

    def retrieve(self, request, pk=None):
        """GET chat/api/chat/{room_id}/ -history for specific room """
        try:
            limit = int(request.query_params.get('limit', 50))
            messages = ChatService.get_room_history(pk, limit)
            serializer = MessageSerializer(messages, many=True)

            return api_response(data={
                'room_id': pk,
                'messages': serializer.data,
                'count': len(messages)
            })
        except Exception as e:
            return api_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e)
            )

    def create(self, request):
        """POST chat/api/chat/ -create new msg"""

        try:
            room_id = request.data.get('room_id')
            content = request.data.get('content')

            #validate
            if not room_id or not content:
                return api_response(
                    data=None,
                    status=status.HTTP_400_BAD_REQUEST,
                    message="room_id and content are required"
                )

            # save msg in database
            message = ChatService.save_message(
                sender=request.user,
                room_id=room_id,
                content=content
            )

            serializer = MessageSerializer(message)
            return api_response(
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return api_response(
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e)
            )

