# Generated by Django 3.2.15 on 2023-05-27 19:10

from django.db import migrations


def change_status_values(apps, schema_editor):
    Order = apps.get_model('foodcartapp', 'Order')
    orders = []
    for order in Order.objects.all().iterator():
        if order.status == 'new_order':
            order.status = '1.new_order'
        elif order.status == 'cooking':
            order.status = '2.cooking'
        elif order.status == 'in_delivery':
            order.status = '3.in_delivery'
        elif order.status == 'compleated':
            order.status = '4.compleated'
        orders.append(order)
    Order.objects.bulk_update(orders, ['status'])


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0052_auto_20230527_1908'),
    ]

    operations = [
        migrations.RunPython(change_status_values),
    ]
