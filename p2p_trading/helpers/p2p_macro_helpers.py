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

def enrich_offers_with_profiles(offers, profile_model):
    """Helper to add profiles to offers"""
    if not offers:
        return offers

    # get all profiles
    user_ids = list(set(offer.user_id for offer in offers))
    profiles = profile_model(user_ids)

    profiles_map = {
        p.user_id: p for p in profiles
    }

    # add profile to each offer
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

def get_user_display_name(profile, user_id):
    """Macro to display user's name"""
    return profile.nickname if profile else f'User{user_id}'

def get_profile_stats(profile):
    """Macro for profile statistics"""
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
def parse_date(date_str, end_of_day=False):
    """Macro لتحويل التاريخ"""
    if not date_str:
        return None
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        date = timezone.make_aware(date)
        if end_of_day:
            date = date.replace(hour=23, minute=59, second=59)
        return date
    except ValueError:
        return None

def get_or_404(model, error_msg="Object not found", **kwargs):
    """Macro للبحث مع رفع خطأ 404"""
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
#CALCULATE_COMPLETION_RATE = lambda completed, total: (completed / total * 100) if total > 0 else 100.0
#CALCULATE_POSITIVE_RATE = lambda positive, total: (positive / total * 100) if total > 0 else 100.0
FORMAT_PERCENTAGE = lambda value: f"{value:.2f}%"
FORMAT_TIME = lambda minutes: f"{minutes:.2f} Minute(s)"

