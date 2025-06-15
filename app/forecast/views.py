from datetime import datetime
import time
from django.db import IntegrityError
import requests

from rest_framework.views import APIView
from rest_framework.response import Response

from django.core.cache import cache

from common.utils import get_city
from forecast.models import WeatherData
from forecast.serializers import CreateWeatherSerializer, ForecastSerializer, CityDateQuerySerializer


class ForecastView(APIView):

    def get(self, request):
        '''
        Возвращает прогноз температуры на заданную дату: минимальное и максимальное значение

        Сначала проверяет запись для пары город-дата в кэше
        Если запись не найдена в кэше, проверяет запись для пары город-дата в БД
        Если запись не найдена в БД, получает город из функции get_city
        По полученным из функции координатам ищет в кэше данные о прогнозе
        Если не находит - получает данные из метеослужбы и кэширует их на 1 час
        '''

        query_serializer = CityDateQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        city = query_serializer.validated_data['city']
        date = query_serializer.validated_data['date']

        city_n_date_cache_key = f"city_n_date_{city}_{date}"
        city_n_date_data = cache.get(city_n_date_cache_key)

        if not city_n_date_data:
            try:
                city_n_date = WeatherData.objects.get(city=city, date=date)
                serializer = ForecastSerializer({
                        'min_temperature': city_n_date.min_temperature,
                        'max_temperature': city_n_date.max_temperature,
                    })
                return Response(serializer.data)

            except WeatherData.DoesNotExist:

                result = get_city(city)

                if not result['success']:
                    return Response(
                        {'error': result['error']},
                        status=result['status']
                    )

                # Кэширование погоды
                weather_cache_key = f"weather_{result['latitude']:.3f}_{result['longitude']:.3f}"
                weather_data = cache.get(weather_cache_key)

                if not weather_data:
                    try:
                        response = requests.get(
                            "https://api.open-meteo.com/v1/forecast",
                            params={
                                'latitude': result['latitude'],
                                'longitude': result['longitude'],
                                'daily': 'temperature_2m_max,temperature_2m_min',
                                'timezone': 'auto',
                                'forecast_days': 11,
                            },
                            timeout=10,
                        )
                        weather_data = response.json()
                        if 'daily' in weather_data:
                            cache.set(weather_cache_key, weather_data, timeout=60*60)
                        else:
                            return Response(
                                {'error': 'Данные о погоде недоступны'},
                                status=503
                            )
                    except requests.RequestException:
                        return Response(
                            {'error': 'Ошибка метеослужбы'},
                            status=503
                        )

                # Извлечение данных по дате
                date_iso = datetime.strptime(date, '%d.%m.%Y').date().strftime("%Y-%m-%d")
                try:
                    dates = weather_data['daily']['time']

                    indx = dates.index(date_iso)

                    serializer = ForecastSerializer({
                        'min_temperature': weather_data['daily']['temperature_2m_min'][indx],
                        'max_temperature': weather_data['daily']['temperature_2m_max'][indx],
                    })
                    return Response(serializer.data)

                except (KeyError, IndexError):
                    return Response(
                        {'error': 'Ошибка анализа данных о погоде'},
                        status=500
                    )

        serializer = ForecastSerializer({
                        'min_temperature': city_n_date_data['min_temperature'],
                        'max_temperature': city_n_date_data['max_temperature'],
                    })
        return Response(serializer.data)

    def post(self, request):
        '''
        Позволяет вручную задать или переопределить прогноз погоды для указанного города на текущую или будущую дату
        Кэширует запись для пары город-дата на 10 дней
        Кэш переписывается при переопределении
        '''

        serializer = CreateWeatherSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        city = serializer.validated_data['city']
        date = serializer.validated_data['date']

        try:
            time.sleep(5)
            instance, created = WeatherData.objects.update_or_create(
                city=city,
                date=date,
                defaults=serializer.validated_data
            )
        except IntegrityError:
            return Response(
                {'conflict': 'Не удалось создать запись, попробуйте позже'},
                status=409
            )

        city_n_date_cache_key = f"city_n_date_{city}_{date}"
        cache.set(city_n_date_cache_key, serializer.validated_data, timeout=10*24*60*60)

        message = (
            f"Создание прогноза на {date} для города {city} успешно завершено"
            if created else
            f"Переопределение прогноза на {date} для города {city} успешно завершено"
        )

        return Response({
            'message': message,
            'data': serializer.data},
            status=201 if created else 200
        )
