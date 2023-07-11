# Generated by Django 4.0.1 on 2022-01-25 15:03

import api.utils.Fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_address_customer_address'),
    ]

    operations = [
        migrations.CreateModel(
            name='AllTimeStat',
            fields=[
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('type', api.utils.Fields.EnumField(choices=[('company_count', 'company_count'), ('driver_count', 'driver_count')], default='company_count')),
                ('value', models.PositiveIntegerField(default=0)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
