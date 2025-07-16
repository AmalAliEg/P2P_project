# p2p_trading/repositories/p2p_offer_repository.py

from ..constants.constant import OfferStatus
from ..models.p2p_offer_model import P2POffer
from ..models.p2p_profile_models import  P2PProfile

# ================ HELPER MACROS ================
from ..helpers import (get_or_404,
                       get_or_403,
                       apply_filters)

# ================ REPOSITORY CLASS ================
class P2POfferRepository:
    # Base queries
    BASE_QUERY = P2POffer.objects.filter(is_deleted=False)
    PUBLIC_QUERY = BASE_QUERY.filter(status=OfferStatus.ACTIVE, available_amount__gt=0)

    @staticmethod
    def create_offer(data):
        """create new offer """
        return P2POffer.objects.create(**data)

    @staticmethod
    def get_by_id(offer_id):
        """جلب عرض بالـ ID"""
        return get_or_404(P2POffer, "Offer not found.", pk=offer_id, is_deleted=False)

    @staticmethod
    def get_by_id_and_owner(user_id, offer_id):
        """جلب عرض مع التحقق من الملكية"""
        return get_or_403(
            P2POffer,
            "Offer not found or you do not have permission to access it.",
            pk=offer_id, user_id=user_id, is_deleted=False
        )

    @staticmethod
    def get_offer_with_profile(offer_id):
        """جلب العرض مع بروفايل المعلن"""
        offer = P2POfferRepository.get_by_id(offer_id)
        # إضافة البروفايل كـ attribute
        offer.user_profile = P2PProfile.objects.filter(user_id=offer.user_id).first()
        return offer

    @staticmethod
    def get_by_user_and_filters(user_id, filters):
        """جلب عروض المستخدم مع الفلاتر"""
        queryset = P2POfferRepository.BASE_QUERY.filter(user_id=user_id)
        queryset = apply_filters(queryset, filters)
        return queryset.order_by('-created_at')

    @staticmethod
    def get_public_offers(filters):
        """get the public offere according to the filters"""
        queryset = P2POfferRepository.PUBLIC_QUERY
        queryset = apply_filters(queryset, filters)

        # order according to the price
        trade_type = filters.get('trade_type', '').upper()
        order_by = '-price' if trade_type == 'BUY' else 'price'

        return queryset.order_by(order_by)

    @staticmethod
    def update_offer(offer, data):
        """تحديث العرض"""
        # تحديث الحقول
        for field, value in data.items():
            setattr(offer, field, value)
        offer.save()
        return offer

    @staticmethod
    def soft_delete(offer):
        """حذف soft مع الاحتفاظ بالبيانات"""
        offer.is_deleted = True
        offer.status = OfferStatus.INACTIVE
        offer.save(update_fields=['is_deleted', 'status'])
        return offer

    @staticmethod
    def get_payment_methods_details(payment_ids):
        """get the details of the payment method fro the  main_db"""
        if not payment_ids:
            return {}

        try:
            from MainDashboard.models import PaymentMethods
            payment_methods = PaymentMethods.objects.using('main_db').filter(
                id__in=payment_ids
            ).values('id', 'type', 'holder_name', 'number', 'payment_method_id')

            payment_map = {}
            for pm in payment_methods:
                display_name = pm['type'] or 'Unknown'
                if pm.get('holder_name'):
                    display_name = f"{pm['type']} ({pm['holder_name']})"
                elif pm.get('number') and len(pm['number']) > 4:
                    display_name = f"{pm['type']} (****{pm['number'][-4:]})"

                payment_map[pm['id']] = {
                    'id': pm['id'],
                    'type': pm['type'],
                    'display_name': display_name,
                    'payment_method_id': pm.get('payment_method_id')
                }
            return payment_map
        except Exception as e:
            print(f"Error fetching payment methods: {str(e)}")
            return {}

