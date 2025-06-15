from django.db import models


class WeatherData(models.Model):
    '''
    city (строка, обязательное) — название города на английском языке, например: "Berlin".
    date (строка, обязательное) — дата, для которой задаётся прогноз, в формате "dd.MM.yyyy".
    min_temperature (число, обязательное) — минимальная температура в указанный день, в градусах Цельсия.
    max_temperature (число, обязательное) — максимальная температура в указанный день, в градусах Цельсия.'
    '''

    city = models.CharField(max_length=50, blank=False)
    date = models.CharField(max_length=10, blank=False)
    min_temperature = models.DecimalField(max_digits=3, decimal_places=1, blank=False)
    max_temperature = models.DecimalField(max_digits=3, decimal_places=1, blank=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['city', 'date'],
                name='unique_citty_date'
            )
        ]
