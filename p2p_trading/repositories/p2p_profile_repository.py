# p2p_trading/repositories/p2p_profile_repository.py
import time

from ..models import P2PProfile

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
            'payment_methods_count': profile.payment_methods.filter(is_active=True).count(),
            'feedback_count': profile.received_feedback.count(),
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
        # Generate default nickname
        #validate that user_id is str type
        if isinstance(user_id, str):
            #generate default nikename is "P2P-first 8 char in the user_id"
            default_nickname = f'P2P-{user_id[:8]}'
        else:
            #generate default nikename is "P2P-user- user_id"
            default_nickname = f'P2P-user-{user_id}'
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
            queryset=queryset.filter(is_active=True)
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
        method = get_or_403(PaymentMethods, id=method_id, user_id=profile.user_id)
        method.delete()
        return method







