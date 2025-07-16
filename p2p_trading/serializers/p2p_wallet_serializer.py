# p2p_trading/serializers/wallet_serializer.py
from rest_framework import serializers
from ..models.p2p_wallet_model import Wallet

class WalletBalanceSerializer(serializers.ModelSerializer):
    available_balance = serializers.ReadOnlyField()

    class Meta:
        model = Wallet
        fields = ['currency', 'balance', 'locked_balance', 'available_balance']

