#p2p_trading/helpers/decorator_helpers.py

import traceback
from functools import wraps
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from .p2p_response_helper import error_response

# ================ HELPER MACROS OFFER CONTROLLERS================

def handle_exception(func):
    """Decorator to deal with errors"""
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        try:
            return func(self, request, *args, **kwargs)
        except ValidationError as e:
            print(f"Validation Error in {func.__name__}: {e.detail}")
            return error_response(e.detail, status.HTTP_400_BAD_REQUEST)
        except NotFound as e:
            return error_response(str(e), status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return error_response(str(e), status.HTTP_403_FORBIDDEN)
        except Exception as e:
            print(f"Unexpected Error in {func.__name__}: {str(e)}")
            traceback.print_exc()
            return error_response(
                "An unexpected server error occurred",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                details=str(e) if request.GET.get('debug') else None
            )
    return wrapper