# Generated by Django 5.1.4 on 2025-03-14 12:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0005_listing_extra_guest_fee_listing_gap_between_bookings_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ListingRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='Titolo')),
                ('description', models.TextField(blank=True, verbose_name='Descrizione')),
                ('is_allowed', models.BooleanField(default=True, verbose_name='È consentito')),
                ('is_predefined', models.BooleanField(default=False, verbose_name='Regola predefinita')),
                ('time_from', models.TimeField(blank=True, null=True, verbose_name='Orario da')),
                ('time_to', models.TimeField(blank=True, null=True, verbose_name='Orario a')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='Ordine')),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rules', to='listings.listing')),
            ],
            options={
                'verbose_name': 'Regola',
                'verbose_name_plural': 'Regole',
                'ordering': ['order', 'title'],
            },
        ),
    ]
