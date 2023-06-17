from rest_framework import serializers
from .models import Order, OrderProduct


class OrderProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderProduct
        fields = ['product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    products = OrderProductSerializer(many=True, allow_empty=False, write_only=True)

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']

    def create(self, validated_data):
        order = Order.objects.create(
            firstname=validated_data['firstname'],
            lastname=validated_data['lastname'],
            phonenumber=validated_data['phonenumber'],
            address=validated_data['address'],
        )
        order_products = [
            OrderProduct(
                order=order,
                product=validated_product['product'],
                quantity=validated_product['quantity'],
                fix_price=validated_product['product'].price
            ) for validated_product in validated_data['products']
        ]
        OrderProduct.objects.bulk_create(order_products)
        return order
