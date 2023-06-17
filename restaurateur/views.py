from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Subquery, OuterRef

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem
from coordinatesapp.models import Place

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


def get_distance_btwn_2_places(order, menu_item):
    if order.coords is None or menu_item.coords is None:
        return 'Ошибка определения координат'
    else:
        return round(distance(
            lonlat(*order.coords.coords),
            lonlat(*menu_item.coords.coords),
        ).km, 2)


def get_not_new_order_item(order, order_items, menu_items):
    order_items.append((
        order,
        [menu_item.restaurant.name for menu_item in menu_items
        if menu_item.restaurant_id == order.cooking_restaurant_id][0]
    ))


def get_new_order_item(order, order_items, menu_items):
    can_cook_restaurants = {}
    for order_item in order.products.all():
        if can_cook_restaurants == {}:
            for menu_item in menu_items:
                if menu_item.product_id == order_item.product_id and menu_item.availability:
                    can_cook_restaurants[menu_item.restaurant] = (
                        menu_item.restaurant.name,
                        get_distance_btwn_2_places(order, menu_item)
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
            get_new_order_item(order, order_items, menu_items)

    return render(request, template_name='order_items.html', context={
        'order_items': order_items,
    })
