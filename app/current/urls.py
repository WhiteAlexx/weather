from django.urls import path

from current.views import CurrentView

app_name = 'current'

urlpatterns = [
    path('current/', CurrentView.as_view())
]
