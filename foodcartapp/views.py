from django.http import JsonResponse
from django.templatetags.static import static
from .models import Order, OrderProduct
from .models import Product
from rest_framework.decorators import api_view
from rest_framework.response import Response


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    raw_order = request.data
    order = Order.objects.create(
        customer_first_name=raw_order['firstname'],
        customer_last_name=raw_order['lastname'],
        customer_phone_number=raw_order['phonenumber'],
        adress=raw_order['address'],
    )

    order_products = []
    for raw_product in raw_order['products']:
        order_products.append(
            OrderProduct(
                order=order,
                product_id=raw_product['product'],
                quantity=raw_product['quantity'],
            )
        )
    OrderProduct.objects.bulk_create(order_products)
    return Response({})
