# p2p_trading/controllers/p2p_wallet_controller.py

from rest_framework import status, viewsets
from rest_framework.decorators import action

from ..serializers.p2p_wallet_serializer import WalletBalanceSerializer
from ..services.p2p_wallet_service import WalletService


# ================ HELPER MACROS ================

from ..helpers import (
    GET_CURRENCY,
    handle_exception,
    success_response,

)
from ..decorator.swagger_decorator import swagger_serializer_mapping

# ================CONTROLLER CLASS ================


@swagger_serializer_mapping(
    transfer_in='WalletBalanceSerializer',

)
class P2PWalletController(viewsets.ViewSet):

    @action(detail=False, methods=['get'], url_path='wallet-balance')
    @handle_exception
    def wallet_balance(self, request):
        """get the wallet-balance for the P2P"""
        wallet = WalletService.get_or_create_wallet(
            user_id=request.user.id,
            currency=GET_CURRENCY(request)
        )

        serializer = WalletBalanceSerializer(wallet)
        return success_response(serializer.data)





'''
    @action(detail=False, methods=['post'], url_path='transfer-in')
    @handle_exception
    def transfer_in(self, request):
        """from main wallet to  P2P-wallet"""
        currency = request.data.get('currency', 'USDT')
        amount = GET_AMOUNT(request.data)

        if not VALIDATE_AMOUNT(amount):
            return error_response("Invalid amount", status.HTTP_400_BAD_REQUEST)

        wallet = WalletService.transfer_from_main_wallet(
            user_id=request.user.id,
            currency=currency,
            amount=amount
        )

        return success_response({
            "message": f"Successfully transferred {amount} {currency}",
            "new_balance": str(wallet.balance)
        })

'''



