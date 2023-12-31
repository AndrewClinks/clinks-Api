# Generated by Django 3.2.3 on 2022-09-12 15:07

from django.db import migrations, models


def run_scripts(apps, scheme_editor):
    from ..company.models import Company
    from ..delivery_distance.models import DeliveryDistance
    from ..payment.models import Payment

    print("Setting values for passcode, driver_fee and delivery_driver_fee")

    import random

    for company in Company.all_objects.all():
        company.passcode = random.randint(1000, 9999)
        company.save()

    for delivery_distance in DeliveryDistance.all_objects.all():
        delivery_distance.driver_fee = delivery_distance.fee
        delivery_distance.save()

    for payment in Payment.all_objects.all():
        payment.delivery_driver_fee = payment.delivery_fee
        payment.save()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0047_auto_20220912_1507'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='delivery_driver_fee',
            field=models.PositiveIntegerField(),
        ),
        migrations.RunPython(run_scripts, migrations.RunPython.noop),
    ]
