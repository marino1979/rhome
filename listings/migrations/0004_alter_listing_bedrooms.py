# Generated by Django 5.1.4 on 2025-01-15 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0003_listing_outdoor_square_meters_listing_total_beds_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='bedrooms',
            field=models.PositiveIntegerField(default=1, verbose_name='Camere da letto'),
        ),
    ]
