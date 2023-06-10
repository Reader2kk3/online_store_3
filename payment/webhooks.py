import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order
from .tasks import payment_completed

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError as e:
        # Недопустимая полезная нагрузка
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Недопустимая подпись
        return HttpResponse(status=400)

    if event.type == 'checkout.session.completed':
        session = event.data.object
        if session.mode == 'payment' and session.payment_status == 'paid':
            try:
                order = Order.objects.get(id=session.client_reference_id)
            except Order.DoesNotExist:
                return HttpResponse(status=404)

        # пометить заказ как оплаченный
        order.paid = True
        # сохранить ИД платежа Stripe
        order.stripe_id = session.payment_intent
        order.save()
        # запустить асинхронное задание
        payment_completed.delay(order.id)

    return HttpResponse(status=200)

'''
    Декоратор @csrf_exempt используется для предотвращения выполнения
    веб-фреймворком Django валидации CSRF, которая делается по умолчанию
    для всех запросов POST. Для верификации заголовка подписи под событи-
    ем используется метод stripe.Webhook.construct_event() библиотеки Stripe.
    Если полезная нагрузка события или подпись недопустимы, то возвращается
    HTTP-ответ 400 Bad Request (Неправильный запрос). В противном случае
    возвращается HTTP-ответ 200 OK. Это базовая функциональность, необхо-
    димая для верификации подписи и конструирования события из полезной
    нагрузки JSON.

    В новом исходном коде проверяется, что полученным событием является
    checkout.session.completed. Это событие указывает на успешное завершение
    сеанса оформления платежа. Если наступает это событие, то извлекается
    сеансовый объект и делается проверка, не является ли режим (mode) сеанса
    платежным (payment), поскольку это ожидаемый режим для разовых плате-
    жей. Затем извлекается атрибут client_reference_id, который использовался
    при создании сеанса оформления платежа, и задействуется преобразова-
    телем Django ORM, чтобы получить объект Order с данным id. Если заказ не
    существует, то вызывается исключение HTTP 404. В противном случае по-
    средством инструкции order.paid = True заказ помечается как оплаченный
    и сохраняется в базе данных.

    Задание payment_completed ставится в очередь путем вызова его метода
    delay(). Задание будет добавлено в очередь и исполнено асинхронно работ-
    ником Celery как можно раньше.
'''
