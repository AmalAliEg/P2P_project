# p2p_trading/repositories/p2p_order_repository.py

from django.db import transaction
from rest_framework.exceptions import NotFound

from ..models.p2p_order_model import P2POrder
from ..models.p2p_offer_model import P2POffer
from ..constants.constant import  OfferStatus


# ================ HELPER MACROS ================
from ..helpers import (ORDER_FILTER_MAP,
                       STATUS_TIME_FIELDS,
                       USER_FILTER,
                       )


# ================ REPOSITORY CLASS ================

class P2POrderRepository:

    @staticmethod
    def get_by_id(order_id):
        """get one order using the ID"""
        print(f"Repository - get_by_id: order_id={order_id}")  # debugging
        try:
            order = P2POrder.objects.select_related('offer').get(id=order_id, is_deleted=False)
            print(f"Found order in DB: {order}")  # debugging
            return order
        except P2POrder.DoesNotExist:
            print(f"Order not found with ID: {order_id}")  # debugging
            raise NotFound("Order not found.")

    @staticmethod
    @transaction.atomic
    def create_order(offer, taker_id, order_data):
        # lock and validate the amount of the user
        offer_locked = P2POffer.objects.select_for_update().get(id=offer.id)

        if offer_locked.available_amount < order_data['crypto_amount']:
            raise ValueError("Insufficient available amount in offer")

        # create the order and update the offer
        order = P2POrder.objects.create(
            offer=offer_locked,
            maker_id=offer_locked.user_id,
            taker_id=taker_id,
            **order_data
        )

        # update the suffient amount
        offer_locked.available_amount -= order.crypto_amount
        if offer_locked.available_amount <= 0:
            offer_locked.status = OfferStatus.COMPLETED
        offer_locked.save()

        return order

    @staticmethod
    def get_orders_for_user(user_id, filters, status_list):
        """get list of specific user"""
        queryset = P2POrder.objects.filter(
            USER_FILTER(user_id),
            status__in=status_list
        ).select_related('offer').order_by('-created_at')

        # apply filters
        for key, filter_func in ORDER_FILTER_MAP.items():
            if key in filters:
                queryset = filter_func(queryset, filters.get(key))

        return queryset

    @staticmethod
    def update_order_status(order, new_status, user_id=None):
        """update the order status and time"""
        print(f"Updating order {order.id} status from {order.status} to {new_status}")  # just for debugging

        order.status = new_status
        update_fields = ['status']

        # update time
        if new_status in STATUS_TIME_FIELDS:
            field_name, time_func = STATUS_TIME_FIELDS[new_status]
            setattr(order, field_name, time_func())
            update_fields.append(field_name)

        print(f"Update fields: {update_fields}")  # debugging

        try:
            order.save(update_fields=update_fields)
            print(f"Order saved successfully. New status: {order.status}")  # debugging
        except Exception as e:
            print(f"Error saving order: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

        return order

    @staticmethod
    def link_chat_room_to_order(order, room_id):
        """link the room id with the order"""
        """it will be used in future """
        order.chat_room_id = room_id
        order.save(update_fields=['chat_room_id'])




