# p2p_trading/helpers/filter_helpers.py
from django.db.models import Q

from ..helpers.p2p_macro_helpers import  parse_date

# ================ HELPER MACROS OFFER CONTROLLERS================

"""*************************************************************************************************************
/*	function name:		    extract_filters
* 	function inputs:	    query_params from request, list of filter_keys 
* 	function outputs:	    dict of the filter_keys with values from the query_params
* 	function description:	create dict of filters according to specific key if exist 
*   call back:              n/a
*/
*************************************************************************************************************"""
def extract_filters(query_params, filter_keys):
    return {k: query_params.get(k) for k in filter_keys if query_params.get(k)}

# ================ HELPER MACROS OFFER REPOSITORY================

FILTER_MAPPING = {
    'status': lambda v, q: q.filter(status=v.upper()),
    'type': lambda v, q: q.filter(trade_type=v.upper()),
    'asset_type': {
        'Normal': lambda q: q.filter(crypto_currency__in=['USDT', 'USDC']),
        'Cash': lambda q: q.filter(crypto_currency__in=['USDT', 'USDC']),
        'Block': lambda q: q.filter(crypto_currency__in=['USDT', 'USDC']),
        'Fiat': lambda q: q.filter(crypto_currency__in=['USDT', 'USDC'])

    },
    'trade_type': lambda v, q: q.filter(trade_type=v.upper()),
    'crypto_currency': lambda v, q: q.filter(crypto_currency=v.upper()),
    'fiat_currency': lambda v, q: q.filter(fiat_currency=v),
    'payment_method': lambda v, q: q.filter(payment_method_ids__contains=v)
}

# ================ HELPER MACROS ORDER REPOSITORY================

# Macros for common patterns
USER_FILTER = lambda user_id: Q(maker_id=user_id) | Q(taker_id=user_id)


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



"""*************************************************************************************************************
/*	function name:		    apply_filters
* 	function inputs:	    queryset of the active offers from the user, filters
* 	function outputs:	    queryset/records/objects of the filtered active offers from the user
* 	function description:	filter the queryset of the active offers
*   call back:              parse_date()
*/
*************************************************************************************************************"""
def apply_filters(queryset, filters):
    #this loop to check if the value exist, each loop check 1 pair
    for key, value in filters.items():
        #null, none, 0, false
        if not value:
            continue

        # edit the date
        if key == 'start_date':
            date = parse_date(value)
            if date:
                #get all the records date >= to date send by filter
                queryset = queryset.filter(created_at__gte=date)
        elif key == 'end_date':
            date = parse_date(value, end_of_day=True)
            if date:
                #get all the records date <= to date send by filter
                queryset = queryset.filter(created_at__lte=date)
        # specific filters
        elif key in FILTER_MAPPING:
            #add the value of the key, if key exist in the  FILTER_MAPPING dic.
            filter_func = FILTER_MAPPING[key]
            #validate if the filter_func is dict or regulare function
            if isinstance(filter_func, dict):
                #if the value exist
                if value in filter_func:
                    queryset = filter_func[value](queryset)
            else:

                queryset = filter_func(value, queryset)

    return queryset

def apply_order_filters(queryset, filters):
    """"""
    for key, filter_func in ORDER_FILTER_MAP.items():
        if key in filters:
            queryset = filter_func(queryset, filters.get(key))
    return queryset
