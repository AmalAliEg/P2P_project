# p2p_trading/controllers/p2p_offer_controller.py
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from ..services.p2p_offer_service import P2POfferService
from ..serializers.p2p_offer_serilaizer import (
    P2POfferCreateSerializer,
    P2POfferListSerializer,
    P2POfferDetailSerializer,
    OfferStatusUpdateSerializer,
    P2POfferPublicSerializer
)

# ================ HELPER MACROS ================
from ..helpers import (
    success_response,
    handle_exception,
    extract_filters
)
# ================ CONTROLLER CLASS ================



class P2POfferController(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    #common object from the class, thus all function can use it
    service = P2POfferService()

    """*************************************************************************************************************
    /*	function name:		    create
    * 	function inputs:	    request from the front end 
    * 	function outputs:	
    * 	function description:	create new offer 
    *   call back:              create_offer(),  P2POfferCreateSerializer()
    * 	API format:             POST: /api/p2p/offers/
    */
    *************************************************************************************************************"""
    @handle_exception
    @transaction.atomic
    def create(self, request):

        #instance from the offer model
        offer = self.service.create_offer(user_id=request.user.id, data=request.data)
        #instance of the P2POfferCreateSerializer
        serializer = P2POfferCreateSerializer(offer)
        return success_response(serializer.data, status_code=status.HTTP_201_CREATED)

    """*************************************************************************************************************
    /*	function name:		list
    * 	function inputs:	request from the front end 
    * 	function outputs:	
    * 	function description:	list my offers of the user in the front end page according to filters 
                                ['status', 'type', 'asset_type', 'start_date', 'end_date']
    *   call back:              get_user_offers(),  get_payment_methods_for_offers()
    * 	API format:     GET: /api/p2p/offers/
                        GET: /api/p2p/offers/?status=active&type=buy
                        GET: /api/p2p/offers/?status=active&type=sell&asset_type=USDT
                        etc
    */
    *************************************************************************************************************"""
    @handle_exception
    def list(self, request):
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

    """*************************************************************************************************************
    /*	function name:		    retrieve
    * 	function inputs:	    request from the front end 
    * 	function outputs:	
    * 	function description:	in each reactangle in the front end it show the details of the offer 
    *   call back:              get_offer_detail(),  P2POfferDetailSerializer()
    * 	API format:             GET: /api/p2p/offers/{order_id}
    */
    *************************************************************************************************************"""
    @handle_exception
    def retrieve(self, request, pk=None):
        offer = self.service.get_offer_detail(user_id=request.user.id, offer_id=pk)
        serializer = P2POfferDetailSerializer(offer)
        return success_response(serializer.data)

    """*************************************************************************************************************
    /*	function name:		    update 
    * 	function inputs:	    request from the front end 
    * 	function outputs:	
    * 	function description:	update exist offer 
    *   call back:              update_offer(),  P2POfferDetailSerializer()
    * 	API format:             PUT: /api/p2p/offers/{order_id}
                                PATCH: /api/p2p/offers/
    */
    *************************************************************************************************************"""
    @handle_exception
    def update(self, request, pk=None):
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


    """*************************************************************************************************************
    /*	function name:		    destroy 
    * 	function inputs:	    request from the front end 
    * 	function outputs:	    n/a
    * 	function description:	DELETE exist offer 
    *   call back:              delete_offer()
    * 	API format:             DELETE: /api/p2p/offers/{order_id}
    */
    *************************************************************************************************************"""
    @handle_exception
    def destroy(self, request, pk=None):
        self.service.delete_offer(user_id=request.user.id, offer_id=pk)
        return success_response(message="Offer deleted successfully",
                                status_code=status.HTTP_204_NO_CONTENT)


    """*************************************************************************************************************
    /*	function name:		    public_offers 
    * 	function inputs:	    request from the front end 
    * 	function outputs:	    n/a
    * 	function description:	list all the public offers 
    *   call back:              get_public_offers(),P2POfferPublicSerializer()
    * 	API format:             GET: /api/p2p/offers//public_offers/
                                GET: /api/p2p/offers//public_offers/?trade_type='BUY'
                                GET: /api/p2p/offers//public_offers/?trade_type='BUY'&fiat_currency='EGP'
                                etc
    */
    *************************************************************************************************************"""
    @action(detail=False, methods=['get'])
    @handle_exception
    def public_offers(self, request):
        # apply filters from the front end
        filters = extract_filters(request.query_params,
                                  ['trade_type', 'crypto_currency', 'fiat_currency', 'payment_method'])

        offers = self.service.get_public_offers(filters=filters)
        serializer = P2POfferPublicSerializer(offers, many=True)

        return success_response(data=serializer.data, count=len(serializer.data))


