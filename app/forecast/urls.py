from django.urls import path

from forecast.views import ForecastView

app_name = 'forecast'

urlpatterns = [
    path('forecast/', ForecastView.as_view())
]
