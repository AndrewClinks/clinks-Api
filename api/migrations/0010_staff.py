# Generated by Django 4.0.1 on 2022-01-31 10:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_alter_alltimestat_type_venue_openinghour'),
    ]

    operations = [
        migrations.CreateModel(
            name='Staff',
            fields=[
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('company_member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff', to='api.companymember')),
                ('venue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff', to='api.venue')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]