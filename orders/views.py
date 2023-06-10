from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required

from .models import OrderItem, Order
from .forms import OrderCreateForm
from cart.cart import Cart
from .tasks import order_created

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
import weasyprint

'''
    Это представление генерирования счета-фактуры в формате PDF для за-
    каза. Декоратор staff_member_required используется в целях обеспечения того,
    чтобы доступ к этому представлению могли получать только штатные поль-
    зователи.
    По заданному ИД извлекается объект Order и, используя предоставлен-
    ную веб-фреймворком Django функцию render_to_string(), прорисовывается
    шаблон orders/order/pdf.html. Прорисованный HTML сохраняется в перемен-
    ной html.
    Затем генерируется новый объект HttpResponse с указанием типа содер-
    жимого application/pdf и с включением заголовка Content-Disposition, чтобы
    задать имя файла. Библиотека WeasyPrint используется для генерирования
    PDF-файла из прорисованного исходного кода HTML и записи файла в объ-
    ект HttpResponse.
    Для добавления стилей CSS в сгенерированный PDF-файл применяется
    статический файл css/pdf.css, который загружается из локального пути, ис-
    пользуя настроечный параметр STATIC_ROOT. Наконец, возвращается сгене-
    рированный ответ.
    Если у вас отсутствуют стили CSS, то не забудьте скопировать статические
    файлы, расположенные в каталоге static/ приложения shop, в то же место
    вашего проекта.
'''
@staff_member_required
def admin_order_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string('orders/order/pdf.html', {'order': order})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=order_{order.id}.pdf'
    weasyprint.HTML(string=html).write_pdf(response,
        stylesheets=[weasyprint.CSS(settings.STATIC_ROOT / 'css/pdf.css')])

    return response

'''
    В представлении order_create текущая корзина извлекается из сеанса посредством 
    инструкции cart = Cart(request).
    В зависимости от метода запроса выполняется следующая работа:
    • запрос методом GET: создает экземпляр формы OrderCreateForm и про-
    рисовывает шаблон orders/order/create.html;
    • запрос методом POST: выполняет валидацию отправленных в запросе
    данных. Если данные валидны, то в базе данных создается новый заказ,
    используя инструкцию order = form.save(). Товарные позиции корзины
    прокручиваются в цикле, и для каждой из них создается OrderItem. Наконец,
    содержимое корзины очищается, и шаблон orders/order/created.html прорисовывается.
'''
def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if cart.coupon:
                order.coupon = cart.coupon
                order.discount = cart.coupon.discount
            order.save()
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'], 
                                price=item['price'], quantity=item['quantity'])
            # очистить корзину
            cart.clear()
            
            # запустить асинхронное задание 
            # Метод delay() задания вызывается для его асинхронного исполнения. 
            # Задание будет добавлено в очередь сообщений и выполнено работником Celery
            # задать заказ в сеансе
            request.session['order_id'] = order.id
            # перенаправить к платежу
            return redirect(reverse('payment:process'))

    else:
        form = OrderCreateForm()

    context = {'cart': cart, 'form': form}
    return render(request, 'orders/order/create.html', context)


# Декоратор staff_member_required проверяет, что значения полей is_active и is_staff 
# запрашивающего страницу пользователя установлены равными True. В этом представлении 
# по заданному ИД извлекается объект Order и затем прорисовывается шаблон для отображения заказа.
@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'admin/orders/order/detail.html', {'order': order})
    