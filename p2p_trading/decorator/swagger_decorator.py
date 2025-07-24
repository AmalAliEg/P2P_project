# p2p_trading/decorators/swagger_decorator.py

def swagger_serializer_mapping(**serializer_map):
    """
    Decorator to add serializer mapping for Swagger/Spectacular
    """
    def decorator(cls):
        # Dynamic import based on controller type
        controller_name = cls.__name__

        # Import the appropriate serializer module
        if 'Offer' in controller_name:
            from p2p_trading.serializers import p2p_offer_serilaizer as serializer_module
        elif 'Order' in controller_name:
            from p2p_trading.serializers import p2p_order_serializer as serializer_module
        elif 'Profile' in controller_name:
            from p2p_trading.serializers import p2p_profile_serializer as serializer_module
        elif 'Wallet' in controller_name:
            from p2p_trading.serializers import p2p_wallet_serializer as serializer_module
        else:
            # Default fallback
            from p2p_trading.serializers import p2p_offer_serilaizer as serializer_module

        # Set serializer_class for basic swagger detection
        if 'create' in serializer_map:
            serializer_class = getattr(serializer_module, serializer_map['create'], None)
            if serializer_class:
                cls.serializer_class = serializer_class

        # Add method to get serializer based on action
        def get_serializer_class(self):
            action = getattr(self, 'action', None)
            if action and action in serializer_map:
                serializer_name = serializer_map[action]
                return getattr(serializer_module, serializer_name, None)
            return getattr(self, 'serializer_class', None)

        cls.get_serializer_class = get_serializer_class
        return cls

    return decorator