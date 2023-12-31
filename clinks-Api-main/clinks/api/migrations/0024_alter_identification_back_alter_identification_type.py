# Generated by Django 4.0.1 on 2022-03-13 20:10

import api.utils.Fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0023_remove_venue_venue_count_driver_total_accept_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='identification',
            name='back',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='back', to='api.image'),
        ),
        migrations.AlterField(
            model_name='identification',
            name='type',
            field=api.utils.Fields.EnumField(choices=[('age_card', 'age_card'), ('driver_license', 'driver_license'), ('passport', 'passport')], default='age_card'),
        ),
    ]
