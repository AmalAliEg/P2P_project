# p2p_trading/models/p2p_profile_models.py

from django.db import models
from .p2p_BaseModel import BaseModel

class P2PProfile(BaseModel):
    """main model for the  P2P user profile"""
    user_id = models.PositiveIntegerField(unique=True, help_text="ID of the user in the main service")
    nickname = models.CharField(max_length=50, unique=True)

    #  updated statistics
    total_30d_trades = models.IntegerField(default=0)
    completion_rate_30d = models.FloatField(default=100.0)
    avg_release_time_minutes = models.FloatField(default=0.0)
    avg_pay_time_minutes = models.FloatField(default=0.0)
    positive_feedback_count = models.IntegerField(default=0)
    positive_feedback_rate = models.FloatField(default=100.0)

    class Meta:
        db_table = 'p2p_profile'
        app_label = 'p2p_trading'
        ordering = ['-total_30d_trades']

    def __str__(self):
        return f"P2P Profile for {self.nickname}"


class Feedback(BaseModel):
    """feedback model for the  P2P user profile"""
    reviewer = models.ForeignKey(P2PProfile, on_delete=models.CASCADE, related_name='given_feedback')
    reviewee = models.ForeignKey(P2PProfile, on_delete=models.CASCADE, related_name='received_feedback')
    order = models.ForeignKey('p2p_trading.P2POrder', on_delete=models.CASCADE)
    is_positive = models.BooleanField()
    comment = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'p2p_feedback'
        app_label = 'p2p_trading'
        unique_together = ['reviewer', 'order']


class Follow(BaseModel):
    """the relationship between the users"""
    follower = models.ForeignKey(P2PProfile, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(P2PProfile, on_delete=models.CASCADE, related_name='followers')

    class Meta:
        db_table = 'p2p_follow'
        app_label = 'p2p_trading'
        unique_together = ('follower', 'followed')


class BlockedUser(BaseModel):
    """the blocking process and relationship between the users"""
    blocker = models.ForeignKey(P2PProfile, on_delete=models.CASCADE, related_name='blocking')
    blocked = models.ForeignKey(P2PProfile, on_delete=models.CASCADE, related_name='blocked_by')

    class Meta:
        db_table = 'p2p_blocked_user'
        app_label = 'p2p_trading'
        unique_together = ('blocker', 'blocked')




