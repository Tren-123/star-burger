# Generated by Django 3.2.15 on 2023-05-20 13:33

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0048_auto_20230520_1308'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='called_at',
            field=models.DateTimeField(blank=True, db_index=True, default=django.utils.timezone.now, verbose_name='дата звонка'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='delivered_at',
            field=models.DateTimeField(blank=True, db_index=True, default=django.utils.timezone.now, verbose_name='дата доставки'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='registrated_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True, default=django.utils.timezone.now, verbose_name='дата создания'),
            preserve_default=False,
        ),
    ]
