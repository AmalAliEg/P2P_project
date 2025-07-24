# p2p_trading/helpers/validation_helpers.py

from decimal import Decimal
from rest_framework.exceptions import ValidationError
from ..constants.constant import TradeType, OfferStatus, PriceType
from ..helpers.p2p_macro_helpers  import get_decimal

# ================ HELPER MACROS OFFER SERVICE================

"""*************************************************************************************************************
/*	function name:		    validate_and_raise
* 	function inputs:	    condition: take any condition like "not serializer.is_valid()" 
* 	function outputs:	    error_message 
* 	function description:	validate the condition and send back the reason of error with message
*   call back:              ValidationError() from rest.framework library
*/
*************************************************************************************************************"""
def validate_and_raise(condition, error_message, field=None):
    if condition:
        #if there field show the parameter cause error  with error message
        error = {field: error_message} if field else error_message
        raise ValidationError(error)

def validate_payment_methods(payment_ids):
    """validate payment methods format"""
    if not payment_ids:
        return True

    if not isinstance(payment_ids, list):
        raise ValidationError('payment_method_ids must be a list')

    for pid in payment_ids:
        if not isinstance(pid, int) or pid <= 0:
            raise ValidationError(f'Invalid payment method ID format: {pid}')

    return True

class OfferValidator:
    """set of validations for the offer validator"""

    @staticmethod
    def validate_price_limits(data):
        """check over the price limit """
        #validate if the price is floating
        if data.get('price_type') != PriceType.FIXED:
            return

        #casting values to decimal
        total_amount = get_decimal(data.get('total_amount'))
        price = get_decimal(data.get('price'))
        max_limit = get_decimal(data.get('max_order_limit'))
        #get the total amount in fiat
        total_fiat_value = total_amount * price
        #validate that the user add the logical max. amount
        validate_and_raise(
            max_limit > total_fiat_value,
            f'Maximum order limit ({max_limit}) cannot exceed the total offer value ({total_fiat_value:.2f} {data["fiat_currency"]})',
            'max_order_limit'
        )


    @staticmethod
    def validate_balance_for_sell(user_id, data):
        """method to check that the seller has the suffient crypto amount in his wallet
        args:
            - user_id: user id
            - data: user data
        return:
            True or error-message
        """

        from ..services.p2p_wallet_service import WalletService
        #if the trade type is BUY no need to validate it mean that the user is buyer, will pay fiat
        if data.get('trade_type') != TradeType.SELL:
            return
        #get the data from the wallet of the user since he is the seller
        wallet = WalletService.get_or_create_wallet(user_id,
                                                    data.get('crypto_currency')
                                                    )
        #get the total amount added by the user
        amount = Decimal(str(data.get('total_amount',0)))
        if wallet.balance < amount:
            validate_and_raise(wallet.balance < amount,
                               f'your balance WalletService.get_or_create_wallet {data.get('crypto_currency')} it less than the total amount {amount}'
                               )


    """*************************************************************************************************************
    /*	function name:		    validate_offer_update
    * 	function inputs:	    offer object, user id , validated data
    * 	function outputs:	    True or error-message
    * 	function description:	validate over the user, offer status 
    *   call back:              n/a 
    */
    *************************************************************************************************************"""
    @staticmethod
    def validate_offer_update(offer, data):

        # if the status of the offer is completed, rais error
        validate_and_raise(
            offer.status == OfferStatus.COMPLETED,
            "Cannot update a completed offer. Please create a new one."
        )

        # validate that the total amount not less than sold_amount
        if 'total_amount' in data and data['total_amount'] < offer.total_amount:
            sold_amount = offer.total_amount - offer.available_amount
            validate_and_raise(
                data['total_amount'] < sold_amount,
                f"Cannot reduce total amount below sold amount ({sold_amount})"
            )


    """*************************************************************************************************************
    /*	function name:		    validate_offer_deletion
    * 	function inputs:	    offer object
    * 	function outputs:	    True or error-message
    * 	function description:	check if there are active orders 
    *   call back:              n(), 
    */
    *************************************************************************************************************"""
    @staticmethod
    def validate_offer_deletion(offer):
        if offer.available_amount < offer.total_amount:
            sold = offer.total_amount - offer.available_amount
            validate_and_raise(
                True,
                f"Cannot delete offer with active trades. {sold} already sold."
            )


