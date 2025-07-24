# p2p_trading/admin.py
from django.contrib import admin, messages
from django.db import transaction
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils import timezone
from decimal import Decimal

# استيراد MainUser من التطبيق الآخر
try:
    from MainDashboard.models import MainUser, MainTransaction, MainWallet, PaymentMethods

    MAIN_USER_AVAILABLE = True
except ImportError:
    MAIN_USER_AVAILABLE = False

# باقي الاستيرادات...
from .models.p2p_offer_model import P2POffer
from .models.p2p_order_model import P2POrder
from .models.p2p_profile_models import P2PProfile, Feedback
from .models.p2p_wallet_model import Wallet
from .models.p2p_transaction_model import Transaction


from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# ================== MAIN WALLET ADMIN ==================
if MAIN_USER_AVAILABLE:
    @admin.register(MainWallet)
    class MainWalletAdmin(admin.ModelAdmin):
        list_display = [
            'user_display', 'currency', 'balance',
            'created_at', 'updated_at'
        ]

        list_filter = ['currency', 'created_at']
        search_fields = ['user__username', 'currency']
        readonly_fields = ['created_at', 'updated_at']

        actions = [
            'transfer_to_p2p_wallet',
            'zero_selected_wallets',
            'delete_empty_wallets'
        ]

        def user_display(self, obj):
            """Display user with link"""
            url = reverse('admin:MainDashboard_mainuser_change', args=[obj.user.id])
            return format_html(
                '<a href="{}" title="View User">{}</a>',
                url, obj.user.username
            )
        user_display.short_description = 'User'

        def transfer_to_p2p_wallet(self, request, queryset):
            """Transfer balance to P2P wallet"""
            transferred = 0
            for main_wallet in queryset:
                if main_wallet.balance > 0:
                    # Create or get P2P wallet
                    p2p_wallet, created = Wallet.objects.get_or_create(
                        user_id=main_wallet.user.id,
                        currency=main_wallet.currency,
                        defaults={'balance': 0, 'locked_balance': 0}
                    )

                    # Transfer balance
                    p2p_wallet.balance += main_wallet.balance
                    p2p_wallet.save()

                    # Create transaction record
                    MainTransaction.objects.create(
                        wallet=main_wallet,
                        transaction_type='TRANSFER_TO_P2P',
                        amount=-main_wallet.balance,
                        reference=f'Transfer to P2P wallet'
                    )

                    # Zero out main wallet
                    main_wallet.balance = 0
                    main_wallet.save()
                    transferred += 1

            self.message_user(request, f'✅ {transferred} wallets transferred to P2P')
        transfer_to_p2p_wallet.short_description = '💸 Transfer balance to P2P wallet'

        def zero_selected_wallets(self, request, queryset):
            """Zero out selected wallets with confirmation"""
            total_balance = sum(wallet.balance for wallet in queryset)
            if total_balance > 0:
                messages.warning(
                    request,
                    f'⚠️ Total balance to be zeroed: {total_balance}. Use with caution!'
                )
            updated = queryset.update(balance=0)
            self.message_user(request, f'✅ {updated} wallets zeroed out')
        zero_selected_wallets.short_description = '⚠️ Zero out balances'

        def delete_empty_wallets(self, request, queryset):
            """Delete only empty wallets"""
            empty = queryset.filter(balance=0)
            count = empty.count()
            empty.delete()
            self.message_user(request, f'🗑️ {count} empty wallets deleted')
        delete_empty_wallets.short_description = '🗑️ Delete empty wallets'

