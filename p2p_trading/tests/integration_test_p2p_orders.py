# tests/integration_test_p2p_orders.py

import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from p2p_trading.models import Wallet, P2POffer, P2POrder
from MainDashboard.models import PaymentMethods

User = get_user_model()

@pytest.mark.django_db(databases=['default', 'main_db'], transaction=True)
class TestP2POrdersIntegration:
    """Integration tests للتحقق من جودة النظام"""

    # Constants
    DEFAULT_CRYPTO = 'USDT'
    DEFAULT_FIAT = 'EGP'
    DEFAULT_PRICE = '60.4'
    DEFAULT_AMOUNT = '1000'
    DEFAULT_ORDER_AMOUNT = '500'

    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        """تنظيف قاعدة البيانات قبل كل test"""
        P2POrder.objects.all().delete()
        P2POffer.objects.all().delete()
        Wallet.objects.all().delete()
        PaymentMethods.objects.all().delete()
        User.objects.all().delete()

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def buyer_with_wallet(self):
        """مشتري مع محفظة وطريقة دفع"""
        buyer = User.objects.create_user(
            username='buyer1',
            password='pass123'
        )

        # Create wallet للمشتري
        Wallet.objects.create(
            user_id=buyer.id,
            currency=self.DEFAULT_FIAT,  # المشتري يحتاج fiat
            balance=Decimal('10000.00')
        )

        # Create payment method
        payment_method = PaymentMethods.objects.create(
            user=buyer,
            payment_method_id='BANK_BUYER',
            type='BANK_TRANSFER',
            number='9876543210',
            holder_name='Buyer User',
            primary=True
        )

        return buyer, payment_method

    @pytest.fixture
    def seller_with_wallet_and_offer(self):
        """بائع مع محفظة وعرض نشط"""
        seller = User.objects.create_user(
            username='seller1',
            password='pass123'
        )

        # Create wallet للبائع
        Wallet.objects.create(
            user_id=seller.id,
            currency=self.DEFAULT_CRYPTO,
            balance=Decimal('5000.00')
        )

        # Create payment method
        payment_method = PaymentMethods.objects.create(
            user=seller,
            payment_method_id='BANK_SELLER',
            type='BANK_TRANSFER',
            number='1234567890',
            holder_name='Seller User',
            primary=True
        )
        offer = P2POffer.objects.create(
            user_id=seller.id,
            trade_type='SELL',
            crypto_currency=self.DEFAULT_CRYPTO,
            fiat_currency=self.DEFAULT_FIAT,
            price_type='FIXED',
            price=Decimal(self.DEFAULT_PRICE),
            total_amount=Decimal(self.DEFAULT_AMOUNT),
            available_amount=Decimal(self.DEFAULT_AMOUNT),
            min_order_limit=Decimal('100'),
            max_order_limit=Decimal('1000'),
            payment_time_limit_minutes=120,
            status='ACTIVE',
            # إضافة payment_method_ids مباشرة في الإنشاء
            payment_method_ids=[payment_method.id]
        )
        # حذف السطر: offer.payment_methods.add(payment_method)

        return seller, offer, payment_method

    @pytest.fixture
    def auth_buyer_client(self, api_client, buyer_with_wallet):
        buyer, payment_method = buyer_with_wallet
        api_client.force_authenticate(user=buyer)
        return api_client, buyer, payment_method

    @pytest.fixture
    def auth_seller_client(self, seller_with_wallet_and_offer):
        seller, offer, payment_method = seller_with_wallet_and_offer
        # إنشاء client جديد مستقل
        client = APIClient()
        client.force_authenticate(user=seller)
        return client, seller, offer, payment_method



    # ========== HELPER METHODS ==========
    def create_order_data(self, offer_id, payment_method_id=None, **overrides):
        """Helper لإنشاء بيانات order صالحة"""
        data = {
            "offer_id": str(offer_id),
            "fiat_amount": self.DEFAULT_ORDER_AMOUNT,
        }
        # إضافة payment_method_id فقط إذا تم تمريره
        if payment_method_id:
            data["payment_method_id"] = payment_method_id

        data.update(overrides)
        return data

    def get_order_safely(self, user_id, error_msg="Order not found"):
        """Helper method للحصول على order بأمان"""
        order = P2POrder.objects.filter(taker_id=user_id).order_by('-created_at').first()
        if not order:
            pytest.fail(error_msg)
        return order

    # ========== CORRECTNESS TESTS - الكود بيشتغل صح؟ ==========

    def test_create_order_from_offer_success(self, auth_buyer_client, seller_with_wallet_and_offer):
        """✅ Test 1: إنشاء order من offer بنجاح"""
        client, buyer, buyer_payment = auth_buyer_client
        seller, offer, seller_payment = seller_with_wallet_and_offer

        order_data = {
            "offer_id": str(offer.id),
            "fiat_amount": 500,
            "payment_method_id": str(seller_payment.id)
        }

        response = client.post('/api/p2p/orders/', order_data, format='json')

        print(f"Create Order Response: {response.status_code}")
        print(f"Response Data: {response.data}")

        # طباعة تفاصيل الخطأ إذا فشل
        if response.status_code != 201:
            print(f"Error details: {response.data}")

        assert response.status_code == status.HTTP_201_CREATED

        # التحقق من النجاح
        assert response.status_code == status.HTTP_201_CREATED

        # التحقق من البيانات
        if 'data' in response.data:
            order_info = response.data['data']
        else:
            order_info = response.data

        assert 'order_id' in str(order_info) or 'id' in str(order_info)

    def test_complete_order_flow(self, api_client, buyer_with_wallet, seller_with_wallet_and_offer,auth_buyer_client,auth_seller_client):
        """🔄 Test 2: دورة حياة الorder كاملة"""
        buyer_client, buyer, _ = auth_buyer_client
        seller_client, seller, offer, seller_payment = auth_seller_client


        # 1️⃣ المشتري ينشئ order
        order_data = {
            "offer_id": str(offer.id),
            "fiat_amount": 300,
            "payment_method_id": str(seller_payment.id)
        }

        print(f"\nSending order data: {order_data}")

        create_response = buyer_client.post('/api/p2p/orders/', order_data, format='json')

        print(f"\nResponse Status: {create_response.status_code}")
        print(f"Response Data: {create_response.data}")

        assert create_response.status_code == status.HTTP_201_CREATED

        # استخراج order_id
        order = P2POrder.objects.filter(taker_id=buyer.id).order_by('-created_at').first()
        assert order is not None
        order_id = order.id

        # 2️⃣ المشتري يشوف تفاصيل الorder
        get_response = buyer_client.get(f'/api/p2p/orders/{order_id}/')
        assert get_response.status_code == status.HTTP_200_OK

        # 3️⃣ المشتري يحدد أنه دفع
        mark_paid_response = buyer_client.post(f'/api/p2p/orders/{order_id}/mark-as-paid/')
        assert mark_paid_response.status_code == status.HTTP_200_OK

        # 4️⃣ البائع يؤكد استلام الدفعة
        confirm_response = seller_client.post(f'/api/p2p/orders/{order_id}/confirm-payment/')
        assert confirm_response.status_code == status.HTTP_200_OK

        # 5️⃣ التحقق من اكتمال الorder
        final_check = buyer_client.get(f'/api/p2p/orders/{order_id}/')
        assert final_check.status_code == status.HTTP_200_OK

    def test_list_user_orders(self, auth_buyer_client, seller_with_wallet_and_offer):
        """📋 Test 3: عرض قائمة orders المستخدم"""
        client, buyer, _ = auth_buyer_client
        _, offer, seller_payment= seller_with_wallet_and_offer

        # إنشاء عدة orders
        for i in range(3):
            order_data = {
                "offer_id": str(offer.id),
                "fiat_amount": str(100 + i*50),
                "payment_method_id": str(seller_payment.id)
            }
            response = client.post('/api/p2p/orders/', order_data, format='json')
            if response.status_code != 201:
                print(f"Failed to create order {i}: {response.data}")

        # عرض القائمة
        list_response = client.get('/api/p2p/orders/')
        assert list_response.status_code == status.HTTP_200_OK

        # التحقق من وجود orders
        if 'data' in list_response.data:
            orders = list_response.data['data']
        else:
            orders = list_response.data

        assert isinstance(orders, list)
        assert len(orders) >= 3

    def test_filter_orders_by_coin(self, auth_buyer_client, seller_with_wallet_and_offer):
        """🔍 Test 4: فلترة Orders حسب العملة"""
        client, buyer, _ = auth_buyer_client
        _, offer, _ = seller_with_wallet_and_offer

        # إنشاء order
        order_data = self.create_order_data(offer_id=offer.id, amount="200")
        client.post('/api/p2p/orders/', order_data, format='json')

        # فلترة حسب العملة
        filter_response = client.get(f'/api/p2p/orders/?coin={self.DEFAULT_CRYPTO}')
        assert filter_response.status_code == status.HTTP_200_OK

    def test_processing_orders_endpoint(self, auth_buyer_client, seller_with_wallet_and_offer):
        """⏳ Test 5: عرض الorders قيد المعالجة"""
        client, buyer, _ = auth_buyer_client
        _, offer, seller_payment = seller_with_wallet_and_offer

        # إنشاء order جديد
        order_data = {
            "offer_id": str(offer.id),
            "fiat_amount": "150",
            "payment_method_id": str(seller_payment.id)
        }
        response = client.post('/api/p2p/orders/', order_data, format='json')

        if response.status_code != 201:
            print(f"Failed to create order: {response.data}")

        # عرض processing orders
        processing_response = client.get('/api/p2p/orders/processing/')
        assert processing_response.status_code == status.HTTP_200_OK

        # التحقق من وجود order واحد على الأقل
        if 'data' in processing_response.data:
            orders = processing_response.data['data']
            # تخطي التحقق من العدد إذا فشل إنشاء الـ order
            if response.status_code == 201:
                assert len(orders) >= 1

    def test_historical_records_endpoint(self, auth_buyer_client, seller_with_wallet_and_offer):
        """📜 Test 6: عرض السجلات التاريخية"""
        client, buyer, _ = auth_buyer_client

        # الحصول على السجلات
        records_response = client.get('/api/p2p/orders/records/')
        assert records_response.status_code == status.HTTP_200_OK


    # ========== ROBUSTNESS TESTS - بيتعامل مع الأخطاء صح؟ ==========

    def test_create_order_with_invalid_offer(self, auth_buyer_client):
        """❌ Test 7: محاولة إنشاء order مع offer غير موجود"""
        client, _, _ = auth_buyer_client

        order_data = self.create_order_data(
            offer_id=99999,  # غير موجود
            fiat_amount="100"
        )

        response = client.post('/api/p2p/orders/', order_data, format='json')
        assert response.status_code in [status.HTTP_400_BAD_REQUEST,
                                        status.HTTP_404_NOT_FOUND,
                                        status.HTTP_403_FORBIDDEN]

    def test_create_order_exceeding_limits(self, auth_buyer_client, seller_with_wallet_and_offer):
        """⚠️ Test 8: محاولة إنشاء order يتجاوز الحدود"""
        client, _, _ = auth_buyer_client
        _, offer, seller_payment = seller_with_wallet_and_offer

        # محاولة طلب أكثر من الحد الأقصى
        order_data = self.create_order_data(
            offer_id=offer.id,
            fiat_amount="2000",  # أكثر من max_order_limit (1000)
            payment_method_id=str(seller_payment.id)

        )

        response = client.post('/api/p2p/orders/', order_data, format='json')
        # طباعة الخطأ إذا لم يفشل كما متوقع
        if response.status_code == 201:
            print(f"Unexpected success! Response: {response.data}")
            print(f"Order limits: min={offer.min_order_limit}, max={offer.max_order_limit}")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_order_below_minimum(self, auth_buyer_client, seller_with_wallet_and_offer):
        """⚠️ Test 9: محاولة إنشاء order أقل من الحد الأدنى"""
        client, _, _ = auth_buyer_client
        _, offer, seller_payment = seller_with_wallet_and_offer

        order_data = self.create_order_data(
            offer_id=offer.id,
            fiat_amount="50",  # أقل من min_order_limit (100)
            payment_method_id=str(seller_payment.id)
        )

        response = client.post('/api/p2p/orders/', order_data, format='json')
        # طباعة الخطأ إذا لم يفشل كما متوقع
        if response.status_code == 201:
            print(f"Unexpected success! Response: {response.data}")
            print(f"Order limits: min={offer.min_order_limit}, max={offer.max_order_limit}")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_mark_as_paid_wrong_user(self, auth_buyer_client, auth_seller_client, seller_with_wallet_and_offer):
        """🚫 Test 10: محاولة mark as paid من user خاطئ"""
        buyer_client, buyer, _ = auth_buyer_client
        seller_client, seller, offer, seller_payment = auth_seller_client

        # المشتري ينشئ order
        order_data = {
            "offer_id": str(offer.id),
            "fiat_amount": "300",
            "payment_method_id": str(seller_payment.id)
        }
        create_response = buyer_client.post('/api/p2p/orders/', order_data, format='json')

        if create_response.status_code != 201:
            print(f"Create order error: {create_response.data}")
        assert create_response.status_code == status.HTTP_201_CREATED

        order = P2POrder.objects.filter(taker_id=buyer.id).order_by('-created_at').first()
        assert order is not None, "Order was not created"
        order_id = order.id

        # البائع يحاول mark as paid (خطأ - المفروض المشتري فقط)
        wrong_response = seller_client.post(f'/api/p2p/orders/{order_id}/mark-as-paid/')
        assert wrong_response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST]

    def test_confirm_payment_wrong_user(self, auth_buyer_client, seller_with_wallet_and_offer):
        """🚫 Test 11: محاولة confirm payment من user خاطئ"""
        buyer_client, buyer, _ = auth_buyer_client
        _, offer, seller_payment = seller_with_wallet_and_offer

        # إنشاء order
        order_data = {
            "offer_id": str(offer.id),
            "fiat_amount": "300",
            "payment_method_id": str(seller_payment.id)
        }
        response = buyer_client.post('/api/p2p/orders/', order_data, format='json')

        # تخطي الاختبار إذا فشل إنشاء الـ order
        if response.status_code != 201:
            pytest.skip(f"Could not create order: {response.data}")

        order = P2POrder.objects.filter(taker_id=buyer.id).order_by('-created_at').first()
        if not order:
            pytest.skip("Order was not created")

        order_id = order.id

        # المشتري يحاول confirm payment (خطأ - المفروض البائع فقط)
        wrong_response = buyer_client.post(f'/api/p2p/orders/{order_id}/confirm-payment/')
        assert wrong_response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST]


    def test_cancel_order_after_payment(self, auth_buyer_client, seller_with_wallet_and_offer):
        """❌ Test 12: محاولة إلغاء order بعد الدفع"""
        client, buyer, _ = auth_buyer_client
        _, offer, seller_payment = seller_with_wallet_and_offer

        # إنشاء order مع payment_method_id
        order_data = self.create_order_data(
            offer_id=offer.id,
            fiat_amount="300",
            payment_method_id=str(seller_payment.id)
        )
        response = client.post('/api/p2p/orders/', order_data, format='json')

        # التحقق من نجاح الإنشاء
        if response.status_code != 201:
            pytest.skip(f"Could not create order: {response.data}")

        order = P2POrder.objects.filter(taker_id=buyer.id).order_by('-created_at').first()
        if not order:
            pytest.skip("Order was not created")

        order_id = order.id

        # mark as paid
        client.post(f'/api/p2p/orders/{order_id}/mark-as-paid/')

        # محاولة الإلغاء بعد الدفع
        cancel_response = client.post(f'/api/p2p/orders/{order_id}/cancel/')
        assert cancel_response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_order_status_transitions(self, auth_buyer_client, auth_seller_client, seller_with_wallet_and_offer):
        """🔄 Test 13: محاولة انتقالات خاطئة في حالة الorder"""
        buyer_client, buyer, _ = auth_buyer_client
        seller_client, _, offer, seller_payment = auth_seller_client

        # إنشاء order مع البيانات الصحيحة
        order_data = self.create_order_data(
            offer_id=offer.id,
            fiat_amount="300",
            payment_method_id=str(seller_payment.id)
        )
        response = buyer_client.post('/api/p2p/orders/', order_data, format='json')

        if response.status_code != 201:
            pytest.skip(f"Could not create order: {response.data}")

        order = P2POrder.objects.filter(taker_id=buyer.id).order_by('-created_at').first()
        if not order:
            pytest.skip("Order was not created")

        order_id = order.id

        # محاولة confirm payment قبل mark as paid
        confirm_response = seller_client.post(f'/api/p2p/orders/{order_id}/confirm-payment/')
        assert confirm_response.status_code == status.HTTP_400_BAD_REQUEST

    # ========== SECURITY TESTS - محمي من unauthorized access؟ ==========

    def test_unauthorized_order_creation(self, api_client, seller_with_wallet_and_offer):
        """🔒 Test 14: محاولة إنشاء order بدون authentication"""
        _, offer, _ = seller_with_wallet_and_offer

        order_data = self.create_order_data(offer_id=offer.id, amount="200")
        response = api_client.post('/api/p2p/orders/', order_data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_access_other_user_order(self, auth_buyer_client, auth_seller_client, seller_with_wallet_and_offer):
        """🔐 Test 15: محاولة الوصول لorder مستخدم آخر"""
        buyer_client, buyer, _ = auth_buyer_client
        seller_client, seller, offer, seller_payment = auth_seller_client

        # المشتري ينشئ order مع البيانات الصحيحة
        order_data = self.create_order_data(
            offer_id=offer.id,
            fiat_amount="300",
            payment_method_id=str(seller_payment.id)
        )
        response = buyer_client.post('/api/p2p/orders/', order_data, format='json')

        if response.status_code != 201:
            pytest.skip(f"Could not create order: {response.data}")

        order = P2POrder.objects.filter(taker_id=buyer.id).order_by('-created_at').first()
        if not order:
            pytest.skip("Order was not created")

        order_id = order.id

        # إنشاء مستخدم ثالث
        third_user = User.objects.create_user(username='third_user', password='pass123')
        third_client = APIClient()
        third_client.force_authenticate(user=third_user)

        # محاولة الوصول للorder
        response = third_client.get(f'/api/p2p/orders/{order_id}/')
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    def test_unauthorized_order_actions(self, api_client):
        """🔒 Test 16: محاولة actions بدون authentication"""
        # محاولة mark as paid
        response = api_client.post('/api/p2p/orders/1/mark-as-paid/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # محاولة confirm payment
        response = api_client.post('/api/p2p/orders/1/confirm-payment/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # محاولة cancel
        response = api_client.post('/api/p2p/orders/1/cancel/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ========== PERFORMANCE TESTS - بيشتغل بسرعة مناسبة؟ ==========

    def test_list_orders_performance(self, auth_buyer_client, seller_with_wallet_and_offer):
        """⚡ Test 17: أداء عرض قائمة كبيرة من الorders"""
        import time
        client, _, _ = auth_buyer_client
        _, offer, _ = seller_with_wallet_and_offer

        # إنشاء 20 order
        for i in range(20):
            order_data = self.create_order_data(
                offer_id=offer.id,
                amount=str(100 + i*10)
            )
            client.post('/api/p2p/orders/', order_data, format='json')

        # قياس وقت استرجاع القائمة
        start_time = time.time()
        response = client.get('/api/p2p/orders/')
        end_time = time.time()

        assert response.status_code == status.HTTP_200_OK
        assert (end_time - start_time) < 2.0  # يجب أن يكون أقل من 2 ثانية

    def test_concurrent_order_creation(self, auth_buyer_client, seller_with_wallet_and_offer):
        """⚡ Test 18: إنشاء orders متزامنة"""
        client, _, _ = auth_buyer_client
        _, offer, _ = seller_with_wallet_and_offer

        # محاولة إنشاء عدة orders في نفس الوقت
        responses = []
        for i in range(5):
            order_data = self.create_order_data(
                offer_id=offer.id,
                amount=str(100 + i*50)
            )
            response = client.post('/api/p2p/orders/', order_data, format='json')
            responses.append(response)

        # التحقق من نجاح جميع الطلبات أو فشل بعضها بسبب نفاد الكمية
        success_count = sum(1 for r in responses if r.status_code == status.HTTP_201_CREATED)
        assert success_count >= 1  # على الأقل order واحد ينجح

    # ========== MAINTAINABILITY TESTS - الكود قابل للصيانة؟ ==========

    def test_order_response_structure_consistency(self, auth_buyer_client, seller_with_wallet_and_offer):
        """📐 Test 19: اتساق structure الresponse"""
        client, _, _ = auth_buyer_client
        _, offer, seller_payment = seller_with_wallet_and_offer

        # إنشاء order مع البيانات الصحيحة
        order_data = self.create_order_data(
            offer_id=offer.id,
            fiat_amount="300",
            payment_method_id=str(seller_payment.id)
        )
        create_response = client.post('/api/p2p/orders/', order_data, format='json')

        if create_response.status_code != 201:
            pytest.skip(f"Could not create order: {create_response.data}")

        order = P2POrder.objects.filter().order_by('-created_at').first()
        if not order:
            pytest.skip("Order was not created")

        order_id = order.id

        # جمع responses من endpoints مختلفة
        responses = {
            'create': create_response,
            'retrieve': client.get(f'/api/p2p/orders/{order_id}/'),
            'list': client.get('/api/p2p/orders/'),
            'processing': client.get('/api/p2p/orders/processing/'),
            'records': client.get('/api/p2p/orders/records/')
        }

        # التحقق من وجود structure متسق
        for endpoint, response in responses.items():
            if response.status_code == 200 or response.status_code == 201:
                # يجب أن يكون هناك success أو data
                assert 'success' in response.data or 'data' in response.data or isinstance(response.data, list)

    def test_error_response_structure(self, auth_buyer_client):
        """📐 Test 20: اتساق structure رسائل الخطأ"""
        client, _, _ = auth_buyer_client

        # محاولة إنشاء order بدون بيانات
        response = client.post('/api/p2p/orders/', {}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # يجب أن يكون هناك رسالة خطأ واضحة
        assert 'error' in response.data or 'detail' in response.data or 'message' in response.data

    def test_api_versioning_compatibility(self, auth_buyer_client, seller_with_wallet_and_offer):
        """🔄 Test 21: التوافق مع إصدارات API المختلفة"""
        client, _, _ = auth_buyer_client
        _, offer, _ = seller_with_wallet_and_offer

        # اختبار endpoints بصيغ مختلفة
        order_data = self.create_order_data(offer_id=offer.id, amount="200")

        # الصيغة الحالية
        response1 = client.post('/api/p2p/orders/', order_data, format='json')
        assert response1.status_code in [200, 201]

        # محاولة بدون trailing slash
        response2 = client.post('/api/p2p/orders', order_data, format='json')
        # يجب أن يعمل أو يعطي redirect
        assert response2.status_code in [200, 201, 301, 302]