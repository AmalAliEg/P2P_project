# p2p_trading/helpers/filter_helpers.py
from django.db.models import Q

from ..helpers.p2p_macro_helpers import  parse_date

# ================ HELPER MACROS OFFER CONTROLLERS================

def extract_filters(query_params, filter_keys):
    """Helper got filter query parameters"""
    return {k: query_params.get(k) for k in filter_keys if query_params.get(k)}

# ================ HELPER MACROS OFFER REPOSITORY================
FILTER_MAPPING = {
    'status': lambda v, q: q.filter(status=v.upper()),
    'type': lambda v, q: q.filter(trade_type=v.upper()),
    'asset_type': {
        'Normal': lambda q: q.exclude(crypto_currency__in=['USDT', 'USDC']),
        'Cash': lambda q: q.filter(crypto_currency__in=['USDT', 'USDC'])
    },
    'trade_type': lambda v, q: q.filter(trade_type=v.upper()),
    'crypto_currency': lambda v, q: q.filter(crypto_currency=v.upper()),
    'fiat_currency': lambda v, q: q.filter(fiat_currency=v),
    'payment_method': lambda v, q: q.filter(payment_method_ids__contains=v)
}

# ================ HELPER MACROS ORDER REPOSITORY================

# Macros for common patterns
USER_FILTER = lambda user_id: Q(maker_id=user_id) | Q(taker_id=user_id)
BUY_FILTER = lambda user_id: Q(trade_type='SELL', taker_id=user_id) | Q(trade_type='BUY', maker_id=user_id)
SELL_FILTER = lambda user_id: Q(trade_type='SELL', maker_id=user_id) | Q(trade_type='BUY', taker_id=user_id)


ORDER_FILTER_MAP = {
    'coin': lambda q, v: q.filter(crypto_currency=v.upper()) if v and v != 'All coins' else q,
    'order_type': lambda q, v: q.filter(trade_type=v.upper()) if v and v != 'All' else q,
    'currency': lambda q, v: q.filter(fiat_currency=v.upper()) if v and v != 'All' else q,
    'start_date': lambda q, v: q.filter(created_at__gte=v) if v else q,
    'end_date': lambda q, v: q.filter(
        created_at__lte=v.replace(hour=23, minute=59, second=59) if hasattr(v, 'replace') else v) if v else q,
    'search': lambda q, v: q.filter(order_number__icontains=v) if v else q,
    'date_from': lambda q, v: q.filter(completed_at__gte=v) if v else q,
    'date_to': lambda q, v: q.filter(completed_at__lte=v) if v else q
}


def apply_filters(queryset, filters):
    """Helper لتطبيق الفلاتر"""
    for key, value in filters.items():
        if not value:
            continue

        # معالجة التواريخ
        if key == 'start_date':
            date = parse_date(value)
            if date:
                queryset = queryset.filter(created_at__gte=date)
        elif key == 'end_date':
            date = parse_date(value, end_of_day=True)
            if date:
                queryset = queryset.filter(created_at__lte=date)
        # معالجة الفلاتر الخاصة
        elif key in FILTER_MAPPING:
            filter_func = FILTER_MAPPING[key]
            if isinstance(filter_func, dict):
                if value in filter_func:
                    queryset = filter_func[value](queryset)
            else:
                queryset = filter_func(value, queryset)

    return queryset

def apply_order_filters(queryset, filters):
    """Helper لتطبيق فلاتر الطلبات"""
    for key, filter_func in ORDER_FILTER_MAP.items():
        if key in filters:
            queryset = filter_func(queryset, filters.get(key))
    return queryset
