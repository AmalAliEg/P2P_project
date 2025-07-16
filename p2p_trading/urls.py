# p2p_trading/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .controllers.p2p_wallet_controller import P2PWalletController
from .controllers.p2p_offer_controller import P2POfferController
from .controllers.p2p_order_controller import P2POrderController
from .controllers.p2p_profile_controller import P2PProfileController

router = DefaultRouter()

# routes for the  Controller of the Offers
router.register(r'offers', P2POfferController, basename='p2p-offer')
router.register(r'orders', P2POrderController, basename='p2p-order')
router.register(r'wallet', P2PWalletController, basename='p2p-wallet')
router.register(r'profiles', P2PProfileController, basename='p2p-profile')


urlpatterns = [
    path('', include(router.urls)),
]



'''
GET    /api/p2p/offers/                    → list
POST   /api/p2p/offers/                    → create
GET    /api/p2p/offers/{id}/               → retrieve
PUT    /api/p2p/offers/{id}/               → update
PATCH  /api/p2p/offers/{id}/               → partial_update
DELETE /api/p2p/offers/{id}/               → destroy
'''