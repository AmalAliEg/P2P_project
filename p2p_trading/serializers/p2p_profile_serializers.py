# p2p_trading/serializers/p2p_profile_serializers.py

from rest_framework import serializers
from ..models import P2PProfile
from ..helpers import FORMAT_PERCENTAGE, FORMAT_TIME




class P2PProfileOverviewSerializer(serializers.ModelSerializer):
    """Serializer to show the user profile"""
    # data
    username = serializers.SerializerMethodField()

    #  statistics
    completion_rate_display = serializers.SerializerMethodField()
    avg_release_time_display = serializers.SerializerMethodField()
    avg_pay_time_display = serializers.SerializerMethodField()
    positive_feedback_display = serializers.SerializerMethodField()

    # metrix
    payment_methods_count = serializers.IntegerField(read_only=True)
    feedback_count = serializers.IntegerField(read_only=True)
    blocked_users_count = serializers.IntegerField(read_only=True)
    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = P2PProfile
        fields = [
            'nickname', 'username',
            'total_30d_trades', 'completion_rate_30d', 'completion_rate_display',
            'avg_release_time_minutes', 'avg_release_time_display',
            'avg_pay_time_minutes', 'avg_pay_time_display',
            'positive_feedback_count', 'positive_feedback_rate', 'positive_feedback_display',
            'payment_methods_count', 'feedback_count', 'blocked_users_count',
            'followers_count', 'following_count'
        ]

    def get_username(self, obj):
        user_data = self.context.get('user_data', {})
        return user_data.get('username', f'User{obj.user_id}')


    def get_completion_rate_display(self, obj):
        return FORMAT_PERCENTAGE(obj.completion_rate_30d)

    def get_avg_release_time_display(self, obj):
        return FORMAT_TIME(obj.avg_release_time_minutes)

    def get_avg_pay_time_display(self, obj):
        return FORMAT_TIME(obj.avg_pay_time_minutes)

    def get_positive_feedback_display(self, obj):
        return f"{FORMAT_PERCENTAGE(obj.positive_feedback_rate)} ({obj.positive_feedback_count})"


class P2PProfileUpdateSerializer(serializers.Serializer):
    """Serializer to update P2PProfile"""
    nickname = serializers.CharField(max_length=50, required=False)


class PaymentMethodCreateSerializer(serializers.Serializer):
    """Serializer to add payment methods"""
    method_type = serializers.CharField(max_length=50)
    account_name = serializers.CharField(max_length=100)
    account_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    extra_details = serializers.JSONField(required=False, default=dict)

class MainPaymentMethodSerializer(serializers.Serializer):
    """Serializer to show the payment methods from MainDashboard"""
    id = serializers.IntegerField()
    payment_method_id = serializers.CharField()
    type = serializers.CharField()
    holder_name = serializers.CharField()
    number = serializers.CharField()
    primary = serializers.BooleanField()







