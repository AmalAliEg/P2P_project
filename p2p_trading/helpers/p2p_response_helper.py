# p2p_trading/helpers/response_helpers.py

from rest_framework import status
from rest_framework.response import Response

# ================ HELPER MACROS OFFER CONTROLLERS================
def success_response(data=None, message=None, count=None, status_code=status.HTTP_200_OK):
    """if the response is success """
    response = {"success": True}
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    if count is not None:
        response["count"] = count
    return Response(response, status=status_code)

def error_response(error, status_code=status.HTTP_400_BAD_REQUEST, details=None):
    """Macro للاستجابات الخاطئة"""
    response = {"success": False, "error": str(error)}
    if details:
        response["details"] = details
    return Response(response, status=status_code)

# ================ HELPER MACROS ORDER CONTROLLERS================
# Response formatters
ORDER_RESPONSE = lambda order, msg: {"order_id": str(order.id), "status": order.status, "message": msg}
