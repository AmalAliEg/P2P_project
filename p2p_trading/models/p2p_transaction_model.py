# p2p_trading/models/transaction_model.py
from django.db import models

from .p2p_BaseModel import BaseModel

'''this model for the transaction actions'''
from ..constants.constant import TransactionType

class Transaction(BaseModel):
    wallet = models.ForeignKey('Wallet', on_delete=models.PROTECT, related_name='transactions')
    related_order = models.ForeignKey('P2POrder', on_delete=models.PROTECT, null=True, blank=True)
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=20, decimal_places=8) #
    running_balance = models.DecimalField(max_digits=20, decimal_places=8) # wallet balance after transaction

    class Meta:
        db_table = 'p2p_transaction_model'
        app_label = 'p2p_trading'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} {self.wallet.currency} for {self.wallet.user.username}"