# ================== MAIN TRANSACTION ADMIN ==================
if MAIN_USER_AVAILABLE:
    @admin.register(MainTransaction)
    class MainTransactionAdmin(admin.ModelAdmin):
        list_display = [
            'id', 'wallet_info', 'transaction_type_badge',
            'amount_display', 'reference', 'created_at'
        ]

        list_filter = ['transaction_type', 'created_at', 'wallet__currency']
        search_fields = ['wallet__user__username', 'reference']
        readonly_fields = ['created_at', 'wallet', 'transaction_type', 'amount']
        date_hierarchy = 'created_at'

        actions = ['export_selected_transactions']

        def wallet_info(self, obj):
            """Display wallet user and currency"""
            return format_html(
                '<a href="{}">{} - {}</a>',
                reverse('admin:MainDashboard_mainwallet_change', args=[obj.wallet.id]),
                obj.wallet.user.username,
                obj.wallet.currency
            )
        wallet_info.short_description = 'Wallet'

        def transaction_type_badge(self, obj):
            """Display transaction type with color"""
            colors = {
                'DEPOSIT': 'green',
                'WITHDRAWAL': 'red',
                'TRANSFER_TO_P2P': 'blue',
                'TRANSFER_FROM_P2P': 'orange',
                'TRANSFER_TO_AUTO': 'purple',
                'TRANSFER_FROM_AUTO': 'brown'
            }
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
                colors.get(obj.transaction_type, 'gray'),
                obj.get_transaction_type_display()
            )
        transaction_type_badge.short_description = 'Type'

        def amount_display(self, obj):
            """Display amount with color"""
            color = 'green' if obj.amount > 0 else 'red'
            amount_str = f"{obj.amount:+.8f}"  # حوّلي القيمة لنص أولاً
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color, amount_str
            )
        amount_display.short_description = 'Amount'

        def has_delete_permission(self, request, obj=None):
            """Prevent deletion of transactions"""
            return False

        def export_selected_transactions(self, request, queryset):
            """Export transactions (placeholder)"""
            messages.info(request, 'Export feature coming soon!')
        export_selected_transactions.short_description = '📥 Export selected'


# ================== PAYMENT METHODS ADMIN ==================
if MAIN_USER_AVAILABLE:

    @admin.register(PaymentMethods)
    class PaymentMethodsAdmin(admin.ModelAdmin):
        list_display = [
            'id', 'user_link', 'type', 'number_masked',
            'holder_name', 'primary_badge', 'expiration_status'
        ]

        list_filter = ['type', 'primary']
        search_fields = ['user__username', 'holder_name', 'number', 'payment_method_id']
        readonly_fields = ['payment_method_id']

        fieldsets = (
            ('User Information', {
                'fields': ('user', 'primary')
            }),
            ('Payment Details', {
                'fields': ('payment_method_id', 'type', 'number', 'holder_name', 'expiration_date')
            }),
        )

        actions = ['make_primary', 'remove_primary', 'mask_sensitive_data']

        def user_link(self, obj):
            """Link to user"""
            if obj.user:
                url = reverse('admin:MainDashboard_mainuser_change', args=[obj.user.id])
                return format_html(
                    '<a href="{}" title="View User">{}</a>',
                    url, obj.user.username
                )
            return '-'
        user_link.short_description = 'User'

        def number_masked(self, obj):
            """Display masked card/account number"""
            if obj.number:
                # Show only last 4 digits
                masked = '*' * (len(obj.number) - 4) + obj.number[-4:]
                return masked
            return '-'
        number_masked.short_description = 'Number'

        def primary_badge(self, obj):
            """Display primary status"""
            if obj.primary:
                return format_html(
                    '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">✓ Primary</span>'
                )
            return format_html(
                '<span style="background-color: gray; color: white; padding: 3px 10px; border-radius: 3px;">Secondary</span>'
            )
        primary_badge.short_description = 'Status'

        def expiration_status(self, obj):
            """Check if payment method is expired"""
            if obj.expiration_date:
                # Assuming format MM/YY
                try:
                    from datetime import datetime
                    month, year = obj.expiration_date.split('/')
                    exp_date = datetime(2000 + int(year), int(month), 1)

                    if exp_date < datetime.now():
                        return format_html('<span style="color: red;">⚠️ Expired</span>')
                    elif (exp_date - datetime.now()).days < 90:
                        return format_html('<span style="color: orange;">⚠️ Expiring Soon</span>')
                    else:
                        return format_html('<span style="color: green;">✓ Valid</span>')
                except:
                    return '-'
            return '-'
        expiration_status.short_description = 'Expiration'

        def make_primary(self, request, queryset):
            """Make selected payment methods primary"""
            for payment_method in queryset:
                # Remove primary from other methods of same user
                PaymentMethods.objects.filter(
                    user=payment_method.user,
                    primary=True
                ).update(primary=False)

                # Set this one as primary
                payment_method.primary = True
                payment_method.save()

            self.message_user(request, f'✅ {queryset.count()} payment methods set as primary')
        make_primary.short_description = '⭐ Make primary'

        def remove_primary(self, request, queryset):
            """Remove primary status"""
            updated = queryset.update(primary=False)
            self.message_user(request, f'✅ {updated} payment methods set as secondary')
        remove_primary.short_description = '☆ Remove primary'

        def mask_sensitive_data(self, request, queryset):
            """For demo - mask sensitive payment data"""
            messages.warning(request, 'This would mask sensitive data in production')
        mask_sensitive_data.short_description = '🔒 Mask sensitive data'

        def save_model(self, request, obj, form, change):
            """Auto-generate payment_method_id if not provided"""
            if not obj.payment_method_id:
                import uuid
                obj.payment_method_id = f"PM_{uuid.uuid4().hex[:8].upper()}"

            # If setting as primary, remove primary from others
            if obj.primary and obj.user:
                PaymentMethods.objects.filter(
                    user=obj.user,
                    primary=True
                ).exclude(pk=obj.pk).update(primary=False)

            super().save_model(request, obj, form, change)


