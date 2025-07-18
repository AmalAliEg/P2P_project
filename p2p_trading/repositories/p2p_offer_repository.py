# p2p_trading/repositories/p2p_offer_repository.py
from rest_framework.exceptions import PermissionDenied

from ..constants.constant import OfferStatus
from ..models.p2p_offer_model import P2POffer
from ..models.p2p_profile_models import  P2PProfile
from MainDashboard.models import PaymentMethods

# ================ HELPER MACROS ================
from ..helpers import (get_or_404,
                       get_or_403,
                       apply_filters,
                       )

# ================ REPOSITORY CLASS ================
class P2POfferRepository:
    #filter according to the is_deleted , all records that not deleted from the database
    NON_DELETED_OFFERS = P2POffer.objects.filter(is_deleted=False)
    #filter according to the is_deleted , all records that not deleted from the database, status active
    PUBLIC_QUERY = NON_DELETED_OFFERS.filter(status=OfferStatus.ACTIVE, available_amount__gt=0)

    """*************************************************************************************************************
      /*	function name:		    create_offer
      * 	function inputs:	    validated_data 
      * 	function outputs:	    instance of the offer model (the new offer ) 
      * 	function description:	access dirctly the model to create the data 
      *     call back:              n/a
      */
    *************************************************************************************************************"""
    @staticmethod
    def create_offer(data):
        return P2POffer.objects.create(**data)


    """*************************************************************************************************************
    /*	function name:		    update_offer
    * 	function inputs:	    offer object, validated data
    * 	function outputs:	    instance of the offer model  
    * 	function description:	apply the updates direct to the offer model
    *   call back:              n/a
    */
    *************************************************************************************************************"""
    @staticmethod
    def update_offer(offer, data):
        for field, value in data.items():
            setattr(offer, field, value)
        offer.save()
        return offer

    """*************************************************************************************************************
    /*	function name:		    soft_delete
    * 	function inputs:	    offer object, validated data
    * 	function outputs:	    instance of the offer model  
    * 	function description:	delete the offer but keep the data in the database 
    *   call back:              n/a
    */
    *************************************************************************************************************"""
    @staticmethod
    def soft_delete(offer):
        offer.is_deleted = True
        offer.status = OfferStatus.INACTIVE
        offer.save(update_fields=['is_deleted', 'status'])
        return offer


    """*************************************************************************************************************
    /*	function name:		    get_public_offers
    * 	function inputs:	    filters from the url frontend 
    * 	function outputs:	    queryset of the offer model  
    * 	function description:	delete the offer but keep the data in the database 
    *   call back:              n/a
    */
    *************************************************************************************************************"""
    @staticmethod
    def get_public_offers(filters):
        #get queryset that is active, not deleted
        queryset = P2POfferRepository.PUBLIC_QUERY
        #apply filters
        queryset = apply_filters(queryset, filters)

        # order according to the price
        trade_type = filters.get('trade_type', '').upper()
        order_by = '-price' if trade_type == 'BUY' else 'price'

        return queryset.order_by(order_by)


    """*************************************************************************************************************
    /*	function name:		    get_by_id_and_owner
    * 	function inputs:	    offer id  , user id 
    * 	function outputs:	    raise error or NULL  
    * 	function description:	check the existence of the offer by sending the offer model, offer id ,
                                is_deleted, user id attri.  to get_or_404 method 
    *     call back:              get_or_404()
    */
    *************************************************************************************************************"""
    @staticmethod
    def get_by_id_and_owner(user_id, offer_id):
        """"""
        return get_or_403(
            P2POffer,
            "Offer not found or you do not have permission to access it.",
            pk=offer_id, user_id=user_id, is_deleted=False
        )
    """*************************************************************************************************************
    /*	function name:		    get_offer_with_profile
    * 	function inputs:	    user id, filters
    * 	function outputs:	    instance of the offer model ordered by creation date 
    * 	function description:	according to the offer id get the offer record from the model 
    *   call back:              n/a
    */
    *************************************************************************************************************"""
    @staticmethod
    def get_offer_with_profile(user_id,offer_id):
        #instance of repo.
        offer = P2POfferRepository.get_by_id_and_owner(user_id,offer_id)

        #get the profile that related to this offer
        offer.user_profile = P2PProfile.objects.filter(user_id=offer.user_id).first()
        return offer


    """*************************************************************************************************************
    /*	function name:		    get_by_user_and_filters
    * 	function inputs:	    user id, filters
    * 	function outputs:	    instance of the offer model ordered by creation date 
    * 	function description:	get queryset of the non-deleted offers, and apply the filters to the model
    *   call back:              n/a
    */
    *************************************************************************************************************"""
    @staticmethod
    def get_by_user_and_filters(user_id, filters):
        #get all the active offers for the user
        queryset = P2POfferRepository.NON_DELETED_OFFERS.filter(user_id=user_id)
        queryset = apply_filters(queryset, filters)
        return queryset.order_by('-created_at')


    """*************************************************************************************************************
    review
    /*	function name:		    get_payment_methods_details
    * 	function inputs:	    list of unique_ids
    * 	function outputs:	    set of payment_map 
    * 	function description:	get the details of the payment method from the main-dashboard according to the id
    *   call back:              get_offer_detail(),  P2POfferDetailSerializer()
    */
    *************************************************************************************************************"""
    @staticmethod
    def get_payment_methods_details(payment_ids):
        if not payment_ids:
            return {}
        try:
            #filter based on id if included in payment_ids and return list of dict.
            payment_methods = PaymentMethods.objects.using('main_db').filter(
                id__in=payment_ids
            ).values('id', 'type', 'holder_name', 'number', 'payment_method_id')

            #empty dict.
            payment_map = {}
            #loop over list of dict.
            #validate if the id/record has value of type, holder_name,number
            for pm in payment_methods:
                display_name = pm['type'] or 'Unknown'
                if pm.get('holder_name'):
                    display_name = f"{pm['type']} ({pm['holder_name']})"
                elif pm.get('number') and len(pm['number']) > 4:
                    display_name = f"{pm['type']} (****{pm['number'][-4:]})"

                #append the dict ,
                payment_map[pm['id']] = {
                    'id': pm['id'],
                    'type': pm['type'],
                    'display_name': display_name,
                    'payment_method_id': pm.get('payment_method_id')
                }
            return payment_map
        except Exception as e:
            print(f"Error fetching payment methods: {str(e)}")
            return {}

