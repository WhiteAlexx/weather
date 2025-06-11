import requests

from rest_framework.views import APIView
from rest_framework.response import Response

from django.core.cache import cache

from common.utils import get_city
from current.serializers import CityQuerySerializer, CurrentSerializer


class CurrentView(APIView):

    def get(self, request):
        '''
        Возвращает текущую температуру и локальное время в указанном городе
        Кэширует данные на 5 минут
        '''

        query_serializer = CityQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        city = query_serializer.validated_data['city']

        current_cache_key = f"current_{city}"
        current_data = cache.get(current_cache_key)

        if not current_data:
            result = get_city(city)

            if not result['success']:
                return Response(
                    {'error': result['error']},
                    status=result['status']
                )

            try:
                response = requests.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        'latitude': result['latitude'],
                        'longitude': result['longitude'],
                        'current_weather': True,
                        'timezone': 'auto',
                    },
                    timeout=10,
                )
                current_weather = response.json()
                if 'current_weather' in current_weather:
                    cache.set(current_cache_key, current_weather['current_weather'], timeout=5*60)
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

            serializer = CurrentSerializer({
                'temperature': current_weather['current_weather']['temperature'],
                'local_time': current_weather['current_weather']['time'].split('T')[-1]
            })
            return Response(
                serializer.data,
                status=200
            )

        serializer = CurrentSerializer({
            'temperature': current_data['current_weather']['temperature'],
            'local_time': current_data['current_weather']['time'].split('T')[-1]
        })
        return Response(
            serializer.data,
            status=200
        )
