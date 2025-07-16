#chat/models.py

from django.db import models
#Create your models here.


class Room(models.Model):
    room_id=models.CharField(max_length=100,primary_key=True)
    created_at=models.DateTimeField(auto_now_add=True)
    # ✨ حقل جديد لربط الغرفة بالطلب في خدمة الـ P2P
    related_order_id = models.UUIDField(null=True, blank=True, unique=True)
    class Meta:
        app_label = 'chat'
        db_table ='room'

    def __str__(self):
        return self.room_id


class Participant(models.Model):
    room=models.ForeignKey(Room, on_delete=models.CASCADE, related_name='members' )
    #refrence for user id
    user_id=models.BigIntegerField(db_index=True)

    class Meta:
        app_label = 'chat'
        db_table = 'room_participants'
        unique_together = ['room', 'user_id']  #avoid repeation

    def __str__(self):
        return f"User {self.user_id} in {self.room.room_id}"


#one to many relation between the users and messages also one to many between the room and message
class Message (models.Model):
    id=models.BigAutoField(primary_key=True)

    #refrence for user id
    sender_id=models.BigIntegerField(db_index=True)
    room=models.ForeignKey(Room,on_delete=models.CASCADE,related_name='messages', db_index=True)
    content=models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read= models.BooleanField(default=False)
    class Meta:
        app_label = 'chat'
        db_table ='message'
        ordering =['timestamp']

    def __str__(self):
        return f"user {self.sender_id}: {self.content}"


