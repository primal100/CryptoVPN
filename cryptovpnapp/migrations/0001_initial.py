# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-27 22:10
from __future__ import unicode_literals

import cryptovpnapp.fields
import datetime
from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Address',
            fields=[
                ('public', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('coin', models.CharField(choices=[('BTC', 'BITCOIN'), ('BTCTEST', 'BITCOIN TESTNET'), ('ETH', 'ETHEREUM')], max_length=12)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Comments',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('crypto_due', cryptovpnapp.fields.CryptoField(decimal_places=20, max_digits=20)),
                ('fiat_due', cryptovpnapp.fields.FiatField(decimal_places=2, max_digits=8)),
                ('currency', models.CharField(max_length=12)),
                ('start_time', models.DateTimeField(auto_now_add=True)),
                ('expiry_time', models.DateTimeField()),
                ('paid', models.BooleanField(default=False)),
                ('paid_time', models.DateTimeField(null=True)),
                ('actual_paid', cryptovpnapp.fields.CryptoField(decimal_places=20, max_digits=20)),
                ('address', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='cryptovpnapp.Address')),
            ],
        ),
        migrations.CreateModel(
            name='RefundRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_id', models.CharField(max_length=64, null=True)),
                ('amount_requested', cryptovpnapp.fields.CryptoField(decimal_places=20, max_digits=20, null=True)),
                ('reqested_on', models.DateTimeField(auto_now_add=True)),
                ('text', models.TextField(null=True)),
                ('address', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='refund_requests', to='cryptovpnapp.Address')),
                ('invoice', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='refund_requests', to='cryptovpnapp.Invoice')),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_subscribed', models.DateTimeField(null=True, verbose_name='last subscribed')),
                ('subscription_expires', models.DateTimeField(null=True, verbose_name='subscription expires')),
                ('auto_renewal', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='SubscriptionType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=48)),
                ('price', cryptovpnapp.fields.FiatField(decimal_places=2, default=7.99, max_digits=8)),
                ('currency', models.CharField(default='USD', max_length=12)),
                ('period', models.DurationField(default=datetime.timedelta(30))),
                ('is_active', models.BooleanField(default=True)),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscription_types', to='cryptovpnapp.Service')),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('hash', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('time', models.DateTimeField()),
                ('coin', models.CharField(choices=[('BTC', 'BITCOIN'), ('BTCTEST', 'BITCOIN TESTNET'), ('ETH', 'ETHEREUM')], max_length=12)),
                ('total_value', cryptovpnapp.fields.CryptoField(decimal_places=20, max_digits=20)),
                ('fee', cryptovpnapp.fields.CryptoField(decimal_places=20, max_digits=20)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cryptovpnapp.Invoice')),
            ],
        ),
        migrations.AddField(
            model_name='subscription',
            name='subscription_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='cryptovpnapp.SubscriptionType', verbose_name='subscription type'),
        ),
        migrations.AddField(
            model_name='subscription',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='refundrequest',
            name='service',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='refund_requests', to='cryptovpnapp.Service'),
        ),
        migrations.AddField(
            model_name='refundrequest',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refund_requests', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='comments',
            name='refund_request',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='cryptovpnapp.RefundRequest'),
        ),
        migrations.AddField(
            model_name='comments',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='address',
            name='subscription',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='cryptovpnapp.Subscription'),
        ),
    ]
