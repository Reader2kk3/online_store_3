from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    discount = models.IntegerField( validators=[MinValueValidator(0),
                MaxValueValidator(100)],help_text='Percentage value (0 to 100)')
    active = models.BooleanField()

    def __str__(self):
        return self.code

'''
    • code: код, который пользователи должны ввести, чтобы применить ку-
    пон к своей покупке;
    • valid_from: значение даты/времени, указывающее, когда купон стано-
    вится действительным;
    • valid_to: значение даты/времени, указывающее, когда купон становит-
    ся недействительным;
    • discount: применяемый уровень скидки (это процент, поэтому прини-
    мает значения в интервале от 0 до 100). Для этого поля надо использо-
    вать валидаторы, чтобы ограничивать минимальное и максимальное
    допустимые значения;
    • active: булево
'''