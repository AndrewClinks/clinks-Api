# Generated by Django 4.0.1 on 2022-03-24 15:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0028_order_started_looking_for_drivers_at_payment_company_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='company',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='api.company'),
        ),
    ]
