#app/channels/connection.py
import threading

from rest_framework_simplejwt.tokens import AccessToken, TokenError
from rest_framework.authtoken.models import Token
from socketio import Namespace
from socketio.exceptions import ConnectionRefusedError
from chat.services.api_chat_services import ChatService

class Connection(Namespace):
    def on_connect(self, sid, environ, auth):
        #debug
        if not auth or type(auth) is not dict or auth.get('token', None) is None or auth.get('token') == '':
            raise ConnectionRefusedError('Invalid Token')
        try:
            user = Token.objects.filter(key=auth.get('token')).first()
            user = user and user.user or None
            if user is None:
                user = User.objects.get(id=AccessToken(auth.get('token')).get('user_id'))
            self.save_session(sid, {'user': user})
            self.emit('message', {
                'data': f'{user.phone_number} Connected', 'count': 0}, room=sid)
        except (User.DoesNotExist, TokenError) as error:
            raise ConnectionRefusedError('Authentication Failed')

    #diconnect coz internet discon. , go out of the page 
    def on_disconnect(self, sid):
        if self.get_session(sid):
            #none means delete it 
            self.save_session(sid, None)
            #show msg is ofline 
        self.emit('message', {'data': f'sid:{sid} disconnected'})
    
    #user request logout
    def on_disconnect_request(self, sid):
        print(f'Request Client {sid} Disconnecting')
        self.disconnect(sid)
    
    
    #print on terminal , send echo for the msg by the user ----> debug 
    def on_my_event(self, sid, data):
        print(f'self:{self}, sid: {sid}, data:{data}')
        self.emit('message', {'data': data['data']}, room=sid)

    def on_my_broadcast_event(self, sid, message):
        session = self.get_session(sid)
        user = session.get('user')
        self.emit('message', {'data': f"{message['data']} From {user.phone_number}"})

    #enter chat room
    # app/channels/connection.py
    def on_join(self, sid, message):
        self.enter_room(sid, message['room'])
        self.emit('message', {'data': 'Entered room: ' + message['room']}, room=sid)
        

    #user close the room
    def on_leave(self, sid, message):
        self.leave_room(sid, message['room'])
        self.emit('message', {'data': 'Left room: ' + message['room']}, room=sid)
    
    #close the room itself
    def on_close_room(self, sid, message):
        self.emit('message', {'data': 'Room ' + message['room'] + ' is closing.'}, room=message['room'])
        self.close_room(message['room'])
    
    #send msg on chat room
    # app/channels/connection.py
    
    def on_my_room_event(self, sid, message):
                
        room    = message['room']
        content = message['data']
        session = self.get_session(sid)
        user    = session['user_obj']

        # 1) أولاً ابعتي الرسالة لباقي الأعضاء
        self.emit('message', {
            'sender_name': user.username,
            'data': content
        }, room=room, skip_sid=sid)

        # 2) بعدين خزنّيها في الـ database
        ChatService.save_message(
            sender=user,
            room_id=room,
            content=content
    )
            
            #self.emit('message', {'data': message['data']}, room=message['room'])

















        # session = self.get_session(sid)
        # user = session.get('user')
        # room_name = message['room']
        # try:
        #     room = Room.objects.get(room_id=room_name)
        #     Message.objects.create(
        #         sender=user,
        #         room=room,
        #         content=message['data']
        #     )
        # except Room.DoesNotExist:
        #     room = Room.objects.create(room_id=room_name)
        #     room.participants.add(user)
        #     Message.objects.create(
        #         sender=user,
        #         room=room,
        #         content=message['data']
        #     )
        # self.emit('message', {
        # 'data': message['data'],
        # 'sender': {
        #     'id': user.id,
        #     'phone_number': user.phone_number
        # },
        # 'timestamp': str(datetime.now())
        # }, room=room_name)
        
