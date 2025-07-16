# p2p_trading/services/p2p_profile_service.py

from django.db import transaction
from ..repositories.p2p_profile_repository import P2PProfileRepository
from ..helpers import validate_and_raise


class P2PProfileService:
    repo = P2PProfileRepository()

    @staticmethod
    def get_profile_overview(user_id):
        """get all data of the profile overview"""
        profile = P2PProfileService.repo.get_or_create_profile(user_id)
        user_data = P2PProfileService.repo.get_user_data(user_id) or {}
        counts = P2PProfileService.repo.get_profile_counts(profile)

        return {
            'profile': profile,
            'user_data': user_data,
            **counts
        }

    @staticmethod
    def update_nickname(user_id, new_nickname):
        """update the nickname of a user"""
        validate_and_raise(
            P2PProfileService.repo.is_nickname_taken(new_nickname),
            "This nickname is already taken"
        )
        profile = P2PProfileService.repo.get_or_create_profile(user_id)
        return P2PProfileService.repo.update_profile(profile, nickname=new_nickname)

    @staticmethod
    def get_payment_methods(user_id):
        """get the payment methods for a user"""
        profile = P2PProfileService.repo.get_or_create_profile(user_id)
        return P2PProfileService.repo.get_payment_methods(profile)

    @staticmethod
    @transaction.atomic
    def add_payment_method(user_id, method_data):
        """add payment method"""
        payment_method = P2PProfileService.repo.add_payment_method_to_main(
            user_id,
            method_data
        )
        return payment_method


    @staticmethod
    def update_payment_method( user_id, method_id, data):
        """update payment method"""
        profile = P2PProfileService.repo.get_or_create_profile(user_id)
        return P2PProfileService.repo.update_payment_method(method_id, profile, **data)

    @staticmethod
    def delete_payment_method( user_id, method_id):
        profile = P2PProfileService.repo.get_or_create_profile(user_id)
        return P2PProfileService.repo.delete_payment_method(method_id, profile)


