# Generated by Django 4.0.1 on 2022-03-13 21:42

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0024_alter_identification_back_alter_identification_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='driver',
            name='last_known_location',
            field=django.contrib.gis.db.models.fields.PointField(null=True, srid=4326),
        ),
    ]
