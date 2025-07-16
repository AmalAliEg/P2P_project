# p2p_trading/controllers/p2p_offer_controller.py

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
    service = P2POfferService()

    # 1. Create new offer
    @handle_exception
    def create(self, request):
        print(f"Request data: {request.data}")
        print(f"User ID: {request.user.id}")

        offer = self.service.create_offer(user_id=request.user.id, data=request.data)
        serializer = P2POfferCreateSerializer(offer)
        return success_response(serializer.data, status_code=status.HTTP_201_CREATED)

    # 2. List "My Offers"
    @handle_exception
    def list(self, request):
        # apply filters
        filters = extract_filters(request.query_params,
                                  ['status', 'type', 'asset_type', 'start_date', 'end_date'])
        # get the offers
        offers = self.service.get_user_offers(user_id=request.user.id, filters=filters)

        # get payment method details
        payment_details_map = self.service.get_payment_methods_for_offers(offers)

        # Serialize
        serializer = P2POfferListSerializer(
            offers, many=True,
            context={'payment_details_map': payment_details_map, 'request': request}
        )

        count = offers.count() if hasattr(offers, 'count') else len(offers)
        return success_response(data=serializer.data, count=count)

    # 3. Show offer details
    @handle_exception
    def retrieve(self, request, pk=None):
        offer = self.service.get_offer_detail(user_id=request.user.id, offer_id=pk)
        serializer = P2POfferDetailSerializer(offer)
        return success_response(serializer.data)

    # 4. Update offer
    @handle_exception
    def update(self, request, pk=None):
        #validate
        serializer = OfferStatusUpdateSerializer(data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)

        # update
        offer = self.service.update_offer(
            user_id=request.user.id,
            offer_id=pk,
            data=serializer.validated_data
        )

        # جلب تفاصيل طرق الدفع
        payment_details_map = self.service.get_payment_methods_for_single_offer(offer)

        # Response
        response_serializer = P2POfferListSerializer(
            offer, context={'payment_details_map': payment_details_map}
        )
        return success_response(response_serializer.data)

    # 5. Delete offer
    @handle_exception
    def destroy(self, request, pk=None):
        self.service.delete_offer(user_id=request.user.id, offer_id=pk)
        return success_response(message="Offer deleted successfully",
                                status_code=status.HTTP_204_NO_CONTENT)

    # 6. List public offers
    @action(detail=False, methods=['get'])
    @handle_exception
    def public_offers(self, request):
        filters = extract_filters(request.query_params,
                                  ['trade_type', 'crypto_currency', 'fiat_currency', 'payment_method'])

        offers = self.service.get_public_offers(filters=filters)
        serializer = P2POfferPublicSerializer(offers, many=True)

        return success_response(data=serializer.data, count=len(serializer.data))


