# Generated by Django 5.1.4 on 2025-03-21 16:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0010_listing_checkin_notes_en_listing_checkin_notes_es_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='base_price',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Prezzo base per'),
        ),
    ]
