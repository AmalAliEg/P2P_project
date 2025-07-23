# p2p_trading/services/p2p_offer_service.py

from django.db import transaction

from ..repositories.p2p_offer_repository import P2POfferRepository
from ..repositories.p2p_profile_repository import P2PProfileRepository
from ..serializers.p2p_offer_serilaizer import P2POfferCreateSerializer


# ================ HELPER MACROS ================
from ..helpers import (
    validate_and_raise,
    OfferValidator,
    enrich_offers_with_profiles
)
# ================ SERVICE CLASS ================
class P2POfferService:
    repo = P2POfferRepository()  # Repository instance


    """*************************************************************************************************************
    /*	function name:		    create_offer
    * 	function inputs:	    user id, data in the body send within the request
    * 	function outputs:	    validated_data send to the repository
    * 	function description:	clean, fiter the data before send to the repository
    *   call back:              repo.create_offer(), P2POfferCreateSerializer(), validate_price_limits(), 
                                validate_payment_methods_ownership(), validate_balance_for_sell()
    */
    *************************************************************************************************************"""
    @staticmethod
    @transaction.atomic
    def create_offer(user_id, data):
        """create new offer"""
        # 1. Validate input
        #instance of the P2POfferCreateSerializer
        serializer = P2POfferCreateSerializer(data=data)
        validate_and_raise(not serializer.is_valid(), serializer.errors)
        #edit the types if the user didn't, add the missed fields with the default value if the user didn't add them
        validated_data = serializer.validated_data

        # 2. Business validations id the logic. the user added the min./max. limits or has a valid payment-method
        OfferValidator.validate_price_limits(validated_data)
        P2PProfileRepository.validate_payment_methods_ownership(
            user_id,
            validated_data.get('payment_method_ids', [])
        )
        #validate thet the user has crypto in the wallet if he is seller
        OfferValidator.validate_balance_for_sell(user_id, validated_data)

        # 3. Prepare data
        validated_data.update({
            'user_id': user_id,
            'available_amount': validated_data['total_amount']
        })

        # 4. Create offer
        return P2POfferService.repo.create_offer(validated_data)

    """*************************************************************************************************************
    /*	function name:		    get_user_offers
    * 	function inputs:	    user id, filters
    * 	function outputs:	    instance of the offer model
    * 	function description:	pass the user id , filters or empty set if no filters 
    *   call back:              n/a
    */
    *************************************************************************************************************"""
    @staticmethod
    def get_user_offers(user_id, filters=None):
        return P2POfferService.repo.get_by_user_and_filters(user_id, filters or {})

    """*************************************************************************************************************
    /*	function name:		    get_offer_detail
    * 	function inputs:	    user id, offer_id 
    * 	function outputs:	    instance of the offer model
    * 	function description:	function return object of specific offer 
    *   call back:              get_offer_with_profile()
    */
    *************************************************************************************************************"""
    @staticmethod
    def get_offer_detail(user_id, offer_id):
        return P2POfferService.repo.get_offer_with_profile(user_id,offer_id)

    """*************************************************************************************************************
    /*	function name:		    update_offer
    * 	function inputs:	    user id, offer_id , validated data 
    * 	function outputs:	    instance of the offer model
    * 	function description:	function return object of updated offer 
    *    call back:              get_by_id(),validate_offer_update(),update_offer()
    */
    *************************************************************************************************************"""
    @staticmethod
    @transaction.atomic
    def update_offer(user_id, offer_id, data):
        #validate the existence of the offerو user id
        offer = P2POfferService.repo.get_by_id_and_owner(user_id,offer_id)
        #apply validations over offer status, total amount
        OfferValidator.validate_offer_update(offer, data)
        return P2POfferService.repo.update_offer(offer, data)

    """*************************************************************************************************************
    /*	function name:		    delete_offer
    * 	function inputs:	    user id, offer_id 
    * 	function outputs:	    instance of the offer model
    * 	function description:	function to delete the object/record of offer model 
    *    call back:             get_by_id_and_owner(),validate_offer_deletion(),soft_delete()
    */
    *************************************************************************************************************"""
    @staticmethod
    @transaction.atomic
    def delete_offer(user_id, offer_id):
        #validate the existence of the offerو user id
        offer = P2POfferService.repo.get_by_id_and_owner(user_id, offer_id)
        #apply validations to check if there are active orders within this offer
        OfferValidator.validate_offer_deletion(offer)
        return P2POfferService.repo.soft_delete(offer)

    """*************************************************************************************************************
    /*	function name:		    get_public_offers
    * 	function inputs:	    user id, offer_id 
    * 	function outputs:	    instance of the offer model
    * 	function description:	function to get all the objects/records of offer model 
    *    call back:             get_public_offers(),enrich_offers_with_profiles(),get_profiles_by_user_ids()
    */
    *************************************************************************************************************"""
    @staticmethod
    def get_public_offers(filters):
        clean_filters = {k: v for k, v in filters.items() if v}
        offers = P2POfferService.repo.get_public_offers(clean_filters)
        return enrich_offers_with_profiles(offers, P2PProfileRepository.get_profiles_by_user_ids)


    """*************************************************************************************************************
    /*	function name:		    get_payment_methods_for_offers
    * 	function inputs:	    queryset/objects of offer model
    * 	function outputs:	    list of unique_ids
    * 	function description:	get id for each offer and pass the ids to the repository
    *   call back:              get_payment_methods_details()
    */
    *************************************************************************************************************"""
    @staticmethod
    def get_payment_methods_for_offers(offers):

        # create list to add all payment IDs
        all_payment_ids = []
        #loop all the offers/queryset to append the payment-method-id
        for offer in offers:
            if offer.payment_method_ids:
                all_payment_ids.extend(offer.payment_method_ids)

        # remove the repeats
        unique_ids = list(set(all_payment_ids))

        # get the details from repository
        return P2POfferRepository.get_payment_methods_details(unique_ids)

    """*************************************************************************************************************
    /*	function name:		    get_payment_methods_for_offers
    * 	function inputs:	    object of offer model
    * 	function outputs:	    list of unique_ids from tj
    * 	function description:	get ids for object and pass the ids to the repository
    *   call back:              get_payment_methods_details()
    */
    *************************************************************************************************************"""
    @staticmethod
    def get_payment_methods_for_single_offer(offer):
        #validate the existence of the payment_method_ids within the offer object
        if not offer.payment_method_ids:
            return {}
        return P2POfferRepository.get_payment_methods_details(offer.payment_method_ids)





















