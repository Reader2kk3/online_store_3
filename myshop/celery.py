import os
from celery import Celery

# задать стандартный модуль настроек Django для программы 'celery'.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
app = Celery('myshop')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


'''
    • задается переменная DJANGO_SETTINGS_MODULE для встроенной в Celery
    программы командной строки;
    • посредством инструкции app = Celery('myshop') создается экземпляр
    приложения;
    • используя метод config_from_object(), загружается любая конкретно-
    прикладная конфигурация из настроек проекта. Атрибут namespace за-
    дает префикс, который будет в вашем файле settings.py у настроек,
    связанных с Celery. Задав именное пространство CELERY, все настройки
    Celery должны включать в свое имя префикс CELERY_ (например, CEL-
    ERY_BROKER_URL);
    • наконец, сообщается, чтобы очередь заданий Celery автоматически об-
    наруживала асинхронные задания в ваших приложениях. Celery будет
    искать файл tasks.py в каждом каталоге приложений, добавленных в IN-
    STALLED_APPS, чтобы загружать определенные в нем асинхронные задания.
'''