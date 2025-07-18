# p2p_trading/controllers/p2p_profile_controller.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from ..services.p2p_profile_service import P2PProfileService

from ..serializers.p2p_profile_serializers import (
    P2PProfileOverviewSerializer, P2PProfileUpdateSerializer,
    PaymentMethodCreateSerializer,
     MainPaymentMethodSerializer
)
from ..helpers import handle_exception,success_response


class P2PProfileController(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    service = P2PProfileService()

    @handle_exception
    def retrieve(self, request, pk=None):
        """
        this end point handle creation of the profile
        API format:
            GET /api/p2p/profiles/{user_id}/
        """
        #if the id related to another profile get that profile
        #if the is null or {current_profile}, use the current id
        user_id = pk or request.user.id
        #get the dic of the profile data
        profile_data = self.service.get_profile_overview(user_id)

        serializer = P2PProfileOverviewSerializer(
            profile_data['profile'],
            context={'user_data': profile_data['user_data']}
        )

        # get serialized data
        data = serializer.data
        #add addition statistics data
        data.update({
            'payment_methods_count': profile_data['payment_methods_count'],
            'feedback_count': profile_data['feedback_count'],
            'blocked_users_count': profile_data['blocked_users_count'],
            'followers_count': profile_data['followers_count'],
            'following_count': profile_data['following_count'],
        })

        return success_response(data)

    @action(detail=False, methods=['get'])
    @handle_exception
    def current_profile(self, request):
        """
        this end point just call the retrieve
        API format:
            GET /api/p2p/profiles/current_profile/
        """
        return self.retrieve(request, pk=request.user.id)

    @handle_exception
    def update(self, request, pk=None):
        """
        this end point handle update of the profile
        API format:
            PUT /api/p2p/profiles/current_profile/
        """
        serializer = P2PProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        #validate that the user trying to update the nikename
        if 'nickname' in serializer.validated_data:
            #update the nikename
            self.service.update_nickname(
                request.user.id,
                serializer.validated_data['nickname']
            )
        return success_response({"message": "Profile updated successfully"})

    # ================ Payment Methods ================

    @action(detail=False, methods=['get'], url_path='payment-methods')
    @handle_exception
    def list_payment_methods(self, request):
        """
        list the user payment methods
        API format:
            GET /api/p2p/profiles/payment-methods/"""
        methods = self.service.get_payment_methods(request.user.id)
        serializer = MainPaymentMethodSerializer(methods, many=True)
        return success_response(serializer.data)

    @action(detail=False, methods=['post'], url_path='payment-methods/add')
    @handle_exception
    def add_payment_method(self, request):
        """
        to add a new payment method when the user at p2p-app
        API format:
            POST /api/p2p/profiles/payment-methods/add/
        """
        serializer = PaymentMethodCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        method = self.service.add_payment_method(
            request.user.id,
            serializer.validated_data
        )

        return success_response(
            MainPaymentMethodSerializer(method).data,
            message="Payment method added successfully",
            status_code=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['patch'], url_path='payment-methods/(?P<method_id>\d+)/update')
    @handle_exception
    def update_payment_method(self, request, method_id=None):
        """
        this endpoint edit and update the payment method
        API format:
            PATCH /api/p2p/profiles/payment-methods/?payment_method_id=''/update/

        """
        method = self.service.update_payment_method(
            request.user.id,
            method_id,
            request.data
        )

        return success_response(
            MainPaymentMethodSerializer(method).data,
            message="Payment method updated successfully"
        )

    @handle_exception
    def destroy(self, request, method_id=None):
        """
        delete the payment method
        API format:
        DELETE /api/p2p/profiles/payment-methods/{id}

        """
        self.service.delete_payment_method(request.user.id, method_id)
        return success_response(message="Payment method deleted successfully")





