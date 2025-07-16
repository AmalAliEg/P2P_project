# MainDashboard/services.py

from django.db import transaction as db_transaction
from decimal import Decimal
from .models import MainWallet, MainTransaction

class MainWalletService:

    @staticmethod
    def get_wallet(user_id, currency):
        """الحصول على المحفظة أو إنشاؤها"""
        from .models import MainUser
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
