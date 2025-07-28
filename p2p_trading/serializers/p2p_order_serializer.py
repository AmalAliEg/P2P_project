# p2p_trading/serializers/p2p_order_serializer.py

from rest_framework import serializers

from ..helpers.p2p_macro_helpers import format_price
from ..models.p2p_order_model import P2POrder
from ..models.p2p_profile_models import P2PProfile
from ..constants.constant import STATUS_MAP

# ================ HELPER MACROS ================
from ..helpers import (
    get_counterparty_id,
    get_trade_type,
    format_fiat,
    format_crypto,
    DECIMAL_FIELD,
)


# ================ BASE SERIALIZER ================

class P2POrderCreateSerializer(serializers.Serializer):
    """Serializer to create new order"""
    offer_id = serializers.IntegerField()
    fiat_amount = DECIMAL_FIELD(20, 2)


class P2POrderListSerializer(serializers.ModelSerializer):
    """Serializer to show the list of the orders"""
    counterparty = serializers.SerializerMethodField()
    type_date = serializers.SerializerMethodField()
    fiat_crypto_amount = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = P2POrder
        fields = ['id', 'order_number', 'type_date', 'price',
                  'fiat_crypto_amount', 'counterparty', 'status_display']

    def get_type_date(self, obj):
        """get the type data and create the date"""
        user_id = self.context['request'].user.id
        return {
            'type': get_trade_type(obj, user_id),
            'date': obj.created_at.strftime('%Y-%m-%d %H:%M')
        }

    def get_fiat_crypto_amount(self, obj):
        """thr fiat"""
        return {
            'fiat': format_fiat(obj.fiat_amount, obj.fiat_currency),
            'crypto': format_crypto(obj.crypto_amount, obj.crypto_currency)
        }

    def get_counterparty(self, obj):
        """get the counterparty"""
        counterparty_id = get_counterparty_id(obj, self.context['request'].user.id)
        try:
            return P2PProfile.objects.get(user_id=counterparty_id).nickname
        except P2PProfile.DoesNotExist:
            return f"User{counterparty_id}"

    def get_status_display(self, obj):
        """show the statuse of the order """
        return STATUS_MAP.get(obj.status, {'text': obj.status, 'class': 'default'})


#====================PNL ===========================
class PNLStatementSerializer(serializers.Serializer):
    """Serializer لبيان الأرباح والخسائر"""
    coin = serializers.CharField()

    # بيانات الشراء
    buy_orders = serializers.IntegerField()
    buy_avg_price = serializers.SerializerMethodField()
    buy_total_crypto = DECIMAL_FIELD(20, 8, 0)
    buy_total_fiat = DECIMAL_FIELD(20, 2, 0)

    # بيانات البيع
    sell_orders = serializers.IntegerField()
    sell_avg_price = serializers.SerializerMethodField()
    sell_total_crypto = DECIMAL_FIELD(20, 8, 0)
    sell_total_fiat = DECIMAL_FIELD(20, 2, 0)

    # الرسوم والأرباح
    total_txn_fee = DECIMAL_FIELD(20, 8, 0)
    profit_loss = serializers.SerializerMethodField()

    def get_buy_avg_price(self, obj):
        """متوسط سعر الشراء مع العملة"""
        return format_price(obj.get('buy_avg_price', 0))

    def get_sell_avg_price(self, obj):
        """متوسط سعر البيع مع العملة"""
        return format_price(obj.get('sell_avg_price', 0))

    def get_profit_loss(self, obj):
        """حساب الربح/الخسارة المحققة"""
        # Extract values with defaults
        sell_total = obj.get('sell_total_fiat', 0)
        buy_total = obj.get('buy_total_fiat', 0)
        sell_crypto = obj.get('sell_total_crypto', 0)
        buy_crypto = obj.get('buy_total_crypto', 0)
        fees = obj.get('total_txn_fee', 0)

        # Check if PnL calculation is applicable
        if not (sell_total and buy_total):
            return "N/A"

        # Calculate PnL
        min_crypto = min(sell_crypto, buy_crypto)
        avg_buy = buy_total / buy_crypto if buy_crypto else 0
        avg_sell = sell_total / sell_crypto if sell_crypto else 0
        pnl = (avg_sell - avg_buy) * min_crypto - (fees * avg_sell)

        return f"{pnl:+.2f} EGP"

