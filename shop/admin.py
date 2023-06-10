from django.contrib import admin
from .models import Category, Product
from parler.admin import TranslatableAdmin

@admin.register(Category)
class CategoryAdmin(TranslatableAdmin):
    list_display = ['name', 'slug']
   
    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(TranslatableAdmin):
    list_display = ['name', 'slug', 'price', 'available', 'created', 'updated']
    list_filter = ['available', 'created', 'updated']
    list_editable = ['price', 'available']
    
    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('name',)}


'''
    Напомним, что атрибут prepopulated_fields используется для того, что-
    бы указывать поля, значение которых устанавливается автоматически с ис-
    пользованием значения других полей. Как вы уже убедились, это удобно для
    генерирования слагов.
    Атрибут list_editable в классе ProductAdmin используется для того, чтобы
    задать поля, которые можно редактировать, находясь на странице отобра-
    жения списка на сайте администрирования. Такой подход позволит редак-
    тировать несколько строк одновременно. Любое поле в list_editable также
    должно быть указано в атрибуте list_display, поскольку редактировать мож-
    но только отображаемые поля.
'''