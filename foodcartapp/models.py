from django.db import models
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MinValueValidator
from django.db.models import Sum, F


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f'restaraunt № {self.restaurant_id} - product № {self.product_id}'


class OrderFullPriceQuerySet(models.QuerySet):
    def with_full_price(self):
        return self.prefetch_related('products').annotate(
            full_price=Sum(F('products__fix_price') * F('products__quantity')),
        )


class Order(models.Model):
    NEW_ORDER = '1.new_order'
    COOKING = '2.cooking'
    IN_DELIVERY = '3.in_delivery'
    COMPLEATED = '4.compleated'

    STATUS_CHOICES = [
        (NEW_ORDER, 'Необработанный'),
        (COOKING, 'Готовится в ресторане'),
        (IN_DELIVERY, 'Доставляется курьером'),
        (COMPLEATED, 'Доставлен'),
    ]
    ON_SITE = 'on_site'
    CASH = 'cash'

    PAYMENT_CHOICES = [
        (ON_SITE, 'Электронно'),
        (CASH, 'Наличностью'),
    ]
    firstname = models.CharField(
        'имя клиента',
        max_length=200,
    )
    lastname = models.CharField(
        'фамилия клиента',
        max_length=200,
    )
    phonenumber = PhoneNumberField(
        'номер телефона клиента',
    )
    address = models.TextField(
        'адрес доставки',
        max_length=300,
    )
    status = models.CharField(
        'статус заказа',
        max_length=100,
        choices=STATUS_CHOICES,
        default=NEW_ORDER,
        db_index=True,
    )
    manager_comment = models.TextField(
        'комментарий',
        max_length=300,
        blank=True,
    )
    registrated_at = models.DateTimeField(
        'дата создания',
        auto_now_add=True,
        db_index=True,
    )
    called_at = models.DateTimeField(
        'дата звонка',
        blank=True,
        null=True,
        db_index=True,
    )
    delivered_at = models.DateTimeField(
        'дата доставки',
        blank=True,
        null=True,
        db_index=True,
    )
    payment_method = models.CharField(
        'способ оплаты',
        max_length=100,
        choices=PAYMENT_CHOICES,
        default=CASH,
        db_index=True,
    )
    cooking_restaurant = models.ForeignKey(
        Restaurant,
        related_name='orders',
        verbose_name='готовит ресторан',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    objects = OrderFullPriceQuerySet.as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'{self.lastname} {self.firstname}. {self.address}'


class OrderProduct(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='products',
        verbose_name='заказ',
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        related_name='orders',
        verbose_name='товар',
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveSmallIntegerField(
        'количество',
        validators=[MinValueValidator(1)],
    )
    fix_price = models.DecimalField(
        'цена в заказе',
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказе'

    def __str__(self):
        return f'product {self.product_id} in order {self.order_id}'
