# p2p_trading/services/p2p_profile_service.py

from django.db import transaction
from rest_framework.exceptions import ValidationError

from ..repositories.p2p_profile_repository import P2PProfileRepository, GET_OR_CREATE_PROFILE
from ..helpers import validate_and_raise, ORDER_FEEDBACK_RESPONSE


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



    @staticmethod
    def get_user_feedback( user_id):
        """
        get the feedback of a user
        args:
            user_id: user id
        return:
            feedback: feedback
        """

        profile = P2PProfileService.repo.get_or_create_profile(user_id)
        return P2PProfileService.repo.get_feedback(profile, feedback_type='received')

    @staticmethod
    def add_feedback( reviewer_id, order_id, is_positive, comment=''):
        #get the order
        order_data = P2PProfileService.repo.validate_feedback_order(order_id,reviewer_id)


        #validate the status of the order
        if not order_data['valid']:
            raise ValidationError(order_data['error'])

        #add the feedback
        reviewer_profile = P2PProfileService.repo.get_or_create_profile(reviewer_id)
        reviewee_profile = P2PProfileService.repo.get_or_create_profile(order_data['reviewee_id'])

        feedback= P2PProfileService.repo.add_feedback(
            reviewer_profile=reviewer_profile,
            reviewee_profile=reviewee_profile,
            order=order_data['order'],
            is_positive=is_positive,
            comment=comment
        )
        #P2PProfileService.repo.update_feedback_stats(reviewee_profile)
        return feedback

    @staticmethod
    def get_order_feedback(user_id, order_id):
        """
        get mutual feedback for a specific order
        """
        # validate user is part of the order
        order = P2PProfileService.repo.validate_user_in_order(user_id, order_id)

        # get both feedbacks
        my_feedback = P2PProfileService.repo.get_my_feedback_for_order(user_id, order_id)
        other_feedback = P2PProfileService.repo.get_other_feedback_for_order(user_id, order_id)

        return ORDER_FEEDBACK_RESPONSE(order_id, my_feedback, other_feedback)


    @staticmethod
    def get_blocked_users( user_id):
        profile = GET_OR_CREATE_PROFILE(user_id)
        return P2PProfileRepository.get_blocked_users(profile)

    @staticmethod
    def block_user( blocker_id, blocked_id):
        validate_and_raise(
            blocker_id == blocked_id,
            "Cannot block yourself"
        )

        blocker_profile = GET_OR_CREATE_PROFILE(blocker_id)
        blocked_profile = GET_OR_CREATE_PROFILE(blocked_id)

        # Remove any existing follow relationships
        P2PProfileRepository.unfollow_user(blocker_profile, blocked_profile)
        P2PProfileRepository.unfollow_user(blocked_profile, blocker_profile)

        return P2PProfileRepository.block_user(blocker_profile, blocked_profile)

    @staticmethod
    def unblock_user(blocker_id, blocked_id):
        blocker_profile = GET_OR_CREATE_PROFILE(blocker_id)
        blocked_profile = GET_OR_CREATE_PROFILE(blocked_id)

        P2PProfileRepository.unblock_user(blocker_profile, blocked_profile)

    @staticmethod
    def get_followers( user_id):
        profile = GET_OR_CREATE_PROFILE(user_id)
        return P2PProfileRepository.get_followers(profile)

    @staticmethod
    def get_following( user_id):
        profile = GET_OR_CREATE_PROFILE(user_id)
        return P2PProfileRepository.get_following(profile)

    @staticmethod
    def follow_user( follower_id, followed_id):
        validate_and_raise(
            follower_id == followed_id,
            "Cannot follow yourself"
        )

        follower_profile = GET_OR_CREATE_PROFILE(follower_id)
        followed_profile = GET_OR_CREATE_PROFILE(followed_id)

        # Check if blocked (from either side)
        is_blocked = P2PProfileRepository.is_blocked(follower_profile, followed_profile)
        validate_and_raise(
            is_blocked,
            "Cannot follow this user due to blocking"
        )

        return P2PProfileRepository.follow_user(follower_profile, followed_profile)

    @staticmethod
    def unfollow_user( follower_id, followed_id):
        follower_profile = GET_OR_CREATE_PROFILE(follower_id)
        followed_profile = GET_OR_CREATE_PROFILE(followed_id)

        P2PProfileRepository.unfollow_user(follower_profile, followed_profile)
