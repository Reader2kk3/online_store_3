from django.db import models
from shop.models import Product
from django.conf import settings

from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from coupons.models import Coupon

from django.utils.translation import gettext_lazy as _

class Order(models.Model):
    first_name = models.CharField(_('first name'), max_length=50)
    last_name = models.CharField(_('last name'), max_length=50)
    email = models.EmailField(_('e-mail'))
    address = models.CharField(_('address'), max_length=250)
    postal_code = models.CharField(_('postal code'), max_length=20)
    city = models.CharField(_('city'),max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    stripe_id = models.CharField(max_length=250, blank=True)
    coupon = models.ForeignKey(Coupon, related_name='orders', null=True, blank=True, on_delete=models.SET_NULL)
    discount = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])

    class Meta:
        ordering = ['-created']
        indexes = [models.Index(fields=['-created']),]

    def __str__(self):
        return f'Order {self.id}'

    def get_total_cost(self):
        total_cost = self.get_total_cost_before_discount()
        return total_cost - self.get_discount()

    def get_stripe_url(self):
        if not self.stripe_id:
            # никаких ассоциированных платежей
            return ''
        if '_test_' in settings.STRIPE_SECRET_KEY:
            # путь Stripe для тестовых платежей
            path = '/test/'
        else:
            # путь Stripe для настоящих платежей
            path = '/'
        return f'https://dashboard.stripe.com{path}payments/{self.stripe_id}'

    def get_total_cost_before_discount(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_discount(self):
        total_cost = self.get_total_cost_before_discount()
        if self.discount:
            return total_cost * (self.discount / Decimal(100))
        return Decimal(0)

'''
    Здесь в модель Order был добавлен новый метод get_stripe_url(). Этот ме-
    тод используется для возврата URL-адреса информационной панели Stripe
    для платежа, связанного с заказом. Если ИД платежа не хранится в поле
    stripe_id объекта Order, то возвращается пустая строка. В противном случае
    возвращается URL-адрес платежа в информационной панели Stripe. Далее
    проверяется наличие подстроки _test_ в настроечном параметре STRIPE_SE-
    CRET_KEY, чтобы отличить производственную среду от тестовой. Платежи
    в производственной среде подчиняются шаблону https://dashboard.stripe.
    com/payments/{id}, тогда как тестовые платежи следуют шаблону https://dash-
    board.stripe.com/payments/test/{id}.
'''

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity