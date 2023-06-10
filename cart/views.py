from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from shop.models import Product
from .cart import Cart
from .forms import CartAddProductForm
from coupons.forms import CouponApplyForm
from shop.recommender import Recommender

# отображения корзины и ее товаров.
def cart_detail(request):
    cart = Cart(request)
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(initial={'quantity': item['quantity'], 'override': True})
    coupon_apply_form = CouponApplyForm()

    # Redis
    r = Recommender()
    cart_products = [item['product'] for item in cart]
    if(cart_products):
        recommended_products = r.suggest_products_for(cart_products, max_results=4)
    else:
        recommended_products = []

    context = {'cart': cart, 'coupon_apply_form': coupon_apply_form, 'recommended_products': recommended_products}
    return render(request, 'cart/detail.html', context)


'''
    Это представление добавления товаров в корзину или обновления коли-
    чества существующих товаров. В нем используется декоратор require_POST,
    чтобы разрешать запросы только методом POST. Указанное представление
    получает ИД товара в качестве параметра. Затем извлекается экземпляр
    класса Product с заданным ИД и выполяется валидация формы посредством
    CartAddProductForm. Если форма валидна, то товар в корзине либо добавляется,
    либо обновляется. Представление перенаправляет на URL-адрес cart_detail,
    который будет отображать содержимое корзины.
'''
@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)

    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product, quantity=cd['quantity'], override_quantity=cd['override'])

    return redirect('cart:cart_detail')

'''
    Представление cart_remove получает ИД товара в качестве параметра. В нем
    используется декоратор require_POST, чтобы разрешать запросы только мето-
    дом POST. Экземпляр товара извлекается с заданным ИД, и товар удаляется
    из корзины. Затем пользователь перенаправляется на URL-адрес cart_detail.
'''
@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')

