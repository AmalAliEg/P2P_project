#MainDashboard/models.py
# MainDashboard/models.py
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

# 1. مدير مستخدمين بسيط جدًا
class MainUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **extra_fields)
        # set_password يقوم بالتشفير، وهو ضروري حتى لو لن تستخدمه لتسجيل الدخول
        user.set_password(password)
        user.save(using=self._db)
        return user

    # لسنا بحاجة لـ create_superuser الآن
    def create_superuser(self, username, password=None, **extra_fields):
        # يمكنك جعلها تثير خطأ لمنع إنشائها
        raise NotImplementedError('Superuser creation is not supported for this user model.')


# 2. موديل مستخدم بسيط جدًا
class MainUser(AbstractBaseUser):
    # Django سيضيف حقل id تلقائيًا (AutoField)
    username = models.CharField(max_length=100, unique=True)

    # هذا الحقل مطلوب بواسطة AbstractBaseUser، لكن يمكننا تركه فارغًا
    # password = models.CharField(max_length=128) -> هذا الحقل يأتي من AbstractBaseUser

    # ربط الموديل بالمدير الخاص به
    objects = MainUserManager()

    # تحديد الحقل الذي سيستخدم لتحديد هوية المستخدم
    USERNAME_FIELD = 'username'

    def __str__(self):
        return self.username

    # الدوال التالية مطلوبة بواسطة Django Admin، يمكن تركها فارغة
    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # أبسط إجابة ممكنة: لا
        return False

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # أبسط إجابة ممكنة: لا
        return False

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # أبسط إجابة ممكنة
        return False

    class Meta:
        db_table = 'main_user'
        app_label = 'MainDashboard'
        verbose_name_plural = 'MainUsers'
        ordering = ['username']




class PaymentMethods(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_methods',
        null=True,
    )
    payment_method_id = models.CharField(max_length=255)
    type = models.CharField(max_length=255, null=True, blank=True)
    number = models.CharField(max_length=255, null=True, blank=True)
    expiration_date = models.CharField(max_length=255, null=True, blank=True)
    holder_name = models.CharField(max_length=255, null=True, blank=True)
    primary = models.BooleanField(default=False)
    class Meta:
        db_table = 'payment_methods'
        app_label = 'MainDashboard'
        verbose_name_plural = 'PaymentMethods'
        ordering = ['type']



# - إضافة نموذج المحفظة

class MainWallet(models.Model):
    """المحفظة الرئيسية للمستخدم"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallets'
    )
    currency = models.CharField(max_length=10, db_index=True)  # BTC, USDT, EGP
    balance = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=0
    )

    # معلومات إضافية
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'main_wallet'
        app_label = 'MainDashboard'
        unique_together = ('user', 'currency')

    def __str__(self):
        return f"{self.user.username} - {self.currency}: {self.balance}"


class MainTransaction(models.Model):
    """سجل المعاملات في المحفظة الرئيسية"""
    wallet = models.ForeignKey(
        MainWallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=[
            ('DEPOSIT', 'Deposit'),
            ('WITHDRAWAL', 'Withdrawal'),
            ('TRANSFER_TO_P2P', 'Transfer to P2P'),
            ('TRANSFER_FROM_P2P', 'Transfer from P2P'),
            ('TRANSFER_TO_AUTO', 'Transfer to Auto Trading'),
            ('TRANSFER_FROM_AUTO', 'Transfer from Auto Trading'),
        ]
    )
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    reference = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'main_transaction'
        app_label = 'MainDashboard'
        ordering = ['-created_at']