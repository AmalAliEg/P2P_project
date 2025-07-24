# p2p_trading/services/p2p_wallet_service.py

from django.db import transaction as db_transaction
from ..constants.constant import TransactionType
from ..repositories.p2p_wallet_repository import P2PWalletRepository


# ================ HELPER MACROS ================

from ..helpers import (
    GET_SELLER_BUYER,
    VALIDATE_BALANCE

)

# ================P2P WALLET SERVICE CLASS ================
class WalletService:
    #common object of P2PWalletRepository
    repo = P2PWalletRepository()

    @staticmethod
    def get_or_create_wallet(user_id, currency):
        """create wallet"""
        return WalletService.repo.get_or_create_wallet(user_id, currency)

    @staticmethod
    @db_transaction.atomic
    def lock_funds_for_order(order):
        """
            lock the crypto amount of funds
            arg:
                instance of the order
            return:
            locking the amount of funds in the wallet

        """
        seller_id, _ = GET_SELLER_BUYER(order)
        wallet = WalletService.repo.get_or_create_wallet(seller_id, order.crypto_currency)
        amount = order.crypto_amount

        # validata the suffeient amount
        error = VALIDATE_BALANCE(wallet, amount)
        if error: raise error

        # update the balance of the wallet
        WalletService.repo.update_wallet_balance(wallet, -amount, amount)

        # create a transaction
        WalletService.repo.create_transaction(
            wallet, order, TransactionType.LOCK_ESCROW, -amount
        )
        return wallet

    @staticmethod
    @db_transaction.atomic
    def release_funds_to_buyer(order):
        """release the crypto to the seller once the order completed"""
        seller_id, buyer_id = GET_SELLER_BUYER(order)
        seller_wallet = WalletService.repo.get_or_create_wallet(seller_id, order.crypto_currency)
        buyer_wallet = WalletService.repo.get_or_create_wallet(buyer_id, order.crypto_currency)
        amount = order.crypto_amount

        # validate the amount in the user wallet
        error = VALIDATE_BALANCE(seller_wallet, amount, 'locked_balance')
        if error: raise error

        # update the wallet
        WalletService.repo.update_wallet_balance(seller_wallet, 0, -amount)
        WalletService.repo.update_wallet_balance(buyer_wallet, amount, 0)

        # create transaction
        WalletService.repo.create_transaction(
            seller_wallet, order, TransactionType.RELEASE_ESCROW, 0
        )
        WalletService.repo.create_transaction(
            buyer_wallet, order, TransactionType.DEPOSIT, amount
        )

        return True

    @staticmethod
    @db_transaction.atomic
    def cancel_order_and_unlock_funds(order):
        """
        this handle the logic to cancel the order and unlock the wallet
        args:
            instance of the order
        return:
            instance of the wallet
        """
        #get seller id , seller who need to get the currencies back
        seller_id, _ = GET_SELLER_BUYER(order)
        #get the wallet of the seller
        wallet = WalletService.repo.get_or_create_wallet(seller_id, order.crypto_currency)
        #the locked amount
        amount = order.crypto_amount

        # release the fund back
        WalletService.repo.update_wallet_balance(wallet, amount, -amount)

        # create transaction
        WalletService.repo.create_transaction(
            wallet, order, TransactionType.CANCEL_ESCROW, amount
        )
        return wallet




'''
    @staticmethod
    @db_transaction.atomic
    def transfer_from_main_wallet(user_id, currency, amount):
        """ transfer the crypto from the main-wallet to P2P-wallet"""

        #  add to P2P-wallet
        p2p_wallet = WalletService.repo.get_or_create_wallet(user_id, currency)
        WalletService.repo.update_wallet_balance(p2p_wallet, amount, 0)

        # create transaction for p2p-transaction
        WalletService.repo.create_transaction(
            p2p_wallet, None, TransactionType.DEPOSIT, amount
        )
        return p2p_wallet

    @staticmethod
    @db_transaction.atomic
    def transfer_to_main_wallet(user_id, currency, amount):
        """trnasfer crypto from p2p-wallet to main-wallet"""
        p2p_wallet = WalletService.repo.get_or_create_wallet(user_id, currency)

        # validation for the sufficient amount
        if p2p_wallet.available_balance < amount:
            raise ValueError("Insufficient available balance")

        # update the p2p-wallet
        WalletService.repo.update_wallet_balance(p2p_wallet, -amount, 0)

        #create transaction
        WalletService.repo.create_transaction(
            p2p_wallet, None, TransactionType.WITHDRAWAL, -amount
        )

        # update the main-wallet through the service at the main
        MainWalletService.deposit(user_id, currency, amount)

        return p2p_wallet


# ================MAIN_DASHBOARD WALLET SERVICE CLASS ================


class MainWalletService:

    @staticmethod
    def get_wallet(user_id, currency):
        user = MainUser.objects.get(id=user_id)

        wallet, created = MainWallet.objects.get_or_create(
            user=user,
            currency=currency,
            defaults={'balance': 0}
        )
        return wallet

    @staticmethod
    @db_transaction.atomic
    def deposit(user_id, currency, amount):
        """add crypto to main wallet"""
        wallet = MainWalletService.get_wallet(user_id, currency)

        wallet.balance += Decimal(str(amount))
        wallet.save()

        # create transaction for the main wallet
        MainTransaction.objects.create(
            wallet=wallet,
            transaction_type='DEPOSIT',
            amount=amount
        )

        return wallet

    @staticmethod
    @db_transaction.atomic
    def withdraw(user_id, currency, amount):
        """take crypto from the main wallet"""
        wallet = MainWalletService.get_wallet(user_id, currency)

        if wallet.balance < amount:
            raise ValueError("Insufficient balance")

        wallet.balance -= Decimal(str(amount))
        wallet.save()

        # save the transaction
        MainTransaction.objects.create(
            wallet=wallet,
            transaction_type='WITHDRAWAL',
            amount=-amount
        )

        return wallet

    @staticmethod
    def get_balance(user_id, currency):
        """get the main wallet balance"""
        wallet = MainWalletService.get_wallet(user_id, currency)
        return wallet.balance

'''