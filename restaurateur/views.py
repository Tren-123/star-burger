from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.contrib.gis.geos import Point
from django.db.models import Subquery, OuterRef
from django.db import IntegrityError

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem
from coordinatesapp.models import Place

import requests
from geopy.distance import lonlat, distance


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, 'login.html', context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect('restaurateur:RestaurantView')
                return redirect('start_page')

        return render(request, 'login.html', context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name='products_list.html', context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name='restaurants_list.html', context={
        'restaurants': Restaurant.objects.all(),
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


def get_or_create_coordinates(api_key, address):
    try:
        address_coordinates = fetch_coordinates(api_key, address)
        if address_coordinates is not None:
            Place.objects.create(text_address=address, coordinates=Point(tuple(map(float, address_coordinates))))
    except IntegrityError as e:
        if 'unique constraint' in str(e.args).lower():
            print('there are identical addresses in new orders that are not in db')
    return address_coordinates


def get_distance_btwn_2_places(api_key, order, menu_item):
    if order.coords is None:
        customer_coordinates = get_or_create_coordinates(api_key, order.address)
    else:
        customer_coordinates = order.coords.coords

    if menu_item.coords is None:
        restaurant_coordinates = get_or_create_coordinates(api_key, menu_item.restaurant.address)
    else:
        restaurant_coordinates = menu_item.coords.coords

    if customer_coordinates is None or restaurant_coordinates is None:
        return 'Ошибка определения координат'

    return round(distance(
        lonlat(*customer_coordinates),
        lonlat(*restaurant_coordinates),
    ).km, 2)


def get_not_new_order_item(order, order_items, menu_items):
    order_items.append((
        order,
        [menu_item.restaurant.name for menu_item in menu_items
        if menu_item.restaurant_id == order.cooking_restaurant_id][0]
    ))


def get_new_order_item(order, order_items, menu_items, api_key):
    can_cook_restaurants = {}
    for order_item in order.products.all():
        if can_cook_restaurants == {}:
            for menu_item in menu_items:
                if menu_item.product_id == order_item.product_id and menu_item.availability:
                    can_cook_restaurants[menu_item.restaurant] = (
                        menu_item.restaurant.name,
                        get_distance_btwn_2_places(api_key, order, menu_item)
                    )
        elif can_cook_restaurants != {}:
            for menu_item in menu_items:
                if menu_item.restaurant in can_cook_restaurants \
                    and menu_item.product_id == order_item.product_id \
                    and not menu_item.availability:
                    can_cook_restaurants.pop(menu_item.restaurant, None)

    order_items.append((order, sorted(can_cook_restaurants.values(), key=lambda restaurant: restaurant[1])))


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    restaurant_place = Place.objects.filter(text_address=OuterRef('restaurant__address'))
    customer_place = Place.objects.filter(text_address=OuterRef('address'))

    menu_items = list(RestaurantMenuItem.objects.select_related('restaurant').annotate(
        coords=Subquery(restaurant_place.values('coordinates'))
    ))
    order_items = []

    for order in Order.objects.with_full_price().annotate(
        coords=Subquery(customer_place.values('coordinates'))
            ).exclude(
                status=Order.COMPLETED
            ).order_by('status'):

        if order.cooking_restaurant_id:
            get_not_new_order_item(order, order_items, menu_items)
        else:
            get_new_order_item(order, order_items, menu_items, settings.YANDEX_GEOCODER_API_KEY)

    return render(request, template_name='order_items.html', context={
        'order_items': order_items,
    })
