from django.http import JsonResponse
from django.templatetags.static import static
from django.db import transaction
from django.conf import settings
from django.contrib.gis.geos import Point

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product
from coordinatesapp.models import Place
from .serializers import OrderSerializer

import requests


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


def fetch_coordinates(apikey, address):
    try:
        base_url = 'https://geocode-maps.yandex.ru/1.x'
        response = requests.get(base_url, params={
            'geocode': address,
            'apikey': apikey,
            'format': 'json',
        })
        response.raise_for_status()
        found_places = response.json()['response']['GeoObjectCollection']['featureMember']

        if not found_places:
            return None

        if 'error' in found_places:
            raise requests.exceptions.HTTPError(found_places['error'])

        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
        return lon, lat
    except requests.exceptions.HTTPError as HTTPError:
        print(HTTPError)
        return None


@api_view(['POST'])
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    address = serializer.validated_data['address']
    ya_geo_key = settings.YANDEX_GEOCODER_API_KEY
    try:
        place, created = Place.objects.get_or_create(
            text_address=address,
            defaults={
                'coordinates': Point(tuple(map(float, fetch_coordinates(ya_geo_key, address))))
            }
        )
        print(place, created)
    except TypeError as e:
        if "'nonetype' object is not iterable" in str(e.args).lower():
            print('func "fetch_coordinates" return None')
    with transaction.atomic():
        order = serializer.save()
    serializer_responce = OrderSerializer(order)
    return Response(serializer_responce.data)
