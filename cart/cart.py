from decimal import Decimal
from django.conf import settings
from shop.models import Product
from coupons.models import Coupon

'''
    Это класс Cart, который позволит управлять корзиной покупок. Перемен-
    ная cart должна быть инициализирована объектом request. Текущий сеанс
    сохраняется посредством инструкции self.session = request.session, чтобы
    сделать его доступным для других методов класса Cart.
    Сначала с помощью метода self.session.get(settings.CART_SESSION_ID) де-
    лается попытка получить корзину из текущего сеанса. Если в сеансе корзины
    нет, то путем задания пустого словаря в сеансе создается пустая корзина.
    Далее надо сформировать словарь cart с идентификаторами товаров в ка-
    честве ключей и словарем, который будет содержать количество и цену, по
    каждому ключу товара. Поступая таким образом, можно гарантировать, что
    товар не будет добавляться в корзину более одного раза. Благодаря этому
    также упрощается извлечение товаров из корзины.
'''

class Cart:
    def __init__(self, request):
        # Инициализировать корзину.
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # сохранить пустую корзину в сеансе
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        # сохранить текущий примененный купон
        self.coupon_id = self.session.get('coupon_id')


    '''
        В методе __iter__() извлекаются присутствующие в корзине экземпляры
        класса Product, чтобы включить их в товарные позиции корзины. Текущая
        корзина копируется в переменную cart, и в нее добавляются экземпляры
        класса Product. Наконец, товары корзины прокручиваются в цикле, конвер-
        тируя цену каждого товара обратно в десятичное число фиксированной точ-
        ности и добавляя в каждый товар атрибут total_price. Метод __iter__() по-
        зволит легко прокручивать товарные позиции корзины в представлениях
        и шаблонах.
    '''
    def __iter__(self):
        # Прокрутить товарные позиции корзины в цикле и получить товары из базы данных.
        product_ids = self.cart.keys()
        # получить объекты product и добавить их в корзину
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()

        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    '''
        Кроме того, понадобится способ возвращать общее число товаров в кор-
        зине. Когда функция len() исполняется с объектом в качестве аргумента,
        Python вызывает свой метод __len__() для получения его длины. Далее будет
        определен конкретно-прикладной метод __len__(), чтобы возвращать общее
        число товаров, хранящихся в корзине.
    '''
    def __len__(self):
        # Подсчитать все товарные позиции в корзине.
        return sum(item['quantity'] for item in self.cart.values())


    '''
        Метод add() принимает на входе следующие ниже параметры:
        • product: экземпляр product для его добавления в корзину либо его обновления;
        • quantity: опциональное целое число с количеством товара. По умолчанию равен 1;
        • override_quantity: это булево значение, указывающее, нужно ли заменить 
        количество переданным количеством (True) либо прибавить новое
        количество к существующему количеству (False).
    '''
    def add(self, product, quantity=1, override_quantity=False):
        # Добавить товар в корзину либо обновить его количество.
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    # Метод save() помечает сеанс как измененный, используя session.modified = True. 
    # Это сообщает Django о том, что сеанс изменился и его необходимо сохранить.
    def save(self):
        # пометить сеанс как "измененный",
        # чтобы обеспечить его сохранение
        self.session.modified = True

    # Метод remove() удаляет данный товар из словаря cart и вызывает метод save(), 
    # чтобы обновить корзину в сеансе.
    def remove(self, product):
        # Удалить товар из корзины.
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        # удалить корзину из сеанса
        del self.session[settings.CART_SESSION_ID]
        self.save()

    # метод расчета общей стоимости товаров в корзине
    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())


    '''
    • coupon(): этот метод определяется как свойство. Если корзина содержит
    атрибут coupon_id, то возвращается объект Coupon с заданным ИД;
    • get_discount(): если в корзине есть купон, то извлекается его уровень
    скидки и возвращается сумма, которая будет вычтена из общей суммы
    корзины;
    • get_total_price_after_discount(): возвращается общая сумма корзины
    после вычета суммы, возвращаемой методом get_discount().
    '''
    @property
    def coupon(self):
        if self.coupon_id:
            try:
                return Coupon.objects.get(id=self.coupon_id)
            except Coupon.DoesNotExist:
                pass
        return None

    def get_discount(self):
        if self.coupon:
            return (self.coupon.discount / Decimal(100)) * self.get_total_price()
        return Decimal(0)

    def get_total_price_after_discount(self):
        return self.get_total_price() - self.get_discount()
        