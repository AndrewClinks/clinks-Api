# Generated by Django 4.0.1 on 2022-03-09 17:11

import api.utils.Fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0022_availability'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='venue',
            name='venue_count',
        ),
        migrations.AddField(
            model_name='driver',
            name='total_accept_time',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='venue',
            name='currency',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='menus', to='api.currency'),
        ),
        migrations.AddField(
            model_name='venue',
            name='service_fee_percentage',
            field=models.DecimalField(decimal_places=4, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='venue',
            name='total_accept_time',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='alltimestat',
            name='type',
            field=api.utils.Fields.EnumField(choices=[('company_count', 'company_count'), ('driver_count', 'driver_count'), ('venue_count', 'venue_count'), ('total_earnings', 'total_earnings'), ('total_company_earnings', 'total_company_earnings'), ('total_driver_earnings', 'total_driver_earnings'), ('platform_earnings', 'platform_earnings'), ('sales_count', 'sales_count'), ('delivered_order_count', 'delivered_order_count'), ('cancelled_order_count', 'cancelled_order_count'), ('rejected_order_count', 'rejected_order_count'), ('average_wait_time', 'average_wait_time')], default='company_count'),
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('amount', models.PositiveIntegerField()),
                ('tip', models.PositiveIntegerField(default=0)),
                ('total', models.PositiveIntegerField()),
                ('service_fee', models.PositiveIntegerField()),
                ('delivery_fee', models.PositiveIntegerField()),
                ('stripe_fee', models.PositiveIntegerField(default=0)),
                ('stripe_charge_id', models.CharField(max_length=255, null=True)),
                ('stripe_refund_id', models.CharField(max_length=255, null=True)),
                ('paid_at', models.DateTimeField()),
                ('refunded_at', models.DateTimeField(null=True)),
                ('card', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='api.card')),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='api.currency')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='api.customer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('status', api.utils.Fields.EnumField(choices=[('pending', 'pending'), ('looking_for_driver', 'looking_for_driver'), ('accepted', 'accepted'), ('rejected', 'rejected')], default='pending')),
                ('delivery_status', api.utils.Fields.EnumField(choices=[('pending', 'pending'), ('out_for_delivery', 'out_for_delivery'), ('failed', 'failed'), ('returned', 'returned'), ('delivered', 'delivered')], default='pending')),
                ('identification_status', api.utils.Fields.EnumField(choices=[('not_requested', 'not_requested'), ('not_provided', 'not_provided'), ('provided', 'provided')], default='not_requested')),
                ('accepted_at', models.DateTimeField(null=True)),
                ('collected_at', models.DateTimeField(null=True)),
                ('rejected_at', models.DateTimeField(null=True)),
                ('failed_at', models.DateTimeField(null=True)),
                ('delivered_at', models.DateTimeField(null=True)),
                ('data', models.JSONField()),
                ('driver_verification_number', models.PositiveIntegerField()),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='api.customer')),
                ('driver', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='api.driver')),
                ('identification', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order', to='api.identification')),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='api.payment')),
                ('venue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='api.venue')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DailyStat',
            fields=[
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('type', api.utils.Fields.EnumField(choices=[('sales_count', 'sales_count'), ('total_earnings', 'total_earnings'), ('total_company_earnings', 'total_company_earnings'), ('total_driver_earnings', 'total_driver_earnings'), ('platform_earnings', 'platform_earnings')], default='sales_count')),
                ('value', models.PositiveIntegerField(default=0)),
                ('company', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='daily_stats', to='api.company')),
                ('venue', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='daily_stats', to='api.venue')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
