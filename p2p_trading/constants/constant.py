# p2p_trading/constants.py

from django.db import models


class TradeType(models.TextChoices):
    BUY = 'BUY', 'Buy'  # user wanna buy
    SELL = 'SELL', 'Sell'  # user wanna sell


class PriceType(models.TextChoices):
    FIXED = 'FIXED', 'Fixed'
    FLOATING = 'FLOATING', 'Floating'


class OfferStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Online'  # offer for everyone
    INACTIVE = 'INACTIVE', 'Offline'  # offer is disabled
    PRIVATE = 'PRIVATE', 'Private'  # offer for user's followers or specific people only
    COMPLETED = 'COMPLETED', 'Completed'


class OrderStatus(models.TextChoices):
    UNPAID = 'UNPAID', 'Unpaid'  # seller didn't paid yet
    PAID = 'PAID', 'Paid'  # seller paid and wait the buyer
    APPEAL = 'APPEAL', 'Appeal in Progress'  # there a problem
    COMPLETED = 'COMPLETED', 'Completed'  # deal is successfully done
    CANCELLED = 'CANCELLED', 'Cancelled'  # order canceled


class TransactionType(models.TextChoices):
    DEPOSIT = 'DEPOSIT', 'Deposit'
    WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'
    LOCK_ESCROW = 'LOCK_ESCROW', 'Lock for Escrow'  # freeze the currencies
    RELEASE_ESCROW = 'RELEASE_ESCROW', 'Release from Escrow'  # send the currencies to the seller
    CANCEL_ESCROW = 'CANCEL_ESCROW', 'Cancel Escrow'  # return the currencies back to buyer
    TRADE_FEE = 'TRADE_FEE', 'Trade Fee'  # trade fees


STATUS_MAP = {
    'UNPAID': {'text': 'Unpaid', 'class': 'warning'},
    'PAID': {'text': 'Paid', 'class': 'info'},
    'COMPLETED': {'text': 'Completed', 'class': 'success'},
    'CANCELLED': {'text': 'Cancelled', 'class': 'danger'},
    'APPEAL': {'text': 'Appeal In Progress', 'class': 'danger'}
}


# Order Status Groups
PROCESSING_STATUSES = ['UNPAID', 'PAID', 'APPEAL']
COMPLETED_STATUSES = ['COMPLETED', 'CANCELLED']




