# p2p_trading/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from .models.p2p_offer_model import P2POffer
from .models.p2p_order_model import P2POrder
from .models.p2p_profile_models import P2PProfile, Feedback, Follow, BlockedUser
from .models.p2p_wallet_model import Wallet
from .models.p2p_transaction_model import Transaction


# ================== P2P OFFER ADMIN ==================
@admin.register(P2POffer)
class P2POfferAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_id_link', 'trade_type_badge', 'crypto_currency',
        'fiat_currency', 'price_display', 'available_amount_display',
        'status_badge', 'created_at'
    ]

    list_filter = [
        'status', 'trade_type', 'crypto_currency', 'fiat_currency',
        'price_type', 'created_at', 'is_deleted'
    ]

    search_fields = [
        'id', 'user_id', 'crypto_currency', 'fiat_currency',
        'remarks', 'auto_reply_message'
    ]

    readonly_fields = [
        'id', 'created_at', 'updated_at', 'available_amount'
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': ('user_id', 'trade_type', 'status', 'is_deleted')
        }),
        ('Currency & Pricing', {
            'fields': (
                'crypto_currency', 'fiat_currency', 'price_type',
                'price', 'price_margin'
            )
        }),
        ('Amounts & Limits', {
            'fields': (
                'total_amount', 'available_amount', 'min_order_limit',
                'max_order_limit'
            )
        }),
        ('Payment Settings', {
            'fields': (
                'payment_method_ids', 'payment_time_limit_minutes'
            )
        }),
        ('Additional Info', {
            'fields': ('remarks', 'auto_reply_message'),
            'classes': ('collapse',)
        }),
        ('Counterparty Requirements', {
            'fields': (
                'counterparty_min_registration_days',
                'counterparty_min_holding_amount'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        })
    )

    actions = ['activate_offers', 'deactivate_offers', 'soft_delete_offers']

    def user_id_link(self, obj):
        """Create clickable link to user"""
        url = reverse('admin:p2p_trading_p2pprofile_change', args=[obj.user_id])
        return format_html('<a href="{}">{}</a>', url, obj.user_id)
    user_id_link.short_description = 'User'

    def trade_type_badge(self, obj):
        """Display trade type with color coding"""
        colors = {'BUY': 'green', 'SELL': 'red'}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.trade_type, 'black'),
            obj.trade_type
        )
    trade_type_badge.short_description = 'Type'

    def price_display(self, obj):
        """Format price display"""
        if obj.price_type == 'FIXED':
            return f"{obj.price} {obj.fiat_currency}"
        else:
            margin = obj.price_margin or Decimal('0')
            return f"Market {'+' if margin >= 0 else ''}{margin}%"
    price_display.short_description = 'Price'

    def available_amount_display(self, obj):
        """Display available/total amount"""
        percentage = (obj.available_amount / obj.total_amount * 100) if obj.total_amount > 0 else 0
        return format_html(
            '{:.8f} / {:.8f} ({:.1f}%)',
            obj.available_amount,
            obj.total_amount,
            percentage
        )
    available_amount_display.short_description = 'Available/Total'

    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'ACTIVE': 'green',
            'INACTIVE': 'gray',
            'COMPLETED': 'blue',
            'CANCELLED': 'red'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.status
        )
    status_badge.short_description = 'Status'

    def activate_offers(self, request, queryset):
        updated = queryset.update(status='ACTIVE')
        self.message_user(request, f'{updated} offers activated.')
    activate_offers.short_description = 'Activate selected offers'

    def deactivate_offers(self, request, queryset):
        updated = queryset.update(status='INACTIVE')
        self.message_user(request, f'{updated} offers deactivated.')
    deactivate_offers.short_description = 'Deactivate selected offers'

    def soft_delete_offers(self, request, queryset):
        updated = queryset.update(is_deleted=True, deleted_at=timezone.now())
        self.message_user(request, f'{updated} offers soft deleted.')
    soft_delete_offers.short_description = 'Soft delete selected offers'


