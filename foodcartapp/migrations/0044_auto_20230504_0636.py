# Generated by Django 3.2.15 on 2023-05-04 06:36

from django.db import migrations


def populate_fix_prices_old_orders(apps, schema_editor):
    OrderProduct = apps.get_model('foodcartapp', 'OrderProduct')
    order_products = []
    for order_product in OrderProduct.objects.select_related('product').iterator():
        order_product.fix_price = order_product.product.price
        order_products.append(order_product)
    OrderProduct.objects.bulk_update(order_products, ['fix_price'])


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0043_auto_20230504_0636'),
    ]

    operations = [
        migrations.RunPython(populate_fix_prices_old_orders),
    ]
