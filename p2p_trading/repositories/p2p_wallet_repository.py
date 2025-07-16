# p2p_trading/repositories/p2p_wallet_repository.py

from ..models.p2p_transaction_model import Transaction

from  ..helpers import CREATE_WALLET


class P2PWalletRepository:

    @staticmethod
    def get_or_create_wallet(user_id, currency):
        """get or create the wallet"""
        return CREATE_WALLET(user_id, currency)

    @staticmethod
    def update_wallet_balance(wallet, balance_delta=0, locked_delta=0):
        """update the wallet balance"""
        wallet.balance += balance_delta
        wallet.locked_balance += locked_delta
        wallet.save()
        return wallet

    @staticmethod
    def create_transaction(wallet, order=None, tx_type=None, amount=0):
        """create transaction"""
        return Transaction.objects.create(
            wallet=wallet,
            related_order=order,
            transaction_type=tx_type,
            amount=amount,
            running_balance=wallet.balance
        )