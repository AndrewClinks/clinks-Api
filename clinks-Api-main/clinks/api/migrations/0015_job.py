# Generated by Django 4.0.1 on 2022-02-07 17:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_category_item_count_item'),
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('data', models.TextField()),
                ('errors', models.JSONField(null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
