# p2p_trading/services/p2p_offer_service.py

from django.db import transaction

from ..repositories.p2p_offer_repository import P2POfferRepository
from ..repositories.p2p_profile_repository import P2PProfileRepository
from ..serializers.p2p_offer_serilaizer import P2POfferCreateSerializer


# ================ HELPER MACROS ================
from ..helpers import (
    validate_and_raise,
    validate_payment_methods,
    OfferValidator,
    enrich_offers_with_profiles
)
# ================ SERVICE CLASS ================
class P2POfferService:
    repo = P2POfferRepository()  # Repository instance مشترك

    @staticmethod
    @transaction.atomic
    def create_offer(user_id, data):
        """إنشاء عرض جديد"""
        # 1. Validate input
        serializer = P2POfferCreateSerializer(data=data)
        validate_and_raise(not serializer.is_valid(), serializer.errors)

        validated_data = serializer.validated_data

        # 2. Business validations
        OfferValidator.validate_price_limits(validated_data)
        P2PProfileRepository.validate_payment_methods_ownership(
            user_id,
            validated_data.get('payment_method_ids', [])
        )

        OfferValidator.validate_balance_for_sell(user_id, validated_data)

        # 3. Prepare data
        validated_data.update({
            'user_id': user_id,
            'available_amount': validated_data['total_amount']
        })

        # 4. Create offer
        return P2POfferService.repo.create_offer(validated_data)

    @staticmethod
    def get_user_offers(user_id, filters=None):
        """get all the offers of the user """
        return P2POfferService.repo.get_by_user_and_filters(user_id, filters or {})

    @staticmethod
    def get_offer_detail(user_id, offer_id):
        """get details of specifc offer"""
        return P2POfferService.repo.get_offer_with_profile(offer_id)

    @staticmethod
    @transaction.atomic
    def update_offer(user_id, offer_id, data):
        """تحديث العرض"""
        offer = P2POfferService.repo.get_by_id(offer_id)
        OfferValidator.validate_offer_update(offer, user_id, data)
        return P2POfferService.repo.update_offer(offer, data)

    @staticmethod
    @transaction.atomic
    def delete_offer(user_id, offer_id):
        """حذف العرض"""
        offer = P2POfferService.repo.get_by_id_and_owner(user_id, offer_id)
        OfferValidator.validate_offer_deletion(offer)
        return P2POfferService.repo.soft_delete(offer)

    @staticmethod
    def get_public_offers(filters):
        """get the public offers for all users """
        clean_filters = {k: v for k, v in filters.items() if v}
        offers = P2POfferService.repo.get_public_offers(clean_filters)
        return enrich_offers_with_profiles(offers, P2PProfileRepository.get_profiles_by_user_ids)

    @staticmethod
    def get_payment_methods_for_offers(offers):
        """get the details of the payment method """
        # جمع كل الـ payment IDs
        all_payment_ids = []
        for offer in offers:
            if offer.payment_method_ids:
                all_payment_ids.extend(offer.payment_method_ids)

        # remove the repeats
        unique_ids = list(set(all_payment_ids))

        # get the details from repository
        return P2POfferRepository.get_payment_methods_details(unique_ids)

    @staticmethod
    def get_payment_methods_for_single_offer(offer):
        """جلب تفاصيل طرق الدفع لعرض واحد"""
        if not offer.payment_method_ids:
            return {}
        return P2POfferRepository.get_payment_methods_details(offer.payment_method_ids)





