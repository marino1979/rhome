# Generated by Django 5.1.4 on 2025-01-14 16:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beds', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bed',
            options={},
        ),
        migrations.AlterModelOptions(
            name='bedtype',
            options={'ordering': ['name'], 'verbose_name': 'Tipo di letto', 'verbose_name_plural': 'Tipi di letto'},
        ),
        migrations.RemoveField(
            model_name='bed',
            name='bed_type',
        ),
        migrations.RemoveField(
            model_name='bed',
            name='listing',
        ),
        migrations.RemoveField(
            model_name='bed',
            name='quantity',
        ),
        migrations.RemoveField(
            model_name='bed',
            name='room_name',
        ),
        migrations.AddField(
            model_name='bedtype',
            name='capacity',
            field=models.PositiveIntegerField(default=1, help_text='Numero di persone che può ospitare questo tipo di letto', verbose_name='Numero posti letto'),
        ),
        migrations.AddField(
            model_name='bedtype',
            name='dimensions',
            field=models.CharField(blank=True, help_text='Es: 160x200', max_length=50, verbose_name='Dimensioni'),
        ),
    ]
