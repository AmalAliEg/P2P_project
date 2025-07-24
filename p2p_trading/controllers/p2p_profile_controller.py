# p2p_trading/controllers/p2p_profile_controller.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from ..services.p2p_profile_service import P2PProfileService

from ..serializers.p2p_profile_serializer import (
    P2PProfileOverviewSerializer, P2PProfileUpdateSerializer,
    PaymentMethodCreateSerializer,
    PaymentMethodSerializer,FeedbackCreateSerializer, FeedbackSerializer,BlockUserSerializer
)
from ..helpers import handle_exception,success_response

from ..decorator.swagger_decorator import swagger_serializer_mapping

@swagger_serializer_mapping(
    retrieve='P2PProfileOverviewSerializer',
    current_profile='P2PProfileOverviewSerializer',
    update='P2PProfileUpdateSerializer',
    list_payment_methods='PaymentMethodSerializer',
    add_payment_method='PaymentMethodCreateSerializer',
    update_payment_method='PaymentMethodSerializer',
    list_feedback='FeedbackSerializer',
    add_feedback='FeedbackCreateSerializer'
)

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
        #if the pk is null or {current_profile}, use the current id
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
        serializer = PaymentMethodSerializer(methods, many=True)
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
            PaymentMethodSerializer(method).data,
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
        serializer = PaymentMethodSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        method = self.service.update_payment_method(
            request.user.id,
            method_id,
            serializer.validated_data
        )

        return success_response(
            PaymentMethodSerializer(method).data,
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




    # ================ Feedback ================

    @action(detail=True, methods=['get'], url_path='feedback')
    @handle_exception
    def list_feedback(self, request,pk=None):
        """
        list all the feedback for the user
        API format:
            GET /api/p2p/profiles/{user_id}/feedback/
        """
        feedback = self.service.get_user_feedback(pk)
        serializer = FeedbackSerializer(feedback, many=True)
        return success_response(serializer.data)

    @action(detail=False, methods=['post'], url_path='feedback/add')
    @handle_exception
    def add_feedback(self, request):
        """
        add feedback to the counterparty after the order is completed
        API format:

            POST /api/p2p/profiles/feedback/add/
        """
        serializer = FeedbackCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        feedback = self.service.add_feedback(
            request.user.id,
            **serializer.validated_data
        )

        return success_response(
            FeedbackSerializer(feedback).data,
            message="Feedback added successfully",
            status_code=status.HTTP_201_CREATED
        )


    @action(detail=False, methods=['get'], url_path='order-feedback/(?P<order_id>[^/.]+)')
    @handle_exception
    def order_feedback(self, request, order_id=None):
        """
        show the feedback within specific order
        API format:

            GET /api/p2p/profiles/order-feedback/{order_id}/

        """
        feedback_data = self.service.get_order_feedback(request.user.id, order_id)
        return success_response(feedback_data)



    # ================ Blocked Users ================

    @action(detail=False, methods=['get'], url_path='blocked-users')
    @handle_exception
    def list_blocked_users(self, request):
        """
        GET /api/p2p/profiles/blocked-users/
        """
        blocked_users = self.service.get_blocked_users(request.user.id)
        data = [
            {
                'user_id': blocked.blocked.user_id,
                'nickname': blocked.blocked.nickname,
                'blocked_at': blocked.created_at
            }
            for blocked in blocked_users
        ]
        return success_response(data)

    @action(detail=False, methods=['post'], url_path='block-user')
    @handle_exception
    def block_user(self, request):
        """
        POST /api/p2p/profiles/block-user/
        """
        serializer = BlockUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.service.block_user(
            request.user.id,
            serializer.validated_data['user_id']
        )

        return success_response(message="User blocked successfully")

    @action(detail=False, methods=['post'], url_path='unblock-user')
    @handle_exception
    def unblock_user(self, request):
        """
        POST /api/p2p/profiles/unblock-user/
        """
        serializer = BlockUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.service.unblock_user(
            request.user.id,
            serializer.validated_data['user_id']
        )

        return success_response(message="User unblocked successfully")

    # ================ Follows ================

    @action(detail=True, methods=['get'], url_path='followers')
    @handle_exception
    def list_followers(self, request, pk=None):
        """
        GET /api/p2p/profiles/{user_id}/followers/
        """
        followers = self.service.get_followers(pk)
        data = [
            {
                'user_id': follow.follower.user_id,
                'nickname': follow.follower.nickname,
                'followed_at': follow.created_at
            }
            for follow in followers
        ]
        return success_response(data)

    @action(detail=True, methods=['get'], url_path='following')
    @handle_exception
    def list_following(self, request, pk=None):
        """
        GET /api/p2p/profiles/{user_id}/following/
        """
        following = self.service.get_following(pk)
        data = [
            {
                'user_id': follow.followed.user_id,
                'nickname': follow.followed.nickname,
                'followed_at': follow.created_at
            }
            for follow in following
        ]
        return success_response(data)

    @action(detail=False, methods=['post'], url_path='follow')
    @handle_exception
    def follow_user(self, request):
        """
        POST /api/p2p/profiles/follow/
        """
        serializer = BlockUserSerializer(data=request.data)  # نفس الـ serializer
        serializer.is_valid(raise_exception=True)

        self.service.follow_user(
            request.user.id,
            serializer.validated_data['user_id']
        )

        return success_response(message="User followed successfully")

    @action(detail=False, methods=['post'], url_path='unfollow')
    @handle_exception
    def unfollow_user(self, request):
        """
        POST /api/p2p/profiles/unfollow/
        """
        serializer = BlockUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.service.unfollow_user(
            request.user.id,
            serializer.validated_data['user_id']
        )

        return success_response(message="User unfollowed successfully")