# ================== CUSTOM FORMS FOR USER ==================
class MainUserCreationForm(forms.ModelForm):
    """Form لإنشاء مستخدم جديد"""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)
    use_hash = forms.BooleanField(label='Use password hash directly', required=False,
                                  help_text='Check this if password1 contains a hash')

    class Meta:
        model = MainUser
        fields = ('username',)

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        use_hash = self.cleaned_data.get("use_hash")

        if not use_hash and password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("use_hash"):
            # استخدم الـ hash مباشرة
            user.password = self.cleaned_data["password1"]
        else:
            # اعمل hash للـ password العادي
            user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class MainUserChangeForm(forms.ModelForm):
    """Form لتعديل المستخدم"""
    password = ReadOnlyPasswordHashField(
        label="Password",
        help_text='Raw passwords are not stored. You can change password below.'
    )

    # حقول إضافية للـ password
    new_password = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput,
        required=False,
        help_text='Leave blank to keep current password'
    )
    new_password_hash = forms.CharField(
        label='OR: Paste Password Hash',
        widget=forms.Textarea(attrs={'rows': 2, 'cols': 80}),
        required=False,
        help_text='Advanced: Paste a pre-computed password hash (e.g., pbkdf2_sha256$...)'
    )

    class Meta:
        model = MainUser
        fields = ('username', 'password', 'is_active', 'is_staff', 'is_superuser')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].help_text = (
            f'Current hash: <code style="font-size:10px">{self.instance.password[:50]}...</code>'
        )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        new_password_hash = cleaned_data.get('new_password_hash')

        if new_password and new_password_hash:
            raise forms.ValidationError("Please provide either a password OR a hash, not both")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        new_password_hash = self.cleaned_data.get('new_password_hash')

        if new_password:
            user.set_password(new_password)
        elif new_password_hash:
            user.password = new_password_hash

        if commit:
            user.save()
        return user


