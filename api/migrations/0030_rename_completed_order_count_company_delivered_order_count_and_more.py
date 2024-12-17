# Generated by Django 4.0.1 on 2022-03-29 14:19

import api.utils.Fields
import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0029_alter_payment_company'),
    ]

    operations = [
        migrations.RenameField(
            model_name='company',
            old_name='completed_order_count',
            new_name='delivered_order_count',
        ),
        migrations.AddField(
            model_name='driver',
            name='delivered_order_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='order',
            name='no_answer_driver_location',
            field=django.contrib.gis.db.models.fields.PointField(null=True, srid=4326),
        ),
        migrations.AddField(
            model_name='order',
            name='no_answer_image',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_as_no_answer_image', to='api.image'),
        ),
        migrations.AlterField(
            model_name='alltimestat',
            name='type',
            field=api.utils.Fields.EnumField(choices=[('company_count', 'company_count'), ('driver_count', 'driver_count'), ('venue_count', 'venue_count'), ('total_earnings', 'total_earnings'), ('total_company_earnings', 'total_company_earnings'), ('total_driver_earnings', 'total_driver_earnings'), ('platform_earnings', 'platform_earnings'), ('sales_count', 'sales_count'), ('delivered_order_count', 'delivered_order_count'), ('cancelled_order_count', 'cancelled_order_count'), ('rejected_order_count', 'rejected_order_count'), ('average_wait_time', 'average_wait_time'), ('customer_count', 'customer_count'), ('total_wait_time', 'total_wait_time')], default='company_count'),
        ),
        migrations.AlterField(
            model_name='order',
            name='identification_status',
            field=api.utils.Fields.EnumField(choices=[('not_requested', 'not_requested'), ('not_required', 'not_required'), ('refused', 'refused'), ('not_provided', 'not_provided'), ('provided', 'provided')], default='not_requested'),
        ),
        migrations.CreateModel(
            name='DriverPayment',
            fields=[
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('amount', models.PositiveIntegerField()),
                ('type', api.utils.Fields.EnumField(choices=[('delivery', 'delivery'), ('return', 'return')], default='delivery')),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='driver_payments', to='api.currency')),
                ('driver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='api.driver')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='driver_payments', to='api.order')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]