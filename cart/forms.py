from django import forms
from django.utils.translation import gettext_lazy as _

PRODUCT_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 21)]

'''
    • quantity: позволяет пользователю выбирать количество от 1 до 20. Для
    конвертирования входных данных в целое число используется поле
    TypedChoiceField вместе с coerce=int;
    • override: позволяет указывать, должно ли количество быть прибавле-
    но к любому существующему количеству в корзине для этого товара
    (False) или же существующее количество должно быть переопределено
    данным количеством (True). Для этого поля используется виджет Hid-
    denInput, так как это поле не будет показываться пользователю.
'''
class CartAddProductForm(forms.Form):
    quantity = forms.TypedChoiceField(choices=PRODUCT_QUANTITY_CHOICES, coerce=int, label=_('Quantity'))
    override = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)

