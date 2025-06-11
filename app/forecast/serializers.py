from rest_framework import serializers

from common.utils import is_latin, validate_date
from forecast.models import WeatherData


class CityDateQuerySerializer(serializers.Serializer):

    city = serializers.CharField(required=True)
    date = serializers.CharField(required=True)

    def validate_city(self, value):
        return is_latin(value)

    def validate_date(self, value):
        return validate_date(value)


class ForecastSerializer(serializers.Serializer):

    min_temperature = serializers.DecimalField(max_digits=3, decimal_places=1, coerce_to_string=False)
    max_temperature = serializers.DecimalField(max_digits=3, decimal_places=1, coerce_to_string=False)


class CreateWeatherSerializer(serializers.ModelSerializer):

    city = serializers.CharField(max_length=10, required=True)
    date = serializers.CharField(max_length=10, required=True)
    min_temperature = serializers.DecimalField(max_digits=3, decimal_places=1, coerce_to_string=False, required=True)
    max_temperature = serializers.DecimalField(max_digits=3, decimal_places=1, coerce_to_string=False, required=True)

    class Meta:
        model = WeatherData
        fields = ['city', 'date', 'min_temperature', 'max_temperature']

    def validate_city(self, value):
        return is_latin(value)

    def validate_date(self, value):
        return validate_date(value)

    def validate(self, data):
        '''
        Валидация температуры
        '''
        min_temp = data['min_temperature']
        max_temp = data['max_temperature']

        if min_temp > max_temp:
            raise serializers.ValidationError({
                'min_temperature': 'Минимальная температура не может превышать максимальную'
            })

        return data