# ==================  USERS ADMIN ==================
if MAIN_USER_AVAILABLE:
    @admin.register(MainUser)
    class MainUserAdmin(BaseUserAdmin):
        # استخدم الـ forms المخصصة
        form = MainUserChangeForm
        add_form = MainUserCreationForm

        list_display = [
            'id', 'username', 'is_active', 'is_staff',
            'has_p2p_profile', 'wallet_count', 'last_login'
        ]

        list_filter = ['is_active', 'is_staff', 'is_superuser']
        search_fields = ['username', 'id']
        ordering = ['id']

        # تخصيص fieldsets للـ edit form
        fieldsets = (
            (None, {'fields': ('username', 'password')}),
            ('Change Password', {
                'fields': ('new_password', 'new_password_hash'),
                'classes': ('collapse',),
                'description': 'Use ONE of these options to change password'
            }),
            ('Permissions', {
                'fields': ('is_active', 'is_staff', 'is_superuser'),
            }),
            ('Important dates', {'fields': ('last_login',)}),
        )

        # تخصيص add_fieldsets للـ create form
        add_fieldsets = (
            (None, {
                'classes': ('wide',),
                'fields': ('username', 'password1', 'password2', 'use_hash'),
            }),
            ('P2P Setup', {
                'fields': (),
                'description': '✅ P2P Profile and Wallets will be created automatically'
            }),
        )

        readonly_fields = ['last_login']

        def save_model(self, request, obj, form, change):
            """Override save_model to create P2P profile automatically"""
            is_new = obj.pk is None  # Check if it's a new user

            # Save the user first
            super().save_model(request, obj, form, change)

            # If it's a new user, create P2P profile and wallets
            if is_new:
                try:
                    # Create P2P Profile
                    p2p_profile, created = P2PProfile.objects.get_or_create(
                        user_id=obj.id,
                        defaults={'nickname': f"{obj.username}_p2p"}
                    )

                    if created:
                        messages.success(
                            request,
                            f'✅ P2P Profile created automatically for {obj.username}'
                        )

                    # Create basic wallets
                    currencies = ['USDT']
                    wallets_created = 0

                    for currency in currencies:
                        wallet, wallet_created = Wallet.objects.get_or_create(
                            user_id=obj.id,
                            currency=currency,
                            defaults={'balance': 0, 'locked_balance': 0}
                        )
                        if wallet_created:
                            wallets_created += 1

                    if wallets_created:
                        messages.success(
                            request,
                            f'💰 {wallets_created} wallets created automatically'
                        )

                    # Create Main wallets too
                    if MAIN_USER_AVAILABLE:
                        main_wallets_created = 0
                        for currency in currencies:
                            main_wallet, mw_created = MainWallet.objects.get_or_create(
                                user=obj,
                                currency=currency,
                                defaults={'balance': 2000}
                            )
                            if mw_created:
                                main_wallets_created += 1

                        if main_wallets_created:
                            messages.success(
                                request,
                                f'🏦 {main_wallets_created} main wallets created'
                            )

                except Exception as e:
                    messages.error(
                        request,
                        f'❌ Error creating P2P setup: {str(e)}'
                    )

        def response_add(self, request, obj, post_url_continue=None):
            """After adding a user, redirect to their P2P profile"""
            response = super().response_add(request, obj, post_url_continue)

            # If user was created successfully, show option to go to P2P profile
            if '_save' in request.POST:
                try:
                    profile = P2PProfile.objects.get(user_id=obj.id)
                    profile_url = reverse('admin:p2p_trading_p2pprofile_change', args=[profile.id])
                    messages.info(
                        request,
                        format_html(
                            'View <a href="{}">P2P Profile for {}</a>',
                            profile_url,
                            obj.username
                        )
                    )
                except P2PProfile.DoesNotExist:
                    pass

            return response

        actions = [
            'create_p2p_profile_for_users',
            'create_basic_wallets_for_users',
            'create_complete_p2p_setup',
            'delete_users_with_cleanup',
            'deactivate_users',
            'reset_password_to_username',
            'show_password_hashes'
        ]

        def reset_password_to_username(self, request, queryset):
            """Reset password to be same as username (for testing)"""
            updated = 0
            for user in queryset:
                user.set_password(user.username)
                user.save()
                updated += 1

            self.message_user(request, f'🔐 {updated} passwords reset to username')
        reset_password_to_username.short_description = '🔐 Reset password = username (TEST ONLY)'

        def show_password_hashes(self, request, queryset):
            """Show password hashes for selected users"""
            user_hashes = []
            for user in queryset[:5]:  # حد أقصى 5 users
                user_hashes.append(f"{user.username}: {user.password}")

            if user_hashes:
                messages.info(request, "Password hashes:\n" + "\n".join(user_hashes))
            else:
                messages.warning(request, "No users selected")
        show_password_hashes.short_description = '👁️ Show password hashes'

        # ... باقي الدوال كما هي ...
        def has_p2p_profile(self, obj):
            """Check if user has P2P profile"""
            has_profile = P2PProfile.objects.filter(user_id=obj.id).exists()
            if has_profile:
                profile = P2PProfile.objects.get(user_id=obj.id)
                url = reverse('admin:p2p_trading_p2pprofile_change', args=[profile.id])
                return format_html(
                    '<a href="{}" style="color: green;">✓ Yes</a>', url
                )
            return format_html('<span style="color: red;">✗ No</span>')
        has_p2p_profile.short_description = 'P2P Profile'

        def wallet_count(self, obj):
            """Count user's P2P wallets"""
            count = Wallet.objects.filter(user_id=obj.id).count()
            if count > 0:
                return format_html(
                    '<span style="color: green; font-weight: bold;">{} wallets</span>',
                    count
                )
            return format_html('<span style="color: red;">No wallets</span>')
        wallet_count.short_description = 'P2P Wallets'

        def create_p2p_profile_for_users(self, request, queryset):
            """Create P2P profiles for selected users"""
            created_count = 0
            errors = []

            for user in queryset:
                try:
                    # Check if profile already exists
                    if not P2PProfile.objects.filter(user_id=user.id).exists():
                        P2PProfile.objects.create(
                            user_id=user.id,
                            nickname=f"{user.username}_p2p"  # Auto-generate nickname
                        )
                        created_count += 1
                    else:
                        errors.append(f"User {user.username} already has P2P profile")
                except Exception as e:
                    errors.append(f"Error creating profile for {user.username}: {str(e)}")

            if created_count:
                self.message_user(request, f'{created_count} P2P profiles created successfully.')
            if errors:
                for error in errors:
                    messages.warning(request, error)

        create_p2p_profile_for_users.short_description = 'Create P2P profiles for selected users'

        def create_basic_wallets_for_users(self, request, queryset):
            """Create basic wallets for selected users"""
            currencies = ['BTC', 'USDT', 'ETH']  # يمكنك تعديل هذه القائمة
            created_count = 0

            for user in queryset:
                for currency in currencies:
                    wallet, created = Wallet.objects.get_or_create(
                        user_id=user.id,
                        currency=currency,
                        defaults={'balance': 0, 'locked_balance': 0}
                    )
                    if created:
                        created_count += 1

            self.message_user(request, f'{created_count} wallets created.')

        create_basic_wallets_for_users.short_description = 'Create basic wallets (BTC, USDT, ETH)'

        def create_complete_p2p_setup(self, request, queryset):
            """Create complete P2P setup (profile + wallets) for selected users"""
            currencies = ['BTC', 'USDT', 'ETH']
            profiles_created = 0
            wallets_created = 0
            errors = []

            for user in queryset:
                try:
                    # Create P2P Profile if doesn't exist
                    profile, profile_created = P2PProfile.objects.get_or_create(
                        user_id=user.id,
                        defaults={'nickname': f"{user.username}_p2p"}
                    )
                    if profile_created:
                        profiles_created += 1

                    # Create wallets
                    for currency in currencies:
                        wallet, wallet_created = Wallet.objects.get_or_create(
                            user_id=user.id,
                            currency=currency,
                            defaults={'balance': 0, 'locked_balance': 0}
                        )
                        if wallet_created:
                            wallets_created += 1

                except Exception as e:
                    errors.append(f"Error setting up {user.username}: {str(e)}")

            success_msg = f'Complete setup: {profiles_created} profiles + {wallets_created} wallets created.'
            self.message_user(request, success_msg)

            if errors:
                for error in errors:
                    messages.error(request, error)

        create_complete_p2p_setup.short_description = 'Create complete P2P setup (Profile + Wallets)'

        def get_queryset(self, request):
            """Customize queryset if needed"""
            return super().get_queryset(request)

        def delete_users_with_cleanup(self, request, queryset):
            """Delete users with all related data"""
            # Filter out superusers for safety
            queryset = queryset.filter(is_superuser=False)

            if not queryset.exists():
                messages.error(request, '❌ Cannot delete superusers!')
                return

            deleted_count = 0
            with transaction.atomic():
                for user in queryset:
                    # Delete P2P data
                    P2PProfile.objects.filter(user_id=user.id).delete()
                    Wallet.objects.filter(user_id=user.id).delete()
                    P2POffer.objects.filter(user_id=user.id).delete()

                    # Delete main wallets
                    if MAIN_USER_AVAILABLE:
                        MainWallet.objects.filter(user=user).delete()

                    # Finally delete user
                    user.delete()
                    deleted_count += 1

            self.message_user(request, f'🗑️ {deleted_count} users deleted with all data')
        delete_users_with_cleanup.short_description = '🗑️ Delete users + ALL data (DANGEROUS!)'

        def deactivate_users(self, request, queryset):
            """Deactivate users instead of deleting"""
            updated = queryset.update(is_active=False)
            # Also deactivate their offers
            user_ids = list(queryset.values_list('id', flat=True))
            P2POffer.objects.filter(user_id__in=user_ids).update(status='INACTIVE')

            self.message_user(request, f'🚫 {updated} users deactivated')
        deactivate_users.short_description = '🚫 Deactivate users (safer than delete)'

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
        available_str = f"{obj.available_amount:.8f}"
        total_str = f"{obj.total_amount:.8f}"
        percentage_str = f"{percentage:.1f}"
        return format_html('{} / {} ({}%)', available_str, total_str, percentage_str)

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
        crypto_str = f"{obj.crypto_amount:.8f}"
        fiat_str = f"{obj.fiat_amount:.2f}"
        return format_html(
            '{} {} = {} {}',
            crypto_str, obj.crypto_currency,
            fiat_str, obj.fiat_currency
        )

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
        'user_id_link', 'nickname', 'total_30d_trades',
        'completion_rate_display', 'feedback_display',
        'created_at'
    ]

    list_filter = [
        'created_at',
    ]

    search_fields = ['user_id', 'nickname']

    readonly_fields = [
        'created_at', 'updated_at', 'total_30d_trades',
        'completion_rate_30d', 'avg_release_time_minutes',
        'avg_pay_time_minutes', 'positive_feedback_count',
        'positive_feedback_rate'
    ]

    actions = ['create_wallets_for_profiles', 'create_user_and_profile']

    def user_id_link(self, obj):
        """Create clickable link to user with username if available"""
        if MAIN_USER_AVAILABLE:
            try:
                main_user = MainUser.objects.get(id=obj.user_id)
                url = reverse('admin:MainDashboard_mainuser_change', args=[obj.user_id])
                return format_html(
                    '<a href="{}" title="View Main User">User #{} ({})</a>',
                    url, obj.user_id, main_user.username
                )
            except MainUser.DoesNotExist:
                return format_html(
                    '<span style="color: red;" title="User not found">User #{} (Not Found)</span>',
                    obj.user_id
                )
        return f"User #{obj.user_id}"
    user_id_link.short_description = 'User'

    def create_wallets_for_profiles(self, request, queryset):
        """Create wallets for selected P2P profiles"""
        currencies = ['BTC', 'USDT', 'ETH']
        created_count = 0

        for profile in queryset:
            for currency in currencies:
                wallet, created = Wallet.objects.get_or_create(
                    user_id=profile.user_id,
                    currency=currency,
                    defaults={'balance': 0, 'locked_balance': 0}
                )
                if created:
                    created_count += 1

        self.message_user(request, f'{created_count} wallets created for selected profiles.')
    create_wallets_for_profiles.short_description = 'Create wallets for selected profiles'

    def create_user_and_profile(self, request, queryset):
        """Redirect to create new user (if MainUser is available)"""
        if MAIN_USER_AVAILABLE:
            messages.info(request, 'To create a new user with profile, use the MainUser admin and select "Create complete P2P setup"')
            return HttpResponseRedirect(reverse('admin:MainDashboard_mainuser_changelist'))
        else:
            messages.error(request, 'MainUser model not available. Please create user manually.')
    create_user_and_profile.short_description = 'Create new user with profile'

    def completion_rate_display(self, obj):
        """Display completion rate with color"""
        rate = obj.completion_rate_30d
        color = 'green' if rate >= 95 else 'orange' if rate >= 80 else 'red'
        rate_str = f"{rate:.1f}"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, rate_str
        )
    completion_rate_display.short_description = 'Completion Rate'

    def feedback_display(self, obj):
        """Display feedback stats"""
        rate_str = f"{obj.positive_feedback_rate:.1f}"
        return format_html(
            '{} positive ({}%)',
            obj.positive_feedback_count,
            rate_str
        )
    feedback_display.short_description = 'Feedback'

