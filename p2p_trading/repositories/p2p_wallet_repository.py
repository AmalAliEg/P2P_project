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
        """
        this function to update the wallet balance
        args:
            wallet: the wallet to update
            balance_delta: the amount of the wallet balance
            locked_delta: the amount of the wallet locked
        return:
            the updated wallet balance
        """
        wallet.balance += balance_delta
        wallet.locked_balance += locked_delta
        wallet.save()
        return wallet

    @staticmethod
    def create_transaction(wallet, order=None, tx_type=None, amount=0):
        """
        this functiom that create transaction
        args:
            wallet: the wallet to create
            order: the order to create the transaction
            tx_type: the transaction type
            amount: the amount of the transaction
        return:
            the created transaction

        """
        return Transaction.objects.create(
            wallet=wallet,
            related_order=order,
            transaction_type=tx_type,
            amount=amount,
            running_balance=wallet.balance
        )