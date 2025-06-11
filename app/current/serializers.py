from rest_framework import serializers

from common.utils import is_latin


class CityQuerySerializer(serializers.Serializer):
    city = serializers.CharField(required=True)

    def validate_city(self, value):
        return is_latin(value)


class CurrentSerializer(serializers.Serializer):

    temperature = serializers.DecimalField(max_digits=3, decimal_places=1, coerce_to_string=False)
    local_time = serializers.TimeField(format='%H:%M')
