# p2p_trading/controllers/p2p_offer_controller.py
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.decorators import action

from ..services.p2p_offer_service import P2POfferService
from ..serializers.p2p_offer_serilaizer import (
    P2POfferCreateSerializer,
    P2POfferListSerializer,
    P2POfferDetailSerializer,
    OfferStatusUpdateSerializer,
    P2POfferPublicSerializer
)

from ..decorator.swagger_decorator import swagger_serializer_mapping
# ================ HELPER MACROS ================
from ..helpers import (
    success_response,
    handle_exception,
    extract_filters
)


# ================ CONTROLLER CLASS ================

@swagger_serializer_mapping(
    create='P2POfferCreateSerializer',
    list='P2POfferListSerializer',
    retrieve='P2POfferDetailSerializer',
    update='OfferStatusUpdateSerializer',
    public_offers='P2POfferPublicSerializer'
)

class P2POfferController(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    #common object from the class, thus all function can use it
    service = P2POfferService()


    @handle_exception
    @transaction.atomic
    def create(self, request):
        """
        endpoint to create a new offer

        API format:
            POST: /api/p2p/offers/

        """

        #instance from the offer model
        offer = self.service.create_offer(user_id=request.user.id, data=request.data)
        #instance of the P2POfferCreateSerializer
        serializer = P2POfferCreateSerializer(offer)
        return success_response(serializer.data, status_code=status.HTTP_201_CREATED)

    @handle_exception
    def list(self, request):
        """
        list my offers of the user in the front end page according to filters
                                ['status', 'type', 'asset_type', 'start_date', 'end_date']
        API format:
            GET: /api/p2p/offers/
            GET: /api/p2p/offers/?status=active&type=buy
            GET: /api/p2p/offers/?status=active&type=sell&asset_type=USDT
            etc
        """
        # apply filters from the frontend url
        filters = extract_filters(request.query_params,
                                  ['status', 'type', 'asset_type', 'start_date', 'end_date'])
        # get the offers according to those filters
        offers = self.service.get_user_offers(user_id=request.user.id, filters=filters)

        # get payment method details
        payment_details_map = self.service.get_payment_methods_for_offers(offers)

        # Serialize
        serializer = P2POfferListSerializer(
            offers, many=True,
            context={'payment_details_map': payment_details_map, 'request': request}
        )
        #add the count of the offers of the user
        count = offers.count() if hasattr(offers, 'count') else len(offers)
        return success_response(data=serializer.data, count=count)

    @handle_exception
    def retrieve(self, request, pk=None):
        """
        endpoint responsible to get the data each offer's reactangle in the front end it show the details of the offer
        API format:
            GET: /api/p2p/offers/{order_id}
        """
        offer = self.service.get_offer_detail(user_id=request.user.id, offer_id=pk)
        serializer = P2POfferDetailSerializer(offer)
        return success_response(serializer.data)

    @handle_exception
    def update(self, request, pk=None):
        """
        endpoint to update all the fileds or speciic fields
        API format:
            PUT: /api/p2p/offers/{order_id}
            PATCH: /api/p2p/offers/
        """
        #pass the data to serializer
        serializer = OfferStatusUpdateSerializer(data=request.data,partial=True)
        #validate the data
        serializer.is_valid(raise_exception=True)

        # pass the validated data to the service layer
        offer = self.service.update_offer(
            user_id=request.user.id,
            offer_id=pk,
            data=serializer.validated_data
        )

        # get the details of the payment
        payment_details_map = self.service.get_payment_methods_for_single_offer(offer)

        # use the list serializer to show the details of updated offer
        response_serializer = P2POfferListSerializer(
            offer, context={'payment_details_map': payment_details_map}
        )
        return success_response(response_serializer.data)


    @handle_exception
    def destroy(self, request, pk=None):
        """API format:
            DELETE: /api/p2p/offers/{order_id}"""

        self.service.delete_offer(user_id=request.user.id, offer_id=pk)
        return success_response(message="Offer deleted successfully",
                                    status_code=status.HTTP_204_NO_CONTENT)


    @action(detail=False, methods=['get'],permission_classes=[AllowAny])
    @handle_exception
    def public_offers(self, request):
        """endpoint to	list all the public offers
        API format:
            GET: /api/p2p/offers//public_offers/
            GET: /api/p2p/offers//public_offers/?trade_type='BUY'
            GET: /api/p2p/offers//public_offers/?trade_type='BUY'&fiat_currency='EGP'
            etc
        """
        # apply filters from the front end
        filters = extract_filters(request.query_params,
                                  ['trade_type', 'crypto_currency', 'fiat_currency', 'payment_method'])

        offers = self.service.get_public_offers(filters=filters)
        serializer = P2POfferPublicSerializer(offers, many=True)

        return success_response(data=serializer.data, count=len(serializer.data))



