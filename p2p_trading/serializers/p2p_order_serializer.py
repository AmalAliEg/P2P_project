# p2p_trading/serializers/p2p_order_serializer.py

from rest_framework import serializers
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



