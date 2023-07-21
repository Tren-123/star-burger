# Generated by Django 3.2.15 on 2023-05-13 11:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0045_alter_order_managers'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('new_order', 'Необработанный'), ('cooking', 'Готовится в ресторане'), ('in_delivery', 'Доставляется курьером'), ('compleated', 'Доставлен')], default='new_order', max_length=100, verbose_name='статус заказа'),
        ),
    ]