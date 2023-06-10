from celery import shared_task
from django.core.mail import send_mail
from .models import Order

@shared_task
def order_created(order_id):
    # Задание по отправке уведомления по электронной почте при успешном создании заказа.
    order = Order.objects.get(id=order_id)
    subject = f'Order nr. {order.id}'
    message = f'Dear {order.first_name},\n\n' \
        f'You have successfully placed an order.' \
        f'Your order ID is {order.id}.'
    mail_sent = send_mail(subject, message, 'admin@myshop.com', [order.email])
    return mail_sent

'''
    Задание order_created было определено с помощью декоратора @shared_
    task. Как видите, задание Celery – это просто функция Python, декориро-
    ванная функцией-декоратором @shared_task. Функция задания order_created
    получает параметр order_id. При исполнении задания рекомендуется всегда
    передавать идентификаторы функциям задания и извлекать объекты из базы
    данных. Тем самым избегается доступ к устаревшей информации, поскольку
    данные в базе данных могли измениться за то время, пока задание стояло
    в очереди. Для отправки уведомления по электронной почте разместившему
    заказ пользователю была использована предоставляемая веб-фреймворком
    Django функция send_mail().
'''