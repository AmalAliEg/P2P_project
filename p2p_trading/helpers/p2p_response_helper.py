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
    """to detect the error and return an error response"""
    response = {"success": False, "error": str(error)}
    if details:
        response["details"] = details
    return Response(response, status=status_code)

# ================ HELPER MACROS ORDER CONTROLLERS================
# Response formatters
ORDER_RESPONSE = lambda order, msg: {"order_id": str(order.id), "status": order.status, "message": msg}


# ================ HELPER MACROS PROFILE CONTROLLERS================
FORMAT_MY_FEEDBACK = lambda feedback: {
    "id": feedback.id,
    "order_id": feedback.order.id,
    "my_feedback": feedback.comment,
    "my_rating": "positive" if feedback.is_positive else "negative",
    "submitted_at": feedback.created_at
} if feedback else None

FORMAT_THEIR_FEEDBACK = lambda feedback: {
    "id": feedback.id,
    "order_id": feedback.order.id,
    "reviewer_nickname": feedback.reviewer.nickname,
    "counterparty_feedback": feedback.comment,
    "their_rating": "positive" if feedback.is_positive else "negative",
    "submitted_at": feedback.created_at
} if feedback else None

ORDER_FEEDBACK_RESPONSE = lambda order_id, my_feedback, their_feedback: {
    "order_id": str(order_id),
    "my_feedback": FORMAT_MY_FEEDBACK(my_feedback),
    "counterparty_feedback": FORMAT_THEIR_FEEDBACK(their_feedback)
}
