# p2p_trading/serializers/p2p_profile_serializer.py

from rest_framework import serializers
from ..models import P2PProfile,Feedback
from MainDashboard.models import PaymentMethods
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
            'total_30d_trades',  'completion_rate_display',
            'avg_release_time_display',
            'avg_pay_time_display',
            'positive_feedback_count',  'positive_feedback_display',
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

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethods
        fields = ['id', 'payment_method_id', 'type', 'holder_name', 'number', 'primary']
        read_only_fields = ['id', 'payment_method_id', 'type']



class FeedbackSerializer(serializers.ModelSerializer):
    """Serializer for the feedback model"""
    reviewer_nickname = serializers.CharField(source='reviewer.nickname', read_only=True)
    order_id = serializers.IntegerField(source='order.id', read_only=True)

    class Meta:
        model = Feedback
        fields = ['id', 'order_id','reviewer_nickname', 'is_positive', 'comment', 'created_at']
        read_only_fields = ['id', 'reviewer_nickname', 'created_at']

class FeedbackCreateSerializer(serializers.Serializer):
    """Serializer to create a new feedback"""
    order_id = serializers.IntegerField()
    is_positive = serializers.BooleanField()
    comment = serializers.CharField(required=False, allow_blank=True)



class BlockUserSerializer(serializers.Serializer):
    """Serializer for blocking users"""
    user_id = serializers.IntegerField()


class FollowUserSerializer(serializers.Serializer):
    """Serializer for blocking users"""
    user_id = serializers.IntegerField()