'''
# p2p_trading/services/p2p_offer_service.py
from django.db import transaction
from decimal import Decimal
from rest_framework.exceptions import ValidationError, PermissionDenied
from ..repositories.p2p_offer_repository import P2POfferRepository
from ..serializers.p2p_offer_serilaizer import P2POfferCreateSerializer
from ..constants.constant import TradeType, OfferStatus, PriceType
from MainDashboard.models import PaymentMethods


class P2POfferService:

    @staticmethod
    @transaction.atomic
    def create_offer( user_id, data):
        serializer = P2POfferCreateSerializer(data=data)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        validated_data = serializer.validated_data
        # 2. Perform business logic validations

        # --- THIS IS THE CORRECTED LOGIC ---
        # Calculate the total value of the offer in FIAT currency.
        # Note: This is only applicable for FIXED price type
        if validated_data.get('price_type') == PriceType.FIXED:
            # إجمالي قيمة العرض بالعملة المحلية = الكمية × السعر
            total_fiat_value = Decimal(str(validated_data['total_amount'])) * Decimal(str(validated_data['price']))

            # التحقق من أن الحد الأقصى للطلب لا يتجاوز القيمة الإجمالية للعرض
            if Decimal(str(validated_data['max_order_limit'])) > total_fiat_value:
                raise ValidationError({
                    'max_order_limit': f'Maximum order limit ({validated_data["max_order_limit"]}) cannot exceed the total offer value ({total_fiat_value:.2f} {validated_data["fiat_currency"]})'
                })
            # 3. Validate payment methods exist in main database
        payment_ids = validated_data.get('payment_method_ids', [])

        if payment_ids:
            # Check if all payment methods exist in the main database
            valid_methods_count = PaymentMethods.objects.using('main_db').filter(
                pk__in=payment_ids
            ).count()

            if valid_methods_count != len(payment_ids):
                raise ValidationError({
                    'payment_method_ids': 'One or more payment methods are invalid or do not exist.'
                })

        # 4. Handle trade-type specific logic
        if validated_data['trade_type'] == TradeType.SELL:
            # TODO: Add balance check logic here when wallet service is available
            # Example:
            # user_balance = WalletService.get_user_crypto_balance(user_id, validated_data['crypto_currency'])
            # if user_balance < validated_data['total_amount']:
            #     raise ValidationError({'total_amount': 'Insufficient balance to create this sell offer.'})
            pass

        # 5. Prepare data for repository
        # Add user_id to the data
        validated_data['user_id'] = user_id

        # Set available_amount equal to total_amount for new offers
        validated_data['available_amount'] = validated_data['total_amount']

        # 6. Create the offer using repository
        offer = P2POfferRepository.create_offer(data=validated_data)

        return offer


    @staticmethod
    def get_user_offers(user_id, filters=None):
        """Get all offers for a specific user with optional filters"""
        if filters is None:
            filters = {}

        # استدعاء Repository
        return P2POfferRepository.get_by_user_and_filters(
            user_id=user_id,
            filters=filters
        )


    @staticmethod
    def update_offer(user_id, offer_id, data):
        """Update offer status (activate/deactivate)"""
        # الحصول على العرض من قاعدة البيانات
        repo = P2POfferRepository()

        # تصحيح: استخدام دالة موجودة
        offer = repo.get_by_id(offer_id)

        # التحقق من أن المستخدم هو صاحب العرض
        if offer.user_id != user_id:
            raise PermissionDenied("You don't have permission to update this offer")

        # منع تعديل العروض المكتملة فقط
        if offer.status == OfferStatus.COMPLETED:
            raise ValidationError("Cannot update a completed offer. Please create a new one.")

        # إذا كان التعديل يشمل تقليل الكمية
        if 'total_amount' in data and data['total_amount'] < offer.total_amount:
        # التأكد من أن الكمية الجديدة لا تقل عن المباع
            sold_amount = offer.total_amount - offer.available_amount
        if data['total_amount'] < sold_amount:
            raise ValidationError(f"Cannot reduce total amount below sold amount ({sold_amount})")


        # استخدام Repository للتحديث
        return repo.update_offer(offer=offer, data=data)

    @staticmethod
    def get_offer_detail(user_id, offer_id):
        repo = P2POfferRepository()
        # استخدام Repository method فقط
        offer = repo.get_offer_with_profile(offer_id=offer_id)
        return offer


    @staticmethod
    def delete_offer( user_id, offer_id):
        repo = P2POfferRepository()

    # استخدم get_by_id_and_owner للتحقق من الصلاحيات مباشرة
        offer = repo.get_by_id_and_owner(user_id=user_id, offer_id=offer_id)

        # منع حذف العروض النشطة التي بها صفقات
        if offer.available_amount < offer.total_amount:
            sold = offer.total_amount - offer.available_amount
            raise ValidationError(f"Cannot delete offer with active trades. {sold} already sold.")

        # soft delete
        return repo.soft_delete(offer)



    @staticmethod
    def get_public_offers(filters):
        """جلب العروض العامة مع معلومات المعلنين"""
        repo = P2POfferRepository()

        # إزالة القيم الفارغة من الفلاتر
        clean_filters = {k: v for k, v in filters.items() if v}

        # جلب العروض
        offers = repo.get_public_offers(filters=clean_filters)

        # جمع معرفات المستخدمين
        user_ids = list(offers.values_list('user_id', flat=True).distinct())

        # جلب بروفايلات المعلنين
        from ..models.p2p_profile_models import P2PProfile
        profiles = P2PProfile.objects.filter(user_id__in=user_ids)
        profiles_map = {profile.user_id: profile for profile in profiles}

        # إضافة البروفايل لكل عرض
        for offer in offers:
            offer.user_profile = profiles_map.get(offer.user_id)

        return offers


'''
'''

    @staticmethod
    def get_available_payment_methods( user_id):
        pass


'''



















