# p2p_trading/services/p2p_order_service.py

# ✨ الدمج: نستدعي خدمة الشات
# ... (imports أخرى)
from chat.repositories.api_chat_repository import ChatRepository


class ChatService:

    @staticmethod
    def get_room_history(room_id, limit=50):
        """get objects"""
        return ChatRepository.get_room_messages(room_id, limit)

    @staticmethod
    def get_user_rooms(user):
        """get objects"""
        return ChatRepository.get_user_rooms(user.id)


    @staticmethod
    def save_message(sender, room_id, content):
        """get objects"""
        return ChatRepository.save_message(
            sender_id=sender.id,
            room_id=room_id,
            content=content
        )

    def create_room_for_order(self, order_id, participants_ids):

        """

        إنشاء غرفة شات جديدة مرتبطة بطلب P2P وإضافة المشاركين.

        """

        # نستخدم repository لإنشاء الغرفة والمشاركين

        return ChatRepository.create_order_room(order_id, participants_ids)


