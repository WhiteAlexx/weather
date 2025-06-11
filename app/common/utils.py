from datetime import datetime, timedelta
import re
import requests

from rest_framework import serializers

from django.core.cache import cache



def get_city(city):
    '''
    Функция проверяет наличие города в кэше
    Если записи нет - получает геоданные города в службе геоданных
    и кэширует их
    Возвращает координаты города или ошибку
    '''

    geo_cache_key = f"geocode_{city}"
    geo_data = cache.get(geo_cache_key)

    if not geo_data:
        try:
            response = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={'name': city, 'count': 1},
                timeout=10,
            )
            geo_data = response.json()
            if 'results' in geo_data and geo_data['results']:
                cache.set(geo_cache_key, geo_data, timeout=356*24*60*60)
            else:
                return {
                    'success': False,
                    'error': 'Город не найден',
                    'status': 404
                }
        except requests.RequestException:
            return {
                'success': False,
                'error': 'Ошибка службы геокодирования',
                'status': 503
            }

    try:
        latitude = geo_data['results'][0]['latitude']
        longitude = geo_data['results'][0]['longitude']
        return {
            'success': True,
            'latitude': latitude,
            'longitude': longitude
        }
    except (KeyError, IndexError):
        return {
            'success': False,
            'error': 'Неверные данные геокодирования',
            'status': 500
        }


def is_latin(value):
    '''
    Валидация города.
    Название города может содержать только латинские буквы,
    разрешены пробелы, дефисы, апострофы, точки, цифры
    '''

    pattern = r"^[a-zA-Z0-9\s\-\'\.]+$"
    if not re.match(pattern, value):
        raise serializers.ValidationError(
            'Название города может содержать только латинские буквы, разрешены пробелы, дефисы, апострофы, точки, цифры'
        )
    return value


def validate_date(value):
    '''
    Валидация даты по формату и диапазону
    '''

    try:
        date = datetime.strptime(value, '%d.%m.%Y').date()
    except ValueError:
        raise serializers.ValidationError('Неверная дата. Используйте формат ДД.ММ.ГГГГ')

    today = datetime.now().date()
    max_date = today + timedelta(days=10)

    if date < today:
        raise serializers.ValidationError({
            'date': f"Дата не может быть раньше {today.strftime('%d.%m.%Y')}"
        })
    if date > max_date:
        raise serializers.ValidationError({
            'date': f"Дата не может быть позже {max_date.strftime('%d.%m.%Y')}"
        })
    return value
