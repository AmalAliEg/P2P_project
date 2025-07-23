# p2p_trading/models/p2p_order_model.py
"""this model for the orders """

from django.db import models
from .p2p_offer_model import P2POffer
from .p2p_BaseModel import BaseModel
from ..constants.constant import OrderStatus

class P2POrder(BaseModel):
    order_number = models.CharField(max_length=20, unique=True) # رقم تسلسلي للطلب

    # order's counterparties
    offer = models.ForeignKey(P2POffer, on_delete=models.PROTECT, related_name='orders')
    maker_id = models.IntegerField(db_index=True)   #creator of the offer
    taker_id = models.IntegerField(db_index=True)   #who take or accept the offer

    # order's attr
    status = models.CharField(max_length=10, choices=OrderStatus.choices, default=OrderStatus.UNPAID)
    trade_type = models.CharField(max_length=4) # 'BUY' or 'SELL' change according to taker
    crypto_currency = models.CharField(max_length=10)
    fiat_currency = models.CharField(max_length=10)
    price = models.DecimalField(max_digits=20, decimal_places=2)
    crypto_amount = models.DecimalField(max_digits=20, decimal_places=8)
    fiat_amount = models.DecimalField(max_digits=20, decimal_places=2)

    # necessary for pnl)
    transaction_fee = models.DecimalField(max_digits=20, decimal_places=8, default=0)

    # time
    payment_time_limit=models.DateTimeField()
    chat_room_id = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'p2p_order'
        app_label = 'p2p_trading'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(crypto_amount__gt=0),
                name='order_crypto_amount_positive'
            ),
            models.CheckConstraint(
                check=models.Q(fiat_amount__gt=0),
                name='order_fiat_amount_positive'
            ),
            models.CheckConstraint(
                check=models.Q(price__gt=0),
                name='order_price_positive'
            ),
            models.CheckConstraint(
                check=~models.Q(maker_id=models.F('taker_id')),
                name='maker_taker_different'
            ),
            models.CheckConstraint(
                check=models.Q(transaction_fee__gte=0),
                name='transaction_fee_non_negative'
            ),
        ]


    #create unique order_numbere
    def save(self, *args, **kwargs):
        if not self.order_number:
            import time
            self.order_number = f"{int(time.time() * 1000)}"[-12:]
        super().save(*args, **kwargs)

