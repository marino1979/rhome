# Generated by Django 5.1.4 on 2025-03-18 17:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0008_remove_listingrule_listing_delete_systemrule_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='allow_smoking',
            field=models.BooleanField(default=False, verbose_name='Consentito fumare'),
        ),
        migrations.AddField(
            model_name='listing',
            name='smoking_notes',
            field=models.TextField(blank=True, verbose_name='Note fumo'),
        ),
    ]
