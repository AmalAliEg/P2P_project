# p2p_trading/helpers/validation_helpers.py

from decimal import Decimal
from rest_framework.exceptions import ValidationError
from ..constants.constant import TradeType, OfferStatus, PriceType

from ..helpers.p2p_macro_helpers  import get_decimal


# ================ HELPER MACROS OFFER SERVICE================

def validate_and_raise(condition, error_message, field=None):
    """Macro للتحقق ورفع خطأ"""
    if condition:
        error = {field: error_message} if field else error_message
        raise ValidationError(error)

def validate_payment_methods(payment_ids):
    """التحقق من تنسيق قائمة طرق الدفع فقط"""
    if not payment_ids:
        return True

    if not isinstance(payment_ids, list):
        raise ValidationError('payment_method_ids must be a list')

    for pid in payment_ids:
        if not isinstance(pid, int) or pid <= 0:
            raise ValidationError(f'Invalid payment method ID format: {pid}')

    return True

class OfferValidator:
    """مجموعة validations للعروض"""

    @staticmethod
    def validate_price_limits(data):
        """التحقق من حدود السعر"""
        if data.get('price_type') != PriceType.FIXED:
            return

        total_amount = get_decimal(data.get('total_amount'))
        price = get_decimal(data.get('price'))
        max_limit = get_decimal(data.get('max_order_limit'))

        total_fiat_value = total_amount * price

        validate_and_raise(
            max_limit > total_fiat_value,
            f'Maximum order limit ({max_limit}) cannot exceed the total offer value ({total_fiat_value:.2f} {data["fiat_currency"]})',
            'max_order_limit'
        )

    @staticmethod
    def validate_balance_for_sell(user_id, data):
        """التحقق من الرصيد للبيع (مؤقتاً معطل)"""
        if data.get('trade_type') != TradeType.SELL:
            return
        # TODO: Add balance check when wallet service is available
        pass

    @staticmethod
    def validate_offer_update(offer, user_id, data):
        """التحقق من صلاحية التحديث"""
        validate_and_raise(
            offer.user_id != user_id,
            "You don't have permission to update this offer"
        )

        validate_and_raise(
            offer.status == OfferStatus.COMPLETED,
            "Cannot update a completed offer. Please create a new one."
        )

        # التحقق من تقليل الكمية
        if 'total_amount' in data and data['total_amount'] < offer.total_amount:
            sold_amount = offer.total_amount - offer.available_amount
            validate_and_raise(
                data['total_amount'] < sold_amount,
                f"Cannot reduce total amount below sold amount ({sold_amount})"
            )

    @staticmethod
    def validate_offer_deletion(offer):
        """التحقق من إمكانية الحذف"""
        if offer.available_amount < offer.total_amount:
            sold = offer.total_amount - offer.available_amount
            validate_and_raise(
                True,
                f"Cannot delete offer with active trades. {sold} already sold."
            )

# ================ HELPER MACROS ORDER SERVICE================
VALIDATE_PERMISSION = lambda condition, msg: validate_and_raise(condition, msg) if condition else None