# Generated by Django 4.0.1 on 2022-03-31 16:21

import api.utils.Fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0032_venuepayment'),
    ]

    operations = [
        migrations.AddField(
            model_name='driver',
            name='current_delivery_request',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='driver_as_current', to='api.deliveryrequest'),
        ),
        migrations.AddField(
            model_name='order',
            name='rejection_reason',
            field=api.utils.Fields.EnumField(choices=[('rejected_by_venue', 'rejected_by_venue'), ('no_driver_found', 'no_driver_found')], default='rejected_by_venue', null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='identification_status',
            field=api.utils.Fields.EnumField(choices=[('not_requested', 'not_requested'), ('not_required', 'not_required'), ('refused', 'refused'), ('not_provided', 'not_provided'), ('provided', 'provided')], default='not_requested', null=True),
        ),
    ]
