"""*************************************************************************************************************
                                                file Card
*	project name:			P2P_trading.py
*	file name:			    wallet_model.py
*	project description:	set the implementation of the wallet model for this project
*  start date:				Jul 14, 2025
*  Author: 				    Eng. Amal Aly
*************************************************************************************************************"""

# p2p_trading/models/wallet_model.py
from django.db import models

from .p2p_BaseModel import BaseModel

'''ths for the virtual wallet that used to transfere the amount and apply escrow '''


class Wallet(BaseModel):
    user_id = models.IntegerField(db_index=True)
    #the crypto amount
    currency = models.CharField(max_length=10)
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    locked_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)

    class Meta:
        # each user has only one wallet
        db_table = 'p2p_wallet'
        app_label = 'p2p_trading'
        unique_together = ('user_id', 'currency')



    @property
    def available_balance(self):
        """balance = total amount - locked_balance"""
        return self.balance - self.locked_balance

    def __str__(self):
        return f"{self.user_id.username}'s {self.currency} Wallet"

