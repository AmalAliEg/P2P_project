# p2p_trading/controllers/p2p_order_controller.py

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from ..services.p2p_order_service import P2POrderService
from ..serializers.p2p_order_serializer import P2POrderListSerializer

from ..decorator.swagger_decorator import swagger_serializer_mapping

# ================ HELPER MACROS ================

from ..helpers import (
    success_response,
    handle_exception,
    GET_CONTEXT,
    ORDER_RESPONSE,
)


@swagger_serializer_mapping(
    create='P2POrderCreateSerializer',
    list='P2POrderListSerializer',
    retrieve='P2POrderListSerializer',
    processing='P2POrderListSerializer',
    records='P2POrderListSerializer'
)

# ================ CONTROLLER CLASS ================
class P2POrderController(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    service = P2POrderService()



    @handle_exception
    def create(self, request):
        """
            create a new order from offer

        	API format:
                    POST /api/p2p/orders/
        """
        order = self.service.create_order_from_offer(
            taker_id=request.user.id,
            data=request.data
        )
        serializer = P2POrderListSerializer(order, context=GET_CONTEXT(self))
        return success_response(serializer.data, "Order created successfully", status_code=status.HTTP_201_CREATED)

    @handle_exception
    def list(self, request):
        """
            list all the orders of the user applying the filters

        	API format:
                GET /api/p2p/orders/
                GET /api/p2p/orders/?coin=BTC
                GET /api/p2p/orders/?order_type=buy
                GET /api/p2p/orders/?currency=USD
                etc
        """
        #get the processing orders + historical data +filters from the url
        all_orders = list(self.service.get_processing_orders(request.user.id, request.query_params)) + \
                     list(self.service.get_historical_orders(request.user.id, request.query_params))

        # order according ti date desce.
        all_orders.sort(key=lambda x: x.created_at, reverse=True)

        serializer = P2POrderListSerializer(all_orders, many=True, context=GET_CONTEXT(self))
        return success_response(serializer.data, count=len(all_orders))

    @handle_exception
    def retrieve(self, request, pk=None):
        """
        get the details of specific order
        API format:
            GET /api/p2p/orders/{id}/"""
        order = self.service.get_order_detail(request.user.id, pk)
        serializer = P2POrderListSerializer(order, context=GET_CONTEXT(self))
        return success_response(serializer.data)


    @action(detail=False, methods=['get'])
    @handle_exception
    def processing(self, request):
        """
        get the processing orders only

        API format:
            GET /api/p2p/orders/processing/
            GET /api/p2p/orders/processing/?coin=BTC
            etc
                """
        orders = self.service.get_processing_orders(request.user.id, request.query_params)
        serializer = P2POrderListSerializer(orders, many=True, context=GET_CONTEXT(self))
        return success_response(serializer.data, count=orders.count() if hasattr(orders, 'count') else len(orders))

    @action(detail=False, methods=['get'])
    @handle_exception

    def records(self, request):
        """
          list all the orders that created by the user

          API format:
                  GET /api/p2p/orders/records/
                  GET /api/p2p/orders/records/?coin=BTC
                  etc
    """
        orders = self.service.get_historical_orders(request.user.id, request.query_params)
        serializer = P2POrderListSerializer(orders, many=True, context=GET_CONTEXT(self))
        return success_response(serializer.data, count=orders.count() if hasattr(orders, 'count') else len(orders))


    @action(detail=True, methods=['post'], url_path='mark-as-paid')
    @handle_exception
    def mark_as_paid(self, request, pk=None):
        """
        regard the fiat, the buyer should mark as paid
        API format:
            POST /api/p2p/orders/mark-as-paid/
        """
        print(f"Mark as paid - Order ID: {pk}, User ID: {request.user.id}")  # debugging
        order = self.service.mark_order_as_paid(request.user.id, pk)
        return success_response(
            ORDER_RESPONSE(order, f"Order {order.order_number} marked as paid."),
            status_code=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='confirm-payment')
    @handle_exception
    def confirm_payment_received(self, request, pk=None):
        """
        regard the fiat, the seller should confirm receiving the payment
        API format:
            POST /api/p2p/orders/{order_id}/confirm-payment/
            """
        order = self.service.confirm_payment_received(request.user.id, pk)
        return success_response(
            ORDER_RESPONSE(order, "Order completed and funds released."),
            status_code=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    @handle_exception
    def cancel(self, request, pk=None):
        """
        in case the order canceled this end point handle the cancelation
        Api format:

            POST /api/p2p/orders/{id}/cancel/

            """
        order = self.service.cancel_order(request.user.id, pk)
        return success_response(
            ORDER_RESPONSE(order, "Order cancelled successfully."),
            status_code=status.HTTP_200_OK
        )