# ================== WALLET ADMIN ==================
@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = [
        'user_id_display', 'currency', 'balance', 'locked_balance',
        'available_balance_display', 'created_at'
    ]

    list_filter = ['currency', 'created_at']
    search_fields = ['user_id', 'currency']
    readonly_fields = ['created_at', 'updated_at']

    actions = ['create_missing_wallets', 'zero_balances']

    def user_id_display(self, obj):
        """Display user ID with username if available"""
        if MAIN_USER_AVAILABLE:
            try:
                main_user = MainUser.objects.get(id=obj.user_id)
                url = reverse('admin:MainDashboard_mainuser_change', args=[obj.user_id])
                return format_html(
                    '<a href="{}" title="View Main User">User #{} ({})</a>',
                    url, obj.user_id, main_user.username
                )
            except MainUser.DoesNotExist:
                return format_html(
                    '<span style="color: red;">User #{} (Not Found)</span>',
                    obj.user_id
                )
        return f"User #{obj.user_id}"
    user_id_display.short_description = 'User'
    user_id_display.admin_order_field = 'user_id'

    def available_balance_display(self, obj):
        """Display available balance"""
        available = obj.balance - obj.locked_balance
        available_str = f"{available:.8f}"
        return format_html(
            '<span style="color: green; font-weight: bold;">{}</span>',
            available_str
        )
    available_balance_display.short_description = 'Available'

    def create_missing_wallets(self, request, queryset):
        """Create missing wallets for users who have some but not all currencies"""
        currencies = ['BTC', 'USDT', 'ETH']
        created_count = 0

        # Get unique user_ids from selected wallets
        user_ids = set(queryset.values_list('user_id', flat=True))

        for user_id in user_ids:
            for currency in currencies:
                wallet, created = Wallet.objects.get_or_create(
                    user_id=user_id,
                    currency=currency,
                    defaults={'balance': 0, 'locked_balance': 0}
                )
                if created:
                    created_count += 1

        self.message_user(request, f'{created_count} missing wallets created.')
    create_missing_wallets.short_description = 'Create missing wallets for selected users'

    def zero_balances(self, request, queryset):
        """Zero out balances for selected wallets (be careful!)"""
        updated = queryset.update(balance=0, locked_balance=0)
        self.message_user(request, f'{updated} wallets zeroed out.')
    zero_balances.short_description = '⚠️ Zero out balances (DANGEROUS)'

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
        amount_str = f"{obj.amount:+.8f}"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, amount_str
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