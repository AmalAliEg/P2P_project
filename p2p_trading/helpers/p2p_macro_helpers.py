# p2p_trading/helpers/macro_helpers.py

from decimal import Decimal
from datetime import datetime
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied

from ..constants.constant import OrderStatus
from ..models.p2p_wallet_model import Wallet

# ================ HELPER MACROS CONTROLLERS================

# Context helper
GET_CONTEXT = lambda self: {'request': self.request}


# ================ HELPER MACROS WALLET CONTROLLERS================

# Macros
VALIDATE_AMOUNT = lambda amount: amount > 0
GET_CURRENCY = lambda request, default='USDT': request.query_params.get('currency', default)
GET_AMOUNT = lambda data: Decimal(data.get('amount', 0))



# ================ HELPER MACROS OFFER SERVICES================
def get_decimal(value):
    """Macro لتحويل إلى Decimal بأمان"""
    return Decimal(str(value)) if value is not None else Decimal('0')


"""*************************************************************************************************************
/*	function name:		    enrich_offers_with_profiles
* 	function inputs:	    queryset of profile that match the ids
* 	function outputs:	    queryset of offers that match te ids  
* 	function description:	add the profile data to each offer 
*   call back:              n/a
*/
*************************************************************************************************************"""
def enrich_offers_with_profiles(offers, profile_model):

    if not offers:
        return offers

    # get all profiles removing the repeated ids
    user_ids = list(set(offer.user_id for offer in offers))
    #get list of profiles
    profiles = profile_model(user_ids)
    #map list pf profile to dic
    profiles_map = {
        p.user_id: p for p in profiles
    }

    # add profile that match the offer
    for offer in offers:
        offer.user_profile = profiles_map.get(offer.user_id)

    return offers


# ================ HELPER MACROS ORDER SERVICES================
# Order type helpers
GET_TAKER_TYPE = lambda offer_type: 'BUY' if offer_type == 'SELL' else 'SELL'

# Time helpers
PAYMENT_DEADLINE = lambda minutes: timezone.now() + timezone.timedelta(minutes=minutes)

GET_BUYER_ID = lambda order: order.taker_id if order.trade_type == 'BUY' else order.maker_id
GET_SELLER_ID = lambda order: order.maker_id if order.trade_type == 'BUY' else order.taker_id
# ================ HELPER MACROS WALLET SERVICE================

GET_SELLER_BUYER = lambda order: (
    (order.offer.user_id, order.taker_id) if order.offer.trade_type == 'SELL'
    else (order.taker_id, order.offer.user_id)
)

VALIDATE_BALANCE = lambda wallet, amount, balance_type='balance': (
    ValueError(f"Insufficient {balance_type}. Available: {getattr(wallet, balance_type)}, Required: {amount}")
    if getattr(wallet, balance_type) < amount else None
)


# ================ HELPER MACROS OFFER SERIALIZER================
def format_currency(amount, currency, decimals=8):
    """Macro"""
    return f"{amount:.{decimals}f} {currency}"

"""*************************************************************************************************************
 /*	function name:		    get_user_display_name
 * 	function inputs:	    profile instance or None, user id 
 * 	function outputs:	    string (nickname or User{id})
 * 	function description:	to return the nikename if
 *   call back:             n/a
 */
 *************************************************************************************************************"""
def get_user_display_name(profile, user_id):
    return profile.nickname if profile else f'User{user_id}'

"""*************************************************************************************************************
 /*	function name:		    get_profile_stats
 * 	function inputs:	    profile instance or None
 * 	function outputs:	    dict with total_orders and completion_rate
 * 	function description:	to return the total of orders and completed rate
 *   call back:             n/a
 */
 *************************************************************************************************************"""
def get_profile_stats(profile):
    return {
        'total_orders': profile.total_30d_trades if profile else 0,
        'completion_rate': f"{profile.completion_rate_30d if profile else 100.0:.2f}%"
    }

# ================ HELPER MACROS ORDER SERIALIZER================
# Macros for common patterns
DECIMAL_FIELD = lambda digits, places, min_val=0.01: serializers.DecimalField(
    max_digits=digits, decimal_places=places, min_value=min_val
)

# Order Helpers
get_counterparty_id = lambda obj, user_id: obj.taker_id if obj.maker_id == user_id else obj.maker_id
get_trade_type = lambda obj, user_id: obj.trade_type if obj.taker_id == user_id else ('Sell' if obj.trade_type == 'BUY' else 'Buy')

# Format Helpers
format_price = lambda price, currency='EGP': f"{price:.2f} {currency}"
format_crypto = lambda amount, currency: f"{amount:.8f} {currency}"
format_fiat = lambda amount, currency: f"{amount:.2f} {currency}"


# ================ HELPER MACROS OFFER REPOSITORY================

"""*************************************************************************************************************
/*	function name:		    parse_date
* 	function inputs:	    value of the key type str.
* 	function outputs:	    date
* 	function description:	turn the str to datetime object 
*   call back:              n/a
*/
*************************************************************************************************************"""
def parse_date(date_str, end_of_day=False):
    #validate if there str value
    if not date_str:
        return None
    try:
        #transfer the str to datetime object
        date = datetime.strptime(date_str, '%Y-%m-%d')
        #configure time zone needed by django
        date = timezone.make_aware(date)
        #if the filter is end date
        if end_of_day:
            #instead of 00:00:00
            date = date.replace(hour=23, minute=59, second=59)
        return date
    except ValueError:
        return None

"""*************************************************************************************************************
      /*	function name:		    get_or_404
      * 	function inputs:	    model class it self , error_msg, any attri like pk
      * 	function outputs:	    raise error or nothing   
      * 	function description:	check the existence of the offer 
      *     call back:              n/a
      */
*************************************************************************************************************"""
def get_or_404(model, error_msg="Object not found", **kwargs):

    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        raise NotFound(error_msg)

def get_or_403(model, error_msg="Access denied", **kwargs):
    """Macro للبحث مع رفع خطأ 403"""
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        raise PermissionDenied(error_msg)

# ================ HELPER MACROS ORDER REPOSITORY================
# Status time fields mapping

STATUS_TIME_FIELDS = {
    OrderStatus.PAID: ('paid_at', timezone.now),
    OrderStatus.COMPLETED: ('completed_at', timezone.now),
    OrderStatus.CANCELLED: ('cancelled_at', timezone.now)
}

# ================ HELPER MACROS WALLET REPOSITORY================

CREATE_WALLET = lambda user_id, currency: Wallet.objects.get_or_create(
    user_id=user_id, currency=currency,
    defaults={'balance': 0, 'locked_balance': 0}
)[0]


# ================ HELPER MACROS PROFILE================

# Profile stats helpers

FORMAT_PERCENTAGE = lambda value: f"{value:.2f}%"
FORMAT_TIME = lambda minutes: f"{minutes:.2f} Minute(s)"

