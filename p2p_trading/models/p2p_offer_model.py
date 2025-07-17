# p2p_trading/models/p2p_offer_model.py
from decimal import Decimal
from .p2p_BaseModel import BaseModel
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from p2p_trading.constants.constant import TradeType, PriceType, OfferStatus

class P2POffer(BaseModel):
    user_id = models.IntegerField(db_index=True)
    trade_type = models.CharField(max_length=4, choices=TradeType.choices, default=TradeType.BUY)

    # currencies and price
    crypto_currency = models.CharField(max_length=10, db_index=True)
    fiat_currency = models.CharField(max_length=10,db_index=True)
    price_type = models.CharField(max_length=10, choices=PriceType.choices, default=PriceType.FIXED)
    '''in case fixed type'''
    price = models.DecimalField(max_digits=20,
                                decimal_places=2,
                                validators=[MinValueValidator(Decimal('0.01'))],
                                help_text="Fixed price in fiat currency")
    '''in case floating type'''
    price_margin = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                       validators=[MinValueValidator(Decimal('-10')),
                                                   MaxValueValidator(Decimal('10'))],
                                       help_text="Percentage margin for floating price (e.g., 5.00 for +5%")

    # amounts and limits
    #total amount in crypto
    total_amount = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(Decimal('0.00001'))])
    #change after each order
    available_amount = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(Decimal('0'))])
    min_order_limit = models.DecimalField(max_digits=20, decimal_places=2,validators=[MinValueValidator(Decimal('0.01'))])
    max_order_limit = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])


    #payment method in the main dashboard
    '''JSONField means it can be:
    payment_method_ids = "text"
    payment_method_ids = {"key": "value"}
    payment_method_ids = []
    payment_method_ids = ["abc", "xyz"]'''
    payment_method_ids = models.JSONField(default=list)

    payment_time_limit_minutes = models.IntegerField(default=15,
                                                     validators=[MinValueValidator(5),
                                                                 MaxValueValidator(120)])

    # optional
    remarks = models.TextField(null=True, blank=True, max_length=1000)
    auto_reply_message = models.TextField(null=True, blank=True,max_length=1000)

    # restriction over the counterparty
    counterparty_min_registration_days = models.PositiveIntegerField(default=0)
    counterparty_min_holding_amount = models.DecimalField(max_digits=20, decimal_places=8, default=0)

    # status
    status = models.CharField(max_length=10, choices=OfferStatus.choices, default=OfferStatus.ACTIVE, db_index=True)

    class Meta:
        db_table = 'p2p_offer'
        app_label = 'p2p_trading'

    def __str__(self):
        return f"Offer by {self.user_id} - {self.crypto_currency}"















