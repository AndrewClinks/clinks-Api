# Generated by Django 4.0.1 on 2022-03-23 12:49

import api.utils.Fields
import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0026_alter_alltimestat_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='returned_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.CreateModel(
            name='DeliveryRequest',
            fields=[
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('status', api.utils.Fields.EnumField(choices=[('pending', 'pending'), ('accepted', 'accepted'), ('rejected', 'rejected'), ('missed', 'missed'), ('pending', 'pending')], default='pending')),
                ('driver_location', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('accepted_at', models.DateTimeField(null=True)),
                ('rejected_at', models.DateTimeField(null=True)),
                ('driver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delivery_requests', to='api.driver')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delivery_requests', to='api.order')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
