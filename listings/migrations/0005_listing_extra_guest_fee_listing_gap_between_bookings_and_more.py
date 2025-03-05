# Generated by Django 5.1.4 on 2025-01-18 10:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0004_alter_listing_bedrooms'),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='extra_guest_fee',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Costo per ogni ospite extra per notte', max_digits=10),
        ),
        migrations.AddField(
            model_name='listing',
            name='gap_between_bookings',
            field=models.PositiveIntegerField(default=0, help_text='Giorni minimi richiesti tra due prenotazioni'),
        ),
        migrations.AddField(
            model_name='listing',
            name='included_guests',
            field=models.PositiveIntegerField(default=1, help_text='Numero di ospiti inclusi nel prezzo base'),
        ),
        migrations.AddField(
            model_name='listing',
            name='max_booking_advance',
            field=models.PositiveIntegerField(default=365, help_text='Giorni massimi di anticipo per prenotare'),
        ),
        migrations.AddField(
            model_name='listing',
            name='min_booking_advance',
            field=models.PositiveIntegerField(default=0, help_text='Giorni minimi di anticipo per prenotare'),
        ),
    ]
