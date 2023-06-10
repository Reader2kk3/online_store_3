import redis
from django.conf import settings
from .models import Product

# соединить с redis
r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)

class Recommender:
    def get_product_key(self, id):
        return f'product:{id}:purchased_with'

    def products_bought(self, products):
        product_ids = [p.id for p in products]
        for product_id in product_ids:
            for with_id in product_ids:
                # получить другие товары, купленные
                # вместе с каждым товаром
                if product_id != with_id:
                    # увеличить балл товара,
                    # купленного вместе
                    r.zincrby(self.get_product_key(product_id), 1, with_id)

    def suggest_products_for(self, products, max_results=6):
        product_ids = [p.id for p in products]
        if len(products) == 1:
            # только 1 товар
            suggestions = r.zrange(self.get_product_key(product_ids[0]), 0, -1, desc=True)[:max_results]
        else:
            # сгенерировать временный ключ
            flat_ids = ''.join([str(id) for id in product_ids])
            tmp_key = f'tmp_{flat_ids}'
            # несколько товаров, объединить баллы всех товаров
            # сохранить полученное сортированное множество
            # во временном ключе
            keys = [self.get_product_key(id) for id in product_ids]
            r.zunionstore(tmp_key, keys)
            # удалить идентификаторы товаров,
            # для которых дается рекомендация
            r.zrem(tmp_key, *product_ids)
            # получить идентификаторы товаров по их количеству,
            # сортировка по убыванию
            suggestions = r.zrange(tmp_key, 0, -1,
            desc=True)[:max_results]
            # удалить временный ключ
            r.delete(tmp_key)
        suggested_products_ids = [int(id) for id in suggestions]
        # получить предлагаемые товары и
        # отсортировать их по порядку их появления
        suggested_products = list(Product.objects.filter(id__in=suggested_products_ids))
        suggested_products.sort(key=lambda x: suggested_products_ids.index(x.id))
        return suggested_products

    def clear_purchases(self):
        for id in Product.objects.values_list('id', flat=True):
            r.delete(self.get_product_key(id))

'''
    Это класс Recommender, который предоставит возможность хранить покупки
    товаров и получать предложения по данному товару или товарам.
    Метод get_product_key() получает ИД объекта Product и формирует ключ
    сортированного множества Redis, в котором хранятся связанные товары. При
    этом ключ выглядит как product:[id]:purchased_with.
    Метод products_bought() получает список объектов Product, которые были
    куплены вместе (то есть принадлежат одному заказу).
    В этом методе выполняется следующая работа.
    1. Берутся товарные идентификаторы для заданных объектов Product.
    2. Товарные идентификаторы прокручиваются в цикле. По каждому иден-
    тификатору товарные идентификаторы снова прокручиваются в цикле,
    пропуская тот же товар, чтобы получить товары, которые покупаются
    вместе с каждым товаром.
    3. С помощью метода get_product_id() по каждому купленному товару бе-
    рется товарный ключ Redis. Для товара с ИД 33 этот метод возвращает
    ключ product:33:purchased_with. Это ключ сортированного множества,
    которое содержит идентификаторы товаров, купленных вместе с ним.
    4. Балл каждого товарного ИД, содержащегося в сортированном множест-
    ве, увеличивается на 1. Балл представляет число раз, когда другой товар
    был куплен вместе с данным товаром.

    Метод offer_products_for() получает следующие параметры:
    • products: это список объектов Product, для которых нужно получить ре-
    комендации. Он может содержать один или несколько товаров;
    • max_results: это целое число, представляющее максимальное число воз-
    вращаемых рекомендуемых товаров.
    В этом методе выполняются следующие действия.
    1. Для заданных объектов Product берутся идентификаторы товаров.
    2. Если указан только один товар, то берутся идентификаторы товаров,
    которые были куплены вместе с данным товаром, упорядоченные по
    общему числу раз, когда они покупались вместе. Для этой цели исполь-
    зуется команда Redis ZRANGE. Число результатов ограничивается числом,
    указанным в атрибуте max_results (по умолчанию 6).
    3. Если указано более одного товара, то генерируется временный ключ
    Redis, сформированный с использованием идентификаторов товаров.
    4. Все баллы товарных позиций, содержащихся в сортированном множест-
    ве каждого данного товара, объединяются и суммируются. Это делается
    с помощью команды Redis ZUNIONSTORE. Команда ZUNIONSTORE выполняет
    операцию объединения сортированных множеств с заданными клю-
    чами и сохраняет агрегированную сумму баллов товарных позиций
    в новом ключе Redis. Подробнее об этой команде можно прочитать на
    странице https://redis.io/commands/zunionstore/. Агрегированные баллы
    сохраняются во временном ключе.
    5. Поскольку баллы суммируются, можно получить те же товары, по кото-
    рым берутся рекомендации. Они удаляются из сгенерированного сор-
    тированного множества с помощью команды ZREM.
    6. С помощью команды ZRANGE из временного ключа извлекаются иден-
    тификаторы товаров, упорядоченные по их баллам. Число результатов
    ограничивается числом, указанным в атрибуте max_results. Затем вре-
    менный ключ удаляется.
    7. Наконец, берутся объекты Product с заданными идентификаторами
    и товары упорядочиваются в том же порядке, что и они.
'''