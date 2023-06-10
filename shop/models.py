from django.db import models
from django.urls import reverse

from parler.models import TranslatableModel, TranslatedFields

class Category(TranslatableModel):
    translations = TranslatedFields(
        name = models.CharField(max_length=200),
        # уникальность подразумевает создание индекса
        slug = models.SlugField(max_length=200, unique=True),
    )

    class Meta:
        # ordering = ['name']
        # indexes = [models.Index(fields=['name']),]
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return str(self.name)

    # get_absolute_url() – это общепринятый способ получения URL-адреса заданного объекта.
    def get_absolute_url(self):
        return reverse('shop:product_list_by_category', args=[self.slug])


class Product(TranslatableModel):
    translations = TranslatedFields(
        name = models.CharField(max_length=200),
        slug = models.SlugField(max_length=200),
        description = models.TextField(blank=True),
    )
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # Для хранения значений денежных сумм всегда следует использовать DecimalField.
    # Внутри FloatField применяется Python’овский тип float, тогда как
    # внутри DecimalField – Python’овский тип Decimal. Используя тип Decimal, вы
    # избежите проблем с округлением чисел с плавающей запятой.


    # товары будут запрашиваться как по идентификатору, так и по слагу
    # Оба поля индексируются вместе с целью повышения производительности запросов,
    # в которых эти два поля используются. (['id', 'slug'])
    class Meta:
        # ordering = ['name']
        indexes = [
            # models.Index(fields=['id', 'slug']),
            # models.Index(fields=['name']),
            models.Index(fields=['-created']),
        ]

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.id, self.slug])