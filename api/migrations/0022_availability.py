# Generated by Django 4.0.1 on 2022-02-25 15:06

import api.utils.Fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0021_alter_setting_key'),
    ]

    operations = [
        migrations.CreateModel(
            name='Availability',
            fields=[
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('day', api.utils.Fields.EnumField(choices=[('sunday', 'sunday'), ('monday', 'monday'), ('tuesday', 'tuesday'), ('wednesday', 'wednesday'), ('thursday', 'thursday'), ('friday', 'friday'), ('saturday', 'saturday')], default='sunday')),
                ('starts_at', models.TimeField(null=True)),
                ('ends_at', models.TimeField(null=True)),
                ('closed', models.BooleanField(default=False)),
                ('date', models.DateField(null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]