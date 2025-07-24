# p2p_trading/repositories/p2p_profile_repository.py
import time

from django.db.models import Q

from ..models import P2PProfile,Feedback,BlockedUser,P2POrder,Follow
#from ..models.p2p_order_model import P2POrder

from ..helpers import get_or_403, validate_and_raise
from MainDashboard.models import PaymentMethods,MainUser

#used to get the
GET_OR_CREATE_PROFILE = lambda user_id: P2PProfile.objects.get_or_create(
    user_id=user_id,
    defaults={'nickname': f'P2P-{user_id[:8]}' if isinstance(user_id, str) else f'P2P-user-{user_id}'}
)[0]


class P2PProfileRepository:

    @staticmethod
    def get_user_data(user_id):
        """
        function to get the data from the MainUser fron the main dashboard
        args:
            user_id (int): user id
        return:
            dict: user data
        """
        #filter the MainUser using the user_id and get first match and only the 'username' field
        return MainUser.objects.filter(id=user_id).values(
            'username'
        ).first()

    @staticmethod
    def is_nickname_taken(nickname):
        """
        validate the nickname availabilty .
        args:
            nickname (str): nickname
        return:
            bool
        """
        return P2PProfile.objects.filter(nickname=nickname).exists()

    @staticmethod
    def get_profile_counts(profile):
        """
        get the counts or metrix of the user
        args:
            profile (P2PProfile): user profile
        return:
            dict: counts
        """
        return {
            'payment_methods_count': PaymentMethods.objects.using('main_db').filter(
                user_id=profile.user_id
            ).count(),
            'feedback_count': Feedback.objects.filter(reviewee_id=profile.user_id).count(),
            'blocked_users_count': profile.blocking.count(),
            'followers_count': profile.followers.count(),
            'following_count': profile.following.count(),
        }

    @staticmethod
    def get_or_create_profile(user_id):
        """
        function to get or create the profile from id
        args:
        user_id: user id
        returns:
        profile: profile overview
        """

        user_id_int = int(user_id) if isinstance(user_id, str) else user_id

        default_nickname = f'P2P-user-{user_id_int}'
        #get or create the profile
        profile, created = P2PProfile.objects.get_or_create(
            user_id=user_id,
            defaults={'nickname': default_nickname}
        )

        return profile

    """*************************************************************************************************************
    /*	function name:		    get_profiles_by_user_ids
    * 	function inputs:	    user ids
    * 	function outputs:	    queryset of profiles that match te ids  
    * 	function description:	get profiles by user ids 
    *   call back:              n/a
    */
    *************************************************************************************************************"""
    @staticmethod
    def get_profiles_by_user_ids(user_ids):

        return P2PProfile.objects.filter(user_id__in=user_ids)

    @staticmethod
    def update_profile(profile, **kwargs):
        """
        update the profile
        args:
            profile (P2PProfile): user profile
        return:
            None

        """
        #loop over the fields
        for key, value in kwargs.items():
            setattr(profile, key, value)
        #retrun object from the profile with the edited fileds
        profile.save()
        return profile

    @staticmethod
    def get_payment_methods(profile, active_only=True):
        """
        get list of payment methods
        args:
            profile (P2PProfile): user profile
            active_only (bool):
        return:
            list: payment methods
        """
        queryset=PaymentMethods.objects.filter(user_id=profile.user_id)
        if active_only:
            queryset=queryset.filter(user__is_active=True)
        return queryset


    @staticmethod
    def add_payment_method_to_main(user_id, method_data):
        """
        add payment method data to main dashboard
        args:
            method_data (dict): payment method data
        return:
            None

        """

        # Access the payment method model direct
        payment_method = PaymentMethods.objects.create(
            user_id=user_id,
            payment_method_id=f"pm_{user_id}_{method_data['method_type']}_{int(time.time())}",
            type=method_data['method_type'],
            holder_name=method_data['account_name'],
            number=method_data.get('account_number', ''),
            primary=False
        )

        return payment_method

    @staticmethod
    def update_payment_method(method_id, profile, **kwargs):
        """
        update payment method
        args:
            method_id (str): payment method id
            profile (P2PProfile): user profile
        return:
            None
        """

        method = get_or_403(PaymentMethods, id=method_id, user_id=profile.user_id)
        #loop over updated fields
        for key, value in kwargs.items():
            setattr(method, key, value)
        #get the object of the payment method
        method.save()
        return method


    @staticmethod
    def validate_payment_methods_ownership(user_id, payment_ids):
        """check the ownership of the payment method by the user from the MainDashboard
        args:
            user_id: user id
            payment_ids (list): payment method id
        return:
            error_message or TRUE"""

        if not payment_ids:
            return True

        # get the payment method for the user from the payment-method model in the main- dashboard
        user_methods = PaymentMethods.objects.filter(
            user__id=user_id,
            id__in=payment_ids
        ).values_list('id', flat=True)

        # get all missing  IDs in set
        missing_ids = set(payment_ids) - set(user_methods)
        #raise error with the wrong id's
        validate_and_raise(
            bool(missing_ids),  # condition
            f'Payment methods {list(missing_ids)} do not exist or do not belong to you',
            'payment_method_ids'  # field name
        )

        return True

    @staticmethod
    def get_user_payment_methods_from_main(user_id):

        return PaymentMethods.objects.filter(
            user_id=user_id
        ).values('id', 'type', 'holder_name', 'number')

    @staticmethod
    def delete_payment_method(method_id, profile):
        """
        soft delete
        args:
            method_id (str): payment method id
            profile (P2PProfile): user profile
        return:
            None

        """
        method = get_or_403(PaymentMethods, id=method_id, user_id=profile.user_id)
        method.delete()
        return method


    @staticmethod
    def get_feedback(profile, feedback_type='received'):
        """
        get feedback

        args:
            profile (P2PProfile): user profile
            feedback_type (str):
        return:
            None

        """
        return getattr(profile, f'{feedback_type}_feedback').all()

    @staticmethod
    def add_feedback(reviewer_profile, reviewee_profile, order, is_positive, comment=''):
        """add feedback
        args:
            reviewer_profile (P2PProfile): user profile
            reviewee_profile (P2PProfile): user profile
            order (int):
            comment (str):
        return:
            None
        """
        return Feedback.objects.create(
            reviewer=reviewer_profile,
            reviewee=reviewee_profile,
            order=order,
            is_positive=is_positive,
            comment=comment
        )

    @staticmethod
    def validate_feedback_order(order_id,reviewer_id):
        """
        function to validate feedback order
        args:
            order_id (str): feedback order id
            reviewer_id (str): reviewer id
        return:
            None

        """

        order = get_or_403(P2POrder, id=order_id, error_msg="Order not found")

        #validate that order is complete
        validate_and_raise(
            order.status != 'COMPLETED',
            'Order must be completed to add feedback'
        )

        # validate reviewer is part of order
        validate_and_raise(
            reviewer_id not in [order.maker_id, order.taker_id],
            'You are not part of this order'
        )
        # validate feedback doesn't exist
        validate_and_raise(
            Feedback.objects.filter(reviewer__user_id=reviewer_id, order=order).exists(),
            'You have already submitted feedback for this order'
        )
        #get the reviewee id based on the reviewr taker /maker
        reviewee_id = order.taker_id if reviewer_id == order.maker_id else order.maker_id
        return {
            'valid': True,
            'order': order,
            'reviewee_id': reviewee_id
        }

    @staticmethod
    def update_feedback_stats(profile):
        """update feedback statistics"""
        from django.db.models import Count, Q

        stats = profile.received_feedback.aggregate(
            total=Count('id'),
            positive=Count('id', filter=Q(is_positive=True))
        )

        profile.total_feedback = stats['total'] or 0
        profile.positive_feedback = stats['positive'] or 0
        profile.feedback_rate = (profile.positive_feedback / profile.total_feedback * 100) if profile.total_feedback > 0 else 100.0
        profile.save(update_fields=['total_feedback', 'positive_feedback', 'feedback_rate'])

    @staticmethod
    def validate_user_in_order(user_id, order_id):
        """
        basic validation that user is part of order
        args:
            user_id (str): user id
            order_id (str): order id
        return:
            None
        """
        order = get_or_403(P2POrder, id=order_id, error_msg="Order not found")

        validate_and_raise(
            user_id not in [order.maker_id, order.taker_id],
            'You are not part of this order'
        )
        return order

    @staticmethod
    def get_my_feedback_for_order(user_id, order_id):
        """
        get my feedback for specific order
        args:
            user_id (str): user id
            order_id (str): order id
        return:
            None
        """
        return Feedback.objects.filter(
            reviewer__user_id=user_id,
            order_id=order_id
        ).first()

    @staticmethod
    def get_other_feedback_for_order(user_id, order_id):
        """
        get other party feedback for specific order
        args:
            user_id (str): user id
            order_id (str): order id
        return:
            None
        """

        return Feedback.objects.filter(
            order_id=order_id
        ).exclude(
            reviewer__user_id=user_id
        ).first()



    @staticmethod
    def is_blocked(profile1, profile2):
        """Check if there's a block relationship between two profiles"""
        return BlockedUser.objects.filter(
            Q(blocker=profile1, blocked=profile2) |
            Q(blocker=profile2, blocked=profile1)
        ).exists()


    @staticmethod
    def get_blocked_users(profile):
        """Get blocked users with related profile data"""
        return profile.blocking.select_related('blocked').all()

    @staticmethod
    def block_user(blocker_profile, blocked_profile):
        return BlockedUser.objects.get_or_create(
            blocker=blocker_profile,
            blocked=blocked_profile
        )[0]

    @staticmethod
    def unblock_user(blocker_profile, blocked_profile):
        BlockedUser.objects.filter(
            blocker=blocker_profile,
            blocked=blocked_profile
        ).delete()

    @staticmethod
    def get_followers(profile):
        """Get followers with related profile data"""
        return Follow.objects.filter(
            followed=profile
        ).select_related('follower').all()

    @staticmethod
    def get_following(profile):
        """Get following users with related profile data"""
        return Follow.objects.filter(
            follower=profile
        ).select_related('followed').all()

    @staticmethod
    def follow_user(follower_profile, followed_profile):
        """Create follow relationship"""
        return Follow.objects.get_or_create(
            follower=follower_profile,
            followed=followed_profile
        )[0]

    @staticmethod
    def unfollow_user(follower_profile, followed_profile):
        """Remove follow relationship"""
        Follow.objects.filter(
            follower=follower_profile,
            followed=followed_profile
        ).delete()







