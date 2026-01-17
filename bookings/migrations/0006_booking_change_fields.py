from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0005_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='change_request_created_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='change_request_note',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='change_requested',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='multibooking',
            name='change_request_created_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='multibooking',
            name='change_request_note',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='multibooking',
            name='change_requested',
            field=models.BooleanField(default=False),
        ),
    ]



