# Generated by Django 5.2.3 on 2025-07-16 00:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('p2p_trading', '0004_wallet_transaction'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='p2pprofile',
            name='enable_sound_notifications',
        ),
        migrations.AddField(
            model_name='p2pprofile',
            name='avg_pay_time_minutes',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='p2pprofile',
            name='avg_release_time_minutes',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='p2pprofile',
            name='positive_feedback_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='p2pprofile',
            name='positive_feedback_rate',
            field=models.FloatField(default=100.0),
        ),
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('is_positive', models.BooleanField()),
                ('comment', models.TextField(blank=True, null=True)),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='p2p_trading.p2porder')),
                ('reviewee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_feedback', to='p2p_trading.p2pprofile')),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='given_feedback', to='p2p_trading.p2pprofile')),
            ],
            options={
                'db_table': 'p2p_feedback',
            },
        ),
        migrations.CreateModel(
            name='UserPaymentMethod',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('method_type', models.CharField(choices=[('INSTAPAY', 'InstaPay'), ('BANK_TRANSFER', 'Bank Transfer'), ('VODAFONE_CASH', 'Vodafone Cash'), ('ORANGE_CASH', 'Orange Cash'), ('ETISALAT_CASH', 'Etisalat Cash'), ('WE_PAY', 'WE Pay')], max_length=50)),
                ('account_name', models.CharField(max_length=100)),
                ('account_number', models.CharField(blank=True, max_length=100)),
                ('extra_details', models.JSONField(blank=True, default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_methods', to='p2p_trading.p2pprofile')),
            ],
            options={
                'db_table': 'p2p_user_payment_method',
            },
        ),
        migrations.CreateModel(
            name='BlockedUser',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('blocked', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocked_by', to='p2p_trading.p2pprofile')),
                ('blocker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocking', to='p2p_trading.p2pprofile')),
            ],
            options={
                'db_table': 'p2p_blocked_user',
                'unique_together': {('blocker', 'blocked')},
            },
        ),
        migrations.CreateModel(
            name='Follow',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('followed', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followers', to='p2p_trading.p2pprofile')),
                ('follower', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='following', to='p2p_trading.p2pprofile')),
            ],
            options={
                'db_table': 'p2p_follow',
                'unique_together': {('follower', 'followed')},
            },
        ),
    ]