# ================== P2P ORDER ADMIN ==================
@admin.register(P2POrder)
class P2POrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'offer_link', 'maker_id', 'taker_id',
        'trade_type_badge', 'amount_display', 'status_badge',
        'created_at'
    ]

    list_filter = [
        'status', 'trade_type', 'crypto_currency', 'fiat_currency',
        'created_at', 'paid_at', 'completed_at'
    ]

    search_fields = [
        'order_number', 'maker_id', 'taker_id', 'chat_room_id'
    ]

    readonly_fields = [
        'order_number', 'created_at', 'updated_at', 'paid_at',
        'completed_at', 'cancelled_at'
    ]

    date_hierarchy = 'created_at'

    def offer_link(self, obj):
        """Link to related offer"""
        url = reverse('admin:p2p_trading_p2poffer_change', args=[obj.offer.id])
        return format_html('<a href="{}">{}</a>', url, f'Offer #{obj.offer.id}')
    offer_link.short_description = 'Offer'

    def trade_type_badge(self, obj):
        """Display trade type with color"""
        colors = {'BUY': 'green', 'SELL': 'red'}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.trade_type, 'black'),
            obj.trade_type
        )
    trade_type_badge.short_description = 'Type'

    def amount_display(self, obj):
        """Display crypto and fiat amounts"""
        return format_html(
            '{:.8f} {} = {:.2f} {}',
            obj.crypto_amount, obj.crypto_currency,
            obj.fiat_amount, obj.fiat_currency
        )
    amount_display.short_description = 'Amount'

    def status_badge(self, obj):
        """Display status with color"""
        colors = {
            'UNPAID': 'orange',
            'PAID': 'blue',
            'COMPLETED': 'green',
            'CANCELLED': 'red',
            'DISPUTED': 'purple'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.status
        )
    status_badge.short_description = 'Status'


# ================== P2P PROFILE ADMIN ==================
@admin.register(P2PProfile)
class P2PProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user_id', 'nickname', 'total_30d_trades',
        'completion_rate_display', 'feedback_display',
        'created_at'
    ]

    list_filter = [
        'created_at',
        ('total_30d_trades', admin.EmptyFieldListFilter),
    ]

    search_fields = ['user_id', 'nickname']

    readonly_fields = [
        'created_at', 'updated_at', 'total_30d_trades',
        'completion_rate_30d', 'avg_release_time_minutes',
        'avg_pay_time_minutes', 'positive_feedback_count',
        'positive_feedback_rate'
    ]

    def completion_rate_display(self, obj):
        """Display completion rate with color"""
        rate = obj.completion_rate_30d
        color = 'green' if rate >= 95 else 'orange' if rate >= 80 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, rate
        )
    completion_rate_display.short_description = 'Completion Rate'

    def feedback_display(self, obj):
        """Display feedback stats"""
        return format_html(
            '{} positive ({:.1f}%)',
            obj.positive_feedback_count,
            obj.positive_feedback_rate
        )
    feedback_display.short_description = 'Feedback'


# ================== WALLET ADMIN ==================
@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = [
        'user_id', 'currency', 'balance', 'locked_balance',
        'available_balance_display', 'created_at'
    ]

    list_filter = ['currency', 'created_at']
    search_fields = ['user_id', 'currency']
    readonly_fields = ['created_at', 'updated_at']

    def available_balance_display(self, obj):
        """Display available balance"""
        available = obj.balance - obj.locked_balance
        return format_html(
            '<span style="color: green; font-weight: bold;">{:.8f}</span>',
            available
        )
    available_balance_display.short_description = 'Available'


# ================== TRANSACTION ADMIN ==================
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'wallet_link', 'transaction_type', 'amount_display',
        'running_balance', 'created_at'
    ]

    list_filter = ['transaction_type', 'created_at']
    search_fields = ['wallet__user_id', 'related_order__order_number']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

    def wallet_link(self, obj):
        """Link to wallet"""
        return format_html(
            '<a href="{}">User {} - {}</a>',
            reverse('admin:p2p_trading_wallet_change', args=[obj.wallet.id]),
            obj.wallet.user_id,
            obj.wallet.currency
        )
    wallet_link.short_description = 'Wallet'

    def amount_display(self, obj):
        """Display amount with color"""
        color = 'green' if obj.amount > 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:+.8f}</span>',
            color, obj.amount
        )
    amount_display.short_description = 'Amount'


# ================== FEEDBACK ADMIN ==================
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'reviewer', 'reviewee', 'order_link', 'is_positive_display',
        'created_at'
    ]

    list_filter = ['is_positive', 'created_at']
    search_fields = ['reviewer__nickname', 'reviewee__nickname', 'comment']
    readonly_fields = ['created_at']

    def order_link(self, obj):
        """Link to order"""
        return format_html(
            '<a href="{}">Order #{}</a>',
            reverse('admin:p2p_trading_p2porder_change', args=[obj.order.id]),
            obj.order.order_number
        )
    order_link.short_description = 'Order'

    def is_positive_display(self, obj):
        """Display feedback type with icon"""
        if obj.is_positive:
            return format_html('<span style="color: green;">✓ Positive</span>')
        return format_html('<span style="color: red;">✗ Negative</span>')
    is_positive_display.short_description = 'Type'


# ================== CUSTOM ADMIN SITE CONFIG ==================
admin.site.site_header = 'P2P Trading Administration'
admin.site.site_title = 'P2P Admin'
admin.site.index_title = 'P2P Trading Management'