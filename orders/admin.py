from django.contrib import admin
from .models import Order, OrderItem
from django.utils.safestring import mark_safe

import csv
import datetime
from django.http import HttpResponse

from django.urls import reverse




'''
        В этом исходном коде выполняется следующая работа.
    1. Создается экземпляр HttpResponse с указанием типа содержимого text/
    csv, сообщая браузеру, что ответ должен обрабатываться как CSV-файл.
    Также добавляется заголовок Content-Disposition, указывая на то, что
    HTTP-ответ содержит вложенный файл.
    2. Создается пишущий объект writer, который будет писать CSV в объект
    response.
    3. Динамически извлекаются поля модели, используя метод get_fields()
    _meta опций модели. Исключаются взаимосвязи многие-ко-многим
    и один-ко-многим.
    4. Пишется строка заголовка, состоящая из имен полей.
    5. Заданный набор запросов QuerySet прокручивается в цикле, и пишется
    строка каждого объекта, возвращаемого набором запросов. При этом
    обращается внимание на форматирование объектов даты/времени, по-
    тому что выходное значение для CSV должно быть строковым.
    6. В раскрывающемся списке действий на сайте администрирования
    адаптируется отображаемое имя действия; это делается за счет уста-
    новки значения атрибута short_description функции.
'''
def export_to_csv(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    content_disposition = f'attachment; filename={opts.verbose_name}.csv'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = content_disposition
    writer = csv.writer(response)
    fields = [field for field in opts.get_fields() if not \
            field.many_to_many and not field.one_to_many]
    # записать первую строку с информацией заголовка
    writer.writerow([field.verbose_name for field in fields])
    # записать строки данных
    for obj in queryset:
        data_row = []
        for field in fields:
            value = getattr(obj, field.name)
            if isinstance(value, datetime.datetime):
                value = value.strftime('%d/%m/%Y')
            data_row.append(value)
        writer.writerow(data_row)
    return response
export_to_csv.short_description = 'Export to CSV'


def order_pdf(obj):
    url = reverse('orders:admin_order_pdf', args=[obj.id])
    return mark_safe(f'<a href="{url}">PDF</a>')
    order_pdf.short_description = 'Invoice'


'''
    Функция order_stripe_payment() принимает в качестве аргумента объект
    Order и возвращает HTML-ссылку с URL-адресом платежа Stripe. Django по
    умолчанию экранирует результат HTML. Мы используем функцию mark_safe,
    чтобы избежать автоматического экранирования.
'''

def order_stripe_payment(obj):
    url = obj.get_stripe_url()
    if obj.stripe_id:
        html = f'<a href="{url}" target="_blank">{obj.stripe_id}</a>'
        return mark_safe(html)
    return ''

order_stripe_payment.short_description = 'Stripe payment'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']

def order_detail(obj):
    url = reverse('orders:admin_order_detail', args=[obj.id])
    return mark_safe(f'<a href="{url}">View</a>')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'address', 'postal_code', 
        'city', 'paid', order_stripe_payment, 'created', 'updated', order_detail, order_pdf]
    list_filter = ['paid', 'created', 'updated']
    inlines = [OrderItemInline]
    actions = [export_to_csv]

# Класс ModelInline используется с моделью OrderItem, чтобы включать ее
# внутристрочно1 в класс OrderAdmin. Атрибут inlines позволяет вставлять модель
# в ту же страницу редактирования, что и связанная с ней модель.