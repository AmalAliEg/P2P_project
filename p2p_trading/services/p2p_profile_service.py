# p2p_trading/services/p2p_profile_service.py

from django.db import transaction
from ..repositories.p2p_profile_repository import P2PProfileRepository
from ..helpers import validate_and_raise


class P2PProfileService:
    repo = P2PProfileRepository()

    @staticmethod
    def get_profile_overview(user_id):
        """
        function to handle and get all data of the profile overview
        args:
            user_id: user id
        return:
            profile_data: profile overview
        """
        #get the profile of the user or create one there no profile
        profile = P2PProfileService.repo.get_or_create_profile(user_id)
        #get the data from the main-dashboard
        user_data = P2PProfileService.repo.get_user_data(user_id) or {}
        #get the statistics of the user
        counts = P2PProfileService.repo.get_profile_counts(profile)

        #return the data in dict
        return {
            'profile': profile,
            'user_data': user_data,
            **counts
        }

    @staticmethod
    def update_nickname(user_id, new_nickname):
        """
        this function update the nickname of a user
        args:
            user_id: user id
            new_nickname: new nickname
        return:
            None
        """
        #validate if the nikname avail to be used
        validate_and_raise(
            P2PProfileService.repo.is_nickname_taken(new_nickname),
            "This nickname is already taken"
        )
        #get or create the profile
        profile = P2PProfileService.repo.get_or_create_profile(user_id)
        return P2PProfileService.repo.update_profile(profile, nickname=new_nickname)

    @staticmethod
    def get_payment_methods(user_id):
        """
        get the payment methods for a user
        args:
            user_id: user id
        return:
            payment_methods: payment methods"""
        #get or create the profile
        profile = P2PProfileService.repo.get_or_create_profile(user_id)
        return P2PProfileService.repo.get_payment_methods(profile)

    @staticmethod
    @transaction.atomic
    def add_payment_method(user_id, method_data):
        """
        add payment method
        args:
            user_id: user id
            method_data: payment method
        return:
            None
        """
        payment_method = P2PProfileService.repo.add_payment_method_to_main(
            user_id,
            method_data
        )
        return payment_method


    @staticmethod
    def update_payment_method( user_id, method_id, data):
        """
        update payment method
        args:
            user_id: user id
            method_id: payment method
            data: payment data
        return:
            None

        """
        profile = P2PProfileService.repo.get_or_create_profile(user_id)
        return P2PProfileService.repo.update_payment_method(method_id, profile, **data)

    @staticmethod
    def delete_payment_method( user_id, method_id):
        profile = P2PProfileService.repo.get_or_create_profile(user_id)
        return P2PProfileService.repo.delete_payment_method(method_id, profile)


