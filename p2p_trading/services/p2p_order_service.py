# p2p_trading/services/p2p_order_service.py

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from ..constants.constant import OrderStatus, COMPLETED_STATUSES, PROCESSING_STATUSES
from ..repositories.p2p_offer_repository import P2POfferRepository
from ..repositories.p2p_order_repository import P2POrderRepository
from ..serializers.p2p_order_serializer import P2POrderCreateSerializer
from ..services.p2p_wallet_service import WalletService


# ================ HELPER MACROS ================

from ..helpers import (
    validate_and_raise,
    GET_TAKER_TYPE,
    PAYMENT_DEADLINE,
    GET_BUYER_ID,

)

# ================SERVICE CLASS ================

# Repository mapping
REPO = {'offer': P2POfferRepository, 'order': P2POrderRepository}

class P2POrderService:

    @staticmethod
    @transaction.atomic
    def create_order_from_offer(taker_id, data):
        """
        Create a new P2P order from an existing offer

        args:
            taker_id (int): ID of the user accepting the offer
            data (dict): Request data

        returns:
            P2POrder: The created order instance with locked funds
        """
        # validate the data
        serializer = P2POrderCreateSerializer(data=data)
        validate_and_raise(not serializer.is_valid(), serializer.errors)

        # get the instance of offer
        offer = REPO['offer'].get_by_id_and_owner(data['offer_id'],taker_id)

        fiat_amount = serializer.validated_data['fiat_amount']
        crypto_amount = fiat_amount / offer.price

        # validate the data before creation by adding all the validations in list
        validations = [
            (offer.status != 'ACTIVE', "This offer is not active"),
            (offer.user_id == taker_id, "You cannot take your own offer"),
            (fiat_amount < offer.min_order_limit, f"Minimum order is {offer.min_order_limit} {offer.fiat_currency}"),
            (fiat_amount > offer.max_order_limit, f"Maximum order is {offer.max_order_limit} {offer.fiat_currency}"),
            (crypto_amount > offer.available_amount, "Insufficient available amount")
        ]
        #loop over the validations list
        for condition, error in validations:
            validate_and_raise(condition, error)

        # passed the validation success
        order_data = {
            'trade_type': GET_TAKER_TYPE(offer.trade_type),
            'crypto_currency': offer.crypto_currency,
            'fiat_currency': offer.fiat_currency,
            'price': offer.price,
            'crypto_amount': crypto_amount,
            'fiat_amount': fiat_amount,
            'payment_time_limit': PAYMENT_DEADLINE(offer.payment_time_limit_minutes),
            'status': OrderStatus.UNPAID
        }
        order = REPO['order'].create_order(offer, taker_id, order_data)
        # lock the crypto-escrow concept began
        try:
            WalletService.lock_funds_for_order(order)
        except ValueError as e:
            order.delete()
            raise ValidationError(f"Failed to lock funds: {str(e)}")

        return order

    @staticmethod
    def get_processing_orders(user_id, filters):
        """
        list the processing orders for that user
        args:
            user_id (int): ID of the user
            filters (dict): Filters data
        returns:
            list: List of processing orders
        """
        return REPO['order'].get_orders_for_user(user_id, filters, PROCESSING_STATUSES)

    @staticmethod
    def get_historical_orders(user_id, filters):
        """
        get the canceled or the completed orders for the user
        args:
            user_id (int): ID of the user
            filters (dict): Filters data
        returns:
            list: List of canceled or completed orders
        """

        return REPO['order'].get_orders_for_user(user_id, filters, COMPLETED_STATUSES)

    @staticmethod
    def mark_order_as_paid(user_id, order_id):
        """mark-as-paid , it should be done by the buyer
        args:
            user_id (int): ID of the user
            order_id (int): ID of the order
        returns:
            bool: True if marked as paid

        """
        print(f"Service - mark_as_paid: user_id={user_id}, order_id={order_id}")  # debugging

        order = REPO['order'].get_by_id(order_id)
        print(f"Found order: {order.id}, taker_id: {order.taker_id}, status: {order.status}")  # debugging

        # validate that the user is seller
        validate_and_raise(
            GET_BUYER_ID(order) != user_id,
            "Only buyer can mark order as paid"
        )

        #validate that the order status is paid
        validate_and_raise(
            order.status != OrderStatus.UNPAID,
            "Order is not in unpaid status",
            field='status'
        )

        #validate the time
        validate_and_raise(
            timezone.now() > order.payment_time_limit,
            "Payment time has expired",
            field='payment_time'
        )

        print(f"About to update order status to PAID")  # just for debugging
        #update the status of the  order
        updated_order = REPO['order'].update_order_status(order, OrderStatus.PAID)
        print(f"Order updated successfully: {updated_order.status}")  # just for debugging
        return updated_order



    @staticmethod
    def confirm_payment_received(user_id, order_id):
        """
        confirm receive money, it should be done by the seller
        args:
            user_id (int): ID of the user
            order_id (int): ID of the order
        returns:
            bool: True if confirmed, else False

        """
        order = REPO['order'].get_by_id(order_id)

        # validate if user is the buyer
        validate_and_raise(
            GET_BUYER_ID(order) != user_id,
            "Only seller can confirm payment"
        )
        #validate that the order status is unpaid
        validate_and_raise(
            order.status != OrderStatus.PAID,
            "Order is not marked as paid",
            field='status'
        )

        # update the status and release the crypto
        order = REPO['order'].update_order_status(order, OrderStatus.COMPLETED)
        WalletService.release_funds_to_buyer(order)
        return order

    @staticmethod
    def cancel_order(user_id, order_id):
        """this function handle the logic to cancel the order
        args:
            user_id (int): ID of the user
            order_id (int): ID of the order
        returns:
            bool: True if canceled, else False
        """
        order = REPO['order'].get_by_id(order_id)

        # validation
        validate_and_raise(
            order.maker_id != user_id,
            "You are not part of this order"
        )

        validate_and_raise(
            order.status in COMPLETED_STATUSES,
            "Cannot cancel this order"
        )

        #use it to make sure that below logic dealed as one block
        with transaction.atomic():
            # update status to CANCEL
            order = REPO['order'].update_order_status(order, OrderStatus.CANCELLED)

            # edit the avail. amount of the offer back to the offer again
            offer = order.offer
            offer.available_amount += order.crypto_amount
            #if the status of the offer was completed, return it back to active
            if offer.status == 'COMPLETED':
                offer.status = 'ACTIVE'
            offer.save()

        # release back the crypto to the seller
        WalletService.cancel_order_and_unlock_funds(order)
        return order


    @staticmethod
    def get_order_detail(user_id, order_id):
        """
        get the order detail for the user
        args:
            user_id (int): ID of the user
            order_id (int): ID of the order
        returns:
            dict: Order details
        """
        order = REPO['order'].get_by_id(order_id)
        #validaion if the user is taker or maker
        if order.maker_id != user_id and order.taker_id != user_id:
            raise PermissionDenied("You don't have permission to view this order")

        return order
