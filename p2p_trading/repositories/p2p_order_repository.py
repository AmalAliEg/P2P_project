# p2p_trading/repositories/p2p_order_repository.py

from django.db import transaction
from django.db.models.functions import Coalesce

from ..models.p2p_order_model import P2POrder
from ..models.p2p_offer_model import P2POffer
from ..constants.constant import OfferStatus, OrderStatus

from django.db.models import Count, Sum, Value, DecimalField
from django.utils import timezone
from datetime import timedelta

# ================ HELPER MACROS ================
from ..helpers import (ORDER_FILTER_MAP,
                       STATUS_TIME_FIELDS,
                       USER_FILTER,
                       get_or_403,
                       buy_filter,
                       sell_filter
                       )


# ================ REPOSITORY CLASS ================

class P2POrderRepository:

    @staticmethod
    def get_by_id(order_id):
        """
        get one order using the ID
        args:
            order_id: order ID
        returns:
            Order details

        """

        return get_or_403(
            P2POrder,
            "Order not found.",
            id=order_id,
            is_deleted=False
        )
        # print(f"Repository - get_by_id: order_id={order_id}")  # debugging
        # try:
        #     order = P2POrder.objects.select_related('offer').get(id=order_id, is_deleted=False)
        #     print(f"Found order in DB: {order}")  # debugging
        #     return order
        # except P2POrder.DoesNotExist:
        #     print(f"Order not found with ID: {order_id}")  # debugging
        #     raise NotFound("Order not found.")

    @staticmethod
    @transaction.atomic
    def create_order(offer, taker_id, order_data):
        """
        Create a new order and update the offer's available amount
        args:
            offer: P2POffer instance
            taker_id: ID of user accepting the offer
            order_data: Dictionary with order details
        returns:
            P2POrder: The created order instance

        """
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
        """
          get queryset for the orders that user is taker or maker
          args:
            user_id: ID of user
            filters: Filters to apply to the queryset
            status_list: List of statuses to filter the queryset
          returns:
            Queryset

        """
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
    def update_order_status(order, new_status):
        """
        update the order status and time
        args:

        order: P2POrder instance
        new_status: New order status

        returns:
        instance of order with updated status

        """
        print(f"Updating order {order.id} status from {order.status} to {new_status}")  # just for debugging


        order.status = new_status
        update_fields = ['status']

        # update time fields
        if new_status in STATUS_TIME_FIELDS:
            field_name, time_func = STATUS_TIME_FIELDS[new_status]
            setattr(order, field_name, time_func())
            update_fields.append(field_name)

        print(f"Update fields: {update_fields}")  # debugging

        #create the instance and update the status
        order.save(update_fields=update_fields)
        print(f"Order saved successfully. New status: {order.status}")  # debugging

        return order



    @staticmethod
    def get_pnl_statement_data(user_id, filters):
        """get the data for the profile and losing statements"""
        completed_orders = P2POrder.objects.select_related('offer').filter(
            USER_FILTER(user_id),
            status=OrderStatus.COMPLETED
        )
        completed_orders = completed_orders.only(
            'fiat_amount', 'crypto_amount', 'transaction_fee',
            'crypto_currency', 'maker_id', 'taker_id', 'trade_type'
        )

        # limited and filter to the last 90 days
        if not filters.get('date_from'):
            completed_orders = completed_orders.filter(
                created_at__gte=timezone.now() - timedelta(days=90)
            )

        # apply filters
        for key in ['coin', 'date_from', 'date_to']:
            if key in filters:
                completed_orders = ORDER_FILTER_MAP[key](completed_orders, filters.get(key))

        # collect the data
        pnl_data = completed_orders.values('crypto_currency').annotate(
            # عمليات الشراء
            buy_orders=Count('id', filter=buy_filter(user_id)),

            buy_total_fiat=Coalesce(Sum('fiat_amount',
                                    filter=buy_filter(user_id)),
                                    Value(0, output_field=DecimalField())),

            buy_total_crypto=Coalesce(Sum('crypto_amount',
                                    filter=buy_filter(user_id)),
                                    Value(0, output_field=DecimalField())),

            # ٍSell orders
            sell_orders=Count('id', filter=sell_filter(user_id)),
            sell_total_fiat=Coalesce(Sum('fiat_amount',
                                    filter=sell_filter(user_id)),
                                    Value(0, output_field=DecimalField())),

            sell_total_crypto=Coalesce(Sum('crypto_amount',
                                    filter=sell_filter(user_id)),
                                    Value(0, output_field=DecimalField())),

            # the transaction fees
            total_txn_fee=Coalesce(Sum('transaction_fee'),
                                   Value(0, output_field=DecimalField()))
        ).order_by('crypto_currency')

        # analysis of the data
        result_list = []
        for item in pnl_data:
            # calculate the mean values
            buy_total_fiat = item.get('buy_total_fiat') or 0
            buy_total_crypto = item.get('buy_total_crypto') or 0
            sell_total_fiat = item.get('sell_total_fiat') or 0
            sell_total_crypto = item.get('sell_total_crypto') or 0


            item['buy_total_fiat'] = buy_total_fiat
            item['buy_total_crypto'] = buy_total_crypto
            item['sell_total_fiat'] = sell_total_fiat
            item['sell_total_crypto'] = sell_total_crypto
            item['total_txn_fee'] = item.get('total_txn_fee') or 0

            item['buy_avg_price'] = buy_total_fiat / buy_total_crypto if buy_total_crypto else 0
            item['sell_avg_price'] = sell_total_fiat / sell_total_crypto if sell_total_crypto else 0
            item['coin'] = item.pop('crypto_currency')

            result_list.append(item)

        return result_list



    """it will be used for the chat"""
    '''@staticmethod
    def link_chat_room_to_order(order, room_id):
        """link the room id with the order"""
        """it will be used in future """
        order.chat_room_id = room_id
        order.save(update_fields=['chat_room_id'])
'''



