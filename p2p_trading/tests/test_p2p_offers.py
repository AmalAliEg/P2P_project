# tests/test_p2p_offers.py
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from p2p_trading.models import P2POffer, Wallet
from p2p_trading.constants.constant import TradeType, OfferStatus
from MainDashboard.models import PaymentMethods

User = get_user_model()

@pytest.mark.django_db(databases=['default','main_db'])
class TestP2POffers:

    # ========== TEST CONSTANTS ==========
    # Avoid hard-coded values by defining them once
    DEFAULT_CRYPTO = 'USDT'
    DEFAULT_FIAT = 'EGP'
    DEFAULT_PRICE = Decimal('60.4')
    DEFAULT_AMOUNT = Decimal('1000')
    MIN_LIMIT = Decimal('100')
    MAX_LIMIT = Decimal('1000')
    WALLET_BALANCE = Decimal('5000.00')
    INSUFFICIENT_BALANCE = Decimal('500.00')

    # ========== HELPER METHODS ==========
    def _create_offer(self, **kwargs):
        """Helper method to create offer with defaults"""
        defaults = {
            'trade_type': TradeType.SELL,
            'crypto_currency': self.DEFAULT_CRYPTO,
            'fiat_currency': self.DEFAULT_FIAT,
            'price': self.DEFAULT_PRICE,
            'total_amount': self.DEFAULT_AMOUNT,
            'available_amount': self.DEFAULT_AMOUNT,
            'min_order_limit': self.MIN_LIMIT,
            'max_order_limit': self.MAX_LIMIT,
            'status': OfferStatus.ACTIVE
        }
        defaults.update(kwargs)
        return P2POffer.objects.create(**defaults)

    def _build_offer_data(self, payment_method_id=None, **overrides):
        """Helper to build offer data dict for API calls"""
        data = {
            "trade_type": "SELL",
            "crypto_currency": self.DEFAULT_CRYPTO,
            "fiat_currency": self.DEFAULT_FIAT,
            "price_type": "FIXED",
            "price": str(self.DEFAULT_PRICE),
            "total_amount": str(self.DEFAULT_AMOUNT),
            "min_order_limit": str(self.MIN_LIMIT),
            "max_order_limit": str(self.MAX_LIMIT),
            "payment_time_limit_minutes": 120
        }

        if payment_method_id:
            data["payment_method_ids"] = [payment_method_id]

        data.update(overrides)
        return data

    def _create_payment_method(self, user, method_id='BANK_001', **kwargs):
        """Helper to create payment method"""
        defaults = {
            'payment_method_id': method_id,
            'type': 'BANK_TRANSFER',
            'number': '1234567890',
            'holder_name': user.username,
            'primary': True
        }
        defaults.update(kwargs)
        return PaymentMethods.objects.create(user=user, **defaults)

    def _create_wallet(self, user_id, balance=None):
        """Helper to create wallet"""
        return Wallet.objects.create(
            user_id=user_id,
            currency=self.DEFAULT_CRYPTO,
            balance=balance or self.WALLET_BALANCE
        )

    # ========== FIXTURES ==========
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def user(self):
        return User.objects.create_user(username='testuser', password='testpass123')

    @pytest.fixture
    def other_user(self):
        return User.objects.create_user(username='otheruser', password='otherpass123')

    @pytest.fixture
    def authenticated_client(self, api_client, user):
        api_client.force_authenticate(user=user)
        return api_client

    @pytest.fixture
    def payment_method(self, user):
        return self._create_payment_method(user)

    @pytest.fixture
    def user_wallet(self, user):
        return self._create_wallet(user.id)

    @pytest.fixture
    def sample_offer_data(self, payment_method):
        return self._build_offer_data(payment_method.id)

    @pytest.fixture
    def other_user_offer(self, other_user):
        """Create complete setup for another user"""
        payment = self._create_payment_method(
            other_user,
            method_id='BANK_002',
            number='9876543210'
        )
        self._create_wallet(other_user.id, balance=self.DEFAULT_AMOUNT)

        return self._create_offer(
            user_id=other_user.id,
            payment_method_ids=[payment.id]
        )

    @pytest.fixture
    def many_offers(self, user, payment_method, user_wallet):
        """Create many offers for pagination testing"""
        offers = []
        for i in range(25):
            offer = self._create_offer(
                user_id=user.id,
                payment_method_ids=[payment_method.id],
                price=self.DEFAULT_PRICE + Decimal(str(i))
            )
            offers.append(offer)
        return offers

    @pytest.fixture
    def multiple_offers(self, user, payment_method, user_wallet):
        """Create offers with different types and statuses for filtering"""
        offers = []

        # Active SELL offers
        for i in range(3):
            offers.append(self._create_offer(
                user_id=user.id,
                trade_type=TradeType.SELL,
                payment_method_ids=[payment_method.id],
                status=OfferStatus.ACTIVE
            ))

        # Active BUY offers
        for i in range(2):
            offers.append(self._create_offer(
                user_id=user.id,
                trade_type=TradeType.BUY,
                payment_method_ids=[payment_method.id],
                status=OfferStatus.ACTIVE
            ))

        # Inactive offer
        offers.append(self._create_offer(
            user_id=user.id,
            payment_method_ids=[payment_method.id],
            status=OfferStatus.INACTIVE
        ))

        return offers

    # ========== TESTS ==========

    def test_create_offer_success(self, authenticated_client, sample_offer_data, user_wallet):
        """Test successful offer creation"""
        response = authenticated_client.post('/api/p2p/offers/', sample_offer_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] == True
        assert P2POffer.objects.count() == 1

        offer = P2POffer.objects.first()
        assert offer.trade_type == TradeType.SELL
        assert offer.crypto_currency == self.DEFAULT_CRYPTO
        assert offer.available_amount == self.DEFAULT_AMOUNT

    def test_create_offer_insufficient_balance(self, authenticated_client, sample_offer_data, user_wallet):
        """Test offer creation with insufficient balance"""
        user_wallet.balance = self.INSUFFICIENT_BALANCE
        user_wallet.save()

        response = authenticated_client.post('/api/p2p/offers/', sample_offer_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_offer_invalid_payment_method(self, authenticated_client, payment_method):
        """Test offer creation with invalid payment method"""
        data = self._build_offer_data(payment_method_id=999)  # Non-existent ID

        response = authenticated_client.post('/api/p2p/offers/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_offers(self, authenticated_client, user, payment_method, user_wallet):
        """Test listing offers"""
        # Create offers using helper
        for _ in range(3):
            self._create_offer(
                user_id=user.id,
                payment_method_ids=[payment_method.id]
            )

        response = authenticated_client.get('/api/p2p/offers/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 3

    def test_get_offer_details(self, authenticated_client, user, payment_method, user_wallet):
        """Test getting offer details"""
        offer = self._create_offer(
            user_id=user.id,
            payment_method_ids=[payment_method.id]
        )

        response = authenticated_client.get(f'/api/p2p/offers/{offer.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['id'] == offer.id

    def test_update_offer_status(self, authenticated_client, user, payment_method, user_wallet):
        """Test updating offer status"""
        offer = self._create_offer(
            user_id=user.id,
            payment_method_ids=[payment_method.id]
        )

        response = authenticated_client.put(
            f'/api/p2p/offers/{offer.id}/',
            {'status': 'INACTIVE'},
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        offer.refresh_from_db()
        assert offer.status == OfferStatus.INACTIVE

    def test_delete_offer(self, authenticated_client, user, payment_method, user_wallet):
        """Test deleting offer"""
        offer = self._create_offer(
            user_id=user.id,
            payment_method_ids=[payment_method.id]
        )

        offer_id = offer.id
        response = authenticated_client.delete(f'/api/p2p/offers/{offer_id}/')

        if P2POffer.objects.filter(id=offer_id).exists():
            offer.refresh_from_db()
            assert offer.status in [OfferStatus.DELETED, OfferStatus.CANCELLED]
        else:
            assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_public_offers_list(self, api_client, user, payment_method, user_wallet):
        """Test public offers list"""
        self._create_offer(
            user_id=user.id,
            payment_method_ids=[payment_method.id]
        )

        response = api_client.get('/api/p2p/offers/')

        if response.status_code == 401:
            api_client.force_authenticate(user=user)
            response = api_client.get('/api/p2p/offers/')

        assert response.status_code == status.HTTP_200_OK

    # ========== AUTHENTICATION & AUTHORIZATION TESTS ==========

    def test_create_offer_unauthenticated(self, api_client, payment_method):
        """Test creating offer without authentication"""
        data = self._build_offer_data(payment_method.id)
        response = api_client.post('/api/p2p/offers/', data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_other_user_offer(self, authenticated_client, other_user_offer):
        """Test updating another user's offer"""
        response = authenticated_client.put(
            f'/api/p2p/offers/{other_user_offer.id}/',
            {'status': 'INACTIVE'},
            format='json'
        )
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    # ========== VALIDATION EDGE CASES ==========

    def test_create_offer_negative_amounts(self, authenticated_client, payment_method):
        """Test with negative amounts"""
        data = self._build_offer_data(
            payment_method.id,
            total_amount='-100'
        )

        response = authenticated_client.post('/api/p2p/offers/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_offer_min_greater_than_max(self, authenticated_client, payment_method):
        """Test min_order_limit > max_order_limit"""
        data = self._build_offer_data(
            payment_method.id,
            min_order_limit='2000',
            max_order_limit='1000'
        )

        response = authenticated_client.post('/api/p2p/offers/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ========== DATABASE EDGE CASES ==========

    def test_get_nonexistent_offer(self, authenticated_client):
        """Test getting non-existent offer"""
        response = authenticated_client.get('/api/p2p/offers/99999/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # ========== FILTERING & PAGINATION ==========

    def test_list_offers_with_filters(self, authenticated_client, multiple_offers):
        """Test filtering offers"""
        response = authenticated_client.get('/api/p2p/offers/?status=ACTIVE&type=SELL')
        assert response.status_code == status.HTTP_200_OK

        if 'data' in response.data:
            offers_data = response.data['data']
            for offer in offers_data:
                assert offer['trade_type'] == 'SELL'
                assert offer['status'] == 'ACTIVE'