# p2p_trading/decorators/swagger_decorator.py

def swagger_serializer_mapping(**serializer_map):
    """
    Decorator to add serializer mapping for Swagger/Spectacular
    Usage:
    @swagger_serializer_mapping(
        create='P2POfferCreateSerializer',
        list='P2POfferListSerializer',
        retrieve='P2POfferDetailSerializer',
        update='OfferStatusUpdateSerializer'
    )
    """
    def decorator(cls):
        # Import serializers dynamically
        from p2p_trading.serializers import p2p_offer_serilaizer

        # Set serializer_class for basic swagger detection
        if 'create' in serializer_map:
            cls.serializer_class = getattr(p2p_offer_serilaizer, serializer_map['create'])

        # Add method to get serializer based on action
        def get_serializer_class(self):
            action = getattr(self, 'action', None)
            if action and action in serializer_map:
                serializer_name = serializer_map[action]
                return getattr(p2p_offer_serilaizer, serializer_name)
            return getattr(self, 'serializer_class', None)

        cls.get_serializer_class = get_serializer_class
        return cls

    return decorator