# p2p_trading/repositories/p2p_profile_repository.py
import time

from ..models import P2PProfile

from ..helpers import get_or_404, validate_and_raise
from MainDashboard.models import PaymentMethods,MainUser

# Macros
GET_OR_CREATE_PROFILE = lambda user_id: P2PProfile.objects.get_or_create(
    user_id=user_id,
    defaults={'nickname': f'P2P-{user_id[:8]}' if isinstance(user_id, str) else f'P2P-user-{user_id}'}
)[0]


class P2PProfileRepository:

    @staticmethod
    def get_user_data(user_id):
        """get the data from the MainUser"""
        return MainUser.objects.filter(id=user_id).values(
            'username'
        ).first()

    @staticmethod
    def is_nickname_taken(nickname):
        """validate the nickname avai. """
        return P2PProfile.objects.filter(nickname=nickname).exists()

    @staticmethod
    def get_profile_counts(profile):
        """metrix of the user"""
        return {
            'payment_methods_count': profile.payment_methods.filter(is_active=True).count(),
            'feedback_count': profile.received_feedback.count(),
            'blocked_users_count': profile.blocking.count(),
            'followers_count': profile.followers.count(),
            'following_count': profile.following.count(),
        }

    @staticmethod
    def get_or_create_profile(user_id):
        """get or create the profile from id """
        return GET_OR_CREATE_PROFILE(user_id)

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
        """update the profile"""
        for key, value in kwargs.items():
            setattr(profile, key, value)
        profile.save()
        return profile

    @staticmethod
    def get_payment_methods(profile, active_only=True):
        """get list of payment methods"""

        return PaymentMethods.objects.filter(user_id=profile.user_id)


    @staticmethod
    def add_payment_method_to_main(user_id, method_data):

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
        """update payment method"""
        method = get_or_404(PaymentMethods, id=method_id, user_id=profile.user_id)
        for key, value in kwargs.items():
            setattr(method, key, value)
        method.save()
        return method

    """*************************************************************************************************************
    /*	function name:		    validate_payment_methods_ownership
    * 	function inputs:	    user id from the payment_method_ids the attri in the offer model
    * 	function outputs:	    error_message or TRUE
    * 	function description:	check the ownership of the payment method by the user from the MainDashboard
    *   call back:              ValidationError() from rest.framework library
    */
    *************************************************************************************************************"""
    @staticmethod
    def validate_payment_methods_ownership(user_id, payment_ids):

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
        """ (soft delete)"""
        method = get_or_404(PaymentMethods, id=method_id, user_id=profile.user_id)
        method.delete()
        return method







