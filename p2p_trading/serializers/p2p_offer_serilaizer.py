# p2p_trading/serializers/p2p_offer_serializer.py

from decimal import Decimal
from rest_framework import serializers
from p2p_trading.constants.constant import PriceType
from p2p_trading.models.p2p_offer_model import P2POffer

# ================ HELPER MACROS ================
from ..helpers import (
    format_currency,
    get_user_display_name,
    get_profile_stats
)


# ================ BASE SERIALIZER ================
class BaseOfferSerializer(serializers.ModelSerializer):
    """Base serializer  common methods """


    """*************************************************************************************************************
     /*	function name:		    get_advertiser_info
     * 	function inputs:	    instance of  model
     * 	function outputs:	    
     * 	function description:	return price if the price type is floating 
     *   call back:             get_user_display_name(), get_profile_stats(), 
     */
     *************************************************************************************************************"""
    def get_advertiser_info(self, obj):
        profile = getattr(obj, 'user_profile', None)
        return {
            'user_id': obj.user_id,
            'nickname': get_user_display_name(profile, obj.user_id),
            **get_profile_stats(profile)
        }

    """*************************************************************************************************************
     /*	function name:		    get_formatted_limits
     * 	function inputs:	    instance of  model
     * 	function outputs:	    
     * 	function description:	
     *   call back:              n/a
     */
     *************************************************************************************************************"""
    def get_formatted_limits(self, obj):
        return {
            'min': format_currency(obj.min_order_limit, obj.fiat_currency, 2),
            'max': format_currency(obj.max_order_limit, obj.fiat_currency, 2),
            'available': format_currency(obj.available_amount, obj.crypto_currency)
        }

# ================ CREATE SERIALIZER ================



class P2POfferCreateSerializer(serializers.ModelSerializer):

    #it restrict the format of the payment_methods_id to be only list
    #  payment_method_ids = []
    payment_method_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )

    class Meta:
        model = P2POffer
        #all fields required, but only price_margin,payment_method_ids,auto_reply_message optional
        fields = [
            'trade_type', 'crypto_currency', 'fiat_currency', 'price_type', 'price',
            'price_margin', 'total_amount', 'min_order_limit', 'max_order_limit',
            'payment_method_ids', 'payment_time_limit_minutes', 'remarks',
            'auto_reply_message', 'counterparty_min_registration_days',
            'counterparty_min_holding_amount'
        ]
        read_only_fields = ['id', 'available_amount', 'created_at', 'updated_at']

# ================ LIST SERIALIZER ================
class P2POfferListSerializer(BaseOfferSerializer):
    # use to_representation instead of SerializerMethodField
    class Meta:
        model = P2POffer
        fields = [
            'id', 'trade_type', 'crypto_currency', 'fiat_currency',
            'total_amount', 'available_amount', 'price', 'price_type',
            'price_margin', 'payment_method_ids', 'status',
            'created_at', 'updated_at'
        ]
    #use the to_representation because we r dealing with compicated data here
    def to_representation(self, instance):
        data = super().to_representation(instance)

        # update the values of the statistics attr.
        data.update({

            'offer_no': str(instance.id).replace('-', '')[:8].upper(),
            'total_amount_display': format_currency(instance.total_amount, instance.crypto_currency),
            'price_display': self._get_price_display(instance),
            'completed_rate': self._calculate_completion_rate(instance),
            'payment_methods_details': self._get_payment_methods(instance)
        })

        return data

    """*************************************************************************************************************
     /*	function name:		    _get_price_display
     * 	function inputs:	    instance of  model
     * 	function outputs:	    string (formatted price or market margin)
     * 	function description:	return formatted price if fixed, or market margin percentage if floating
     *   call back:              n/a
     */
     *************************************************************************************************************"""
    def _get_price_display(self, obj):
        """update the price based on price-type fixed or float"""
        if obj.price_type == PriceType.FIXED:
            return format_currency(obj.price, obj.fiat_currency, 2)
        margin = obj.price_margin or Decimal('0')
        return f"Market {'+' if margin >= 0 else ''}{margin}%"

    """*************************************************************************************************************
    /*	function name:		    _calculate_completion_rate
    * 	function inputs:	    instance of model
    * 	function outputs:	    rate of completion--->string percentage 
    * 	function description:	return the percentage of completed order within this offer  
    *   call back:              n/a
    */
    *************************************************************************************************************"""
    def _calculate_completion_rate(self, obj):
        if obj.total_amount <= 0:
            return "0.0%"
        rate = ((obj.total_amount - obj.available_amount) / obj.total_amount) * 100
        return f"{rate:.1f}%"

    """*************************************************************************************************************
   /*	function name:		    _get_payment_methods
   * 	function inputs:	    instance of model
   * 	function outputs:	    list of payment method display names
   * 	function description:	return the payment method display names for each offer   
   *   call back:              n/a
   */
   *************************************************************************************************************"""
    def _get_payment_methods(self, obj):
        payment_map = self.context.get('payment_details_map', {})
        return [
            payment_map.get(id, {}).get('display_name', f"Payment Method #{id}")
            for id in (obj.payment_method_ids or [])
        ]

# ================ DETAIL SERIALIZER ================
class P2POfferDetailSerializer(BaseOfferSerializer):
    class Meta:
        model = P2POffer
        fields = [
            'id', 'trade_type', 'crypto_currency', 'fiat_currency',
            'price', 'price_type', 'payment_method_ids',
            'payment_time_limit_minutes','status'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update({
            'advertiser': self.get_advertiser_info(instance),
            'order_limit': self.get_formatted_limits(instance),
            'payment_methods': instance.payment_method_ids or []
        })
        return data

# ================ UPDATE SERIALIZER ================
class OfferStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = P2POffer
        fields = [
            'status', 'price', 'price_margin', 'total_amount',
            'min_order_limit', 'max_order_limit', 'payment_method_ids',
            'payment_time_limit_minutes', 'remarks', 'auto_reply_message'
        ]
        # for partial update
        extra_kwargs = {
            'price': {'required': False},
            'total_amount': {'required': False},
            'min_order_limit': {'required': False},
            'max_order_limit': {'required': False},
            'payment_method_ids': {'required': False},
            'price_margin': {'required': False},
            'payment_time_limit_minutes': {'required': False},
            'status': {'required': False}
        }

# ================ PUBLIC SERIALIZER ================
class P2POfferPublicSerializer(BaseOfferSerializer):
    class Meta:
        model = P2POffer
        fields = [
            'id', 'price', 'available_amount', 'trade_type',
            'crypto_currency', 'fiat_currency', 'payment_method_ids',
            'payment_time_limit_minutes'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        #calculate the avail. fait
        available_in_fiat = instance.available_amount * instance.price

        data.update({
            'advertiser': self.get_advertiser_info(instance),
            'order_limit': f"{instance.min_order_limit:.2f} - {instance.max_order_limit:.2f} {instance.fiat_currency}",
            'available_order_limit': format_currency(available_in_fiat, instance.fiat_currency, 2),
            'payment_methods': self._get_payment_types(instance)
        })

        return data


    """*************************************************************************************************************
    /*	function name:		    _get_payment_types
    * 	function inputs:	    instance of model
    * 	function outputs:	    return payment_method 
    * 	function description:	return the payment method id and deatils for each    
    *   call back:              n/a
    */
    *************************************************************************************************************"""
    def _get_payment_types(self, obj):
        payment_map = self.context.get('payment_details_map', {})
        if not payment_map:
            return ["there no payment method provided"]
        return [payment_map.get(payment_id, {}).get('type', 'Unknown') for payment_id in obj.payment_method_ids]