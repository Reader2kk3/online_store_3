from decimal import Decimal
import stripe
from django.conf import settings
from django.shortcuts import render, redirect, reverse,get_object_or_404
from orders.models import Order

# создать экземпляр Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION

def payment_process(request):
    order_id = request.session.get('order_id', None)
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        # request.build_absolute_uri() - формирование абсолютного URI-идентификатор из пути URL
        success_url = request.build_absolute_uri(reverse('payment:completed'))
        cancel_url = request.build_absolute_uri(reverse('payment:canceled'))
        
        # данные сеанса оформления платежа Stripe
        session_data = {
            'mode': 'payment',
            'client_reference_id': order.id,
            'success_url': success_url,
            'cancel_url': cancel_url,
            'line_items': []
        }
        
        # добавить товарные позиции заказа
        # в сеанс оформления платежа Stripe
        for item in order.items.all():
            session_data['line_items'].append({
            'price_data': 
                {
                'unit_amount': int(item.price * Decimal('100')),
                'currency': 'usd',
                'product_data': {'name': item.product.name,},
                },
            'quantity': item.quantity,
            })

        # купон Stripe
        if order.coupon:
            stripe_coupon = stripe.Coupon.create(name=order.coupon.code, percent_off=order.discount, duration='once')
            session_data['discounts'] = [{'coupon': stripe_coupon.id}]
        # создать сеанс оформления платежа Stripe
        session = stripe.checkout.Session.create(**session_data)
        # перенаправить к форме для платежа Stripe
        return redirect(session.url, code=303)
    else:
        return render(request, 'payment/process.html', locals())

'''
        Представление payment_process выполняет следующую работу.
    1. Текущий объект Order извлекается по сеансовому ключу order_id, который
    ранее был сохранен в сеансе представлением order_create.
    2. Объект Order извлекается из базы данных по данному order_id. Если при
    использовании функции сокращенного доступа get_object_ or_404()
    возникает исключение Http404 (страница не найдена), то заказ с задан-
    ным ИД не найден.
    3. Если представление загружается с помощью запроса методом GET, то
    прорисовывается и возвращается шаблон payment/process.html. Этот
    шаблон будет содержать сводную информацию о заказе и кнопку для
    перехода к платежу, которая будет генерировать запрос методом POST
    к представлению.
    4. Если представление загружается с помощью запроса методом POST, то
    сеанс Stripe оформления платежа создается с использованием Stripe.
    checkout.Session.create() со следующими ниже параметрами:
        – mode: режим сеанса оформления платежа. Здесь используется значе-
        ние payment, указывающее на разовый платеж. На странице https://
        stripe.com/docs/api/checkout/sessions/object#checkout_session_object-
        mode можно увидеть другие принятые для этого параметра зна-
        чения;
        – client_reference_id: уникальная ссылка для этого платежа. Она будет
        использоваться для согласования сеанса оформления платежа Stripe
        с заказом. Передавая ИД заказа, платежи Stripe связываются с зака-
        зами в вашей системе, и вы сможете получать уведомления от Stripe
        о платежах, чтобы помечать заказы как оплаченные;
        – success_url: URL-адрес, на который Stripe перенаправляет пользо-
        вателя в случае успешного платежа. Здесь используется request.
        build_absolute_uri(), чтобы формировать абсолютный URI-иденти-
        фикатор из пути URL-адреса. Документация по этому методу на-
        ходится по адресу https://docs.djangoproject.com/en/4.1/ref/request-
        response/#django.http.HttpRequest.build_absolute_uri;
        – cancel_url: URL-адрес, на который Stripe перенаправляет пользова-
        теля в случае отмены платежа;
        – line_items: это пустой список. Далее он будет заполнен приобретае-
        мыми товарными позициями заказа.
    5. После создания сеанса оформления платежа возвращается HTTP-
    перенаправление с кодом состояния, равным 303, чтобы перенаправить
    пользователя к Stripe. Код состояния 303 рекомендуется для перена-
    правления веб-приложений на новый URI-идентификатор после вы-
    полнения HTTP-запроса методом POST.

    По каждой товарной позиции используется следующая информация:
        • price_data: информация, связанная с ценой;
        • unit_amount: сумма в центах, которую необходимо получить при оплате. 
        Это положительное целое число, показывающее, сколько взимать
        в наименьшей денежной единице без десятичных знаков. Например,
        10 долларов будет равно 1000 (то есть 1000 центам). Цена товара, item.
        price, умножается на Decimal('100'), чтобы получить значение в центах,
        а затем конвертируется в целое число;
        • currency: используемая валюта в трехбуквенном формате ISO. Значение
        usd используется для долларов США. Список поддерживаемых валют
        можно увидеть на странице https://stripe.com/docs/currencies;
        • product_data: информация, связанная с товаром:
        • name: название товара;
        • quantity: число приобретаемых единиц товара.

    • name: применяется связанный с объектом order код (code) купона;
    • percent_off: скидка (discount) объекта order;
    • duration: используется значение once. Оно указывает Stripe, что это ку-
    пон для разового платежа.
'''

def payment_completed(request):
    return render(request, 'payment/completed.html')

def payment_canceled(request):
    return render(request, 'payment/canceled.html')