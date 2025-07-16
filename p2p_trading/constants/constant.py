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











'''wait to know its imporatnce '''
'''
# Payment method types

PAYMENT_METHOD_TYPES = [
    ('INSTAPAY', 'InstaPay'),
    ('BANK_TRANSFER', 'Bank Transfer'),
    ('VODAFONE_CASH', 'Vodafone Cash'),
    ('ORANGE_CASH', 'Orange Cash'),
    ('ETISALAT_CASH', 'Etisalat Cash'),
    ('WE_PAY', 'WE Pay'),
]


'''
'''


    class TradeType(models.TextChoices):
        BUY = 'BUY', 'Buy'   # user أنا كصاحب عرض "أريد شراء" كريبتو
    SELL = 'SELL', 'Sell' # أنا كصاحب عرض "أريد بيع" كريبتو

class PriceType(models.TextChoices):
    FIXED = 'FIXED', 'Fixed'
    FLOATING = 'FLOATING', 'Floating'

class OfferStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Online'     # العرض ظاهر للجميع
    INACTIVE = 'INACTIVE', 'Offline' # العرض غير ظاهر (أو تم إيقافه)
    PRIVATE = 'PRIVATE', 'Private'   # العرض متاح لأشخاص محددين (ميزة متقدمة)
    COMPLETED = 'COMPLETED', 'Completed'


class OrderStatus(models.TextChoices):
    UNPAID = 'UNPAID', 'Unpaid'                 # المشتري لم يدفع بعد
    PAID = 'PAID', 'Paid'                       # المشتري قام بالدفع وينتظر البائع
    APPEAL = 'APPEAL', 'Appeal in Progress'     # هناك نزاع على الطلب
    COMPLETED = 'COMPLETED', 'Completed'        # تم إتمام الصفقة بنجاح
    CANCELED = 'CANCELED', 'Canceled'           # تم إلغاء الطلب


class TransactionType(models.TextChoices):
    DEPOSIT = 'DEPOSIT', 'Deposit'
    WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'
    LOCK_ESCROW = 'LOCK_ESCROW', 'Lock for Escrow'       # تجميد أموال البائع
    RELEASE_ESCROW = 'RELEASE_ESCROW', 'Release from Escrow' # إرسال الأموال للمشتري
    CANCEL_ESCROW = 'CANCEL_ESCROW', 'Cancel Escrow'       # إعادة الأموال للبائع
    TRADE_FEE = 'TRADE_FEE', 'Trade Fee'               # رسوم العملية

'''
