# Generated by Django 4.0.1 on 2022-01-31 16:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_companymember_active_venue'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='has_added_menu_items',
            field=models.BooleanField(default=False),
        ),
    ]
