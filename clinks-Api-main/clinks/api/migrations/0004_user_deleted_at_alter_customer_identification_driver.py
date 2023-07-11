# Generated by Django 4.0.1 on 2022-01-19 16:57

import api.utils.Fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_image_setting_identification_customer'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='customer',
            name='identification',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='customers', to='api.identification'),
        ),
        migrations.CreateModel(
            name='Driver',
            fields=[
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='driver', serialize=False, to=settings.AUTH_USER_MODEL)),
                ('ppsn', models.CharField(max_length=255)),
                ('vehicle_type', api.utils.Fields.EnumField(choices=[('car', 'car'), ('scooter', 'scooter'), ('bicycle', 'bicycle')], default='car')),
                ('vehicle_registration_no', models.CharField(max_length=255, null=True)),
                ('order_count', models.PositiveIntegerField(default=0)),
                ('total_earnings', models.PositiveIntegerField(default=0)),
                ('average_delivery_time', models.PositiveIntegerField(default=0)),
                ('total_delivery_time', models.PositiveIntegerField(default=0)),
                ('identification', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='drivers', to='api.identification')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
