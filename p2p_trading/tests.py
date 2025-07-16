















































# from django.test import TestCase
#
# # Create your tests here.
# # p2p_trading/management/commands/create_test_offers.py
#
# from django.core.management.base import BaseCommand
# from MainDashboard.models import MainUser
# from p2p_trading.models.p2p_profile_models import P2PProfile
# from p2p_trading.models.p2p_offer_model import P2POffer
# from p2p_trading.constants.constant import OfferStatus, TradeType, PriceType
# from decimal import Decimal
# import random
#
# class Command(BaseCommand):
#     help = 'Create test offers'
#
#     def handle(self, *args, **options):
#         # البيانات من الصورة
#         test_data = [
#             {
#                 'username': 'el_pop1',
#                 'nickname': 'El_Pop1',
#                 'orders': 751,
#                 'completion': 98.90,
#                 'price': '50.09',
#                 'amount': '769.07'
#             },
#             {
#                 'username': 'borms',
#                 'nickname': 'Borms',
#                 'orders': 44,
#                 'completion': 91.70,
#                 'price': '50.10',
#                 'amount': '898.65'
#             },
#             {
#                 'username': 'mer',
#                 'nickname': 'mer33',
#                 'orders': 1000,
#                 'completion': 99.70,
#                 'price': '55.10',
#                 'amount': '2500.65'
#             },
#             # أضف الباقي
#         ]
#
#         for data in test_data:
#             # أنشئ مستخدم
#             user, created = MainUser.objects.get_or_create(
#                 username=data['username']
#             )
#             if created:
#                 user.set_password('test123')
#                 user.save()
#
#             # أنشئ بروفايل
#             profile, _ = P2PProfile.objects.get_or_create(
#                 user_id=user.id,
#                 defaults={
#                     'nickname': data['nickname'],
#                     'total_30d_trades': data['orders'],
#                     'completion_rate_30d': data['completion']
#                 }
#             )
#
#             # أنشئ عرض
#             P2POffer.objects.create(
#                 user_id=user.id,
#                 trade_type=TradeType.SELL,
#                 crypto_currency='USDT',
#                 fiat_currency='EGP',
#                 price_type=PriceType.FIXED,
#                 price=Decimal(data['price']),
#                 total_amount=Decimal(data['amount']),
#                 available_amount=Decimal(data['amount']),
#                 min_order_limit=Decimal('5000'),
#                 max_order_limit=Decimal('50000'),
#                 payment_method_ids=[1],
#                 status=OfferStatus.ACTIVE
#             )
#
#             self.stdout.write(f'Created offer for {data["nickname"]}')