from django.urls import path

from .views import lawyer_assistant_view


app_name = 'legalapp'

urlpatterns = [
    path('assistente-advogado/', lawyer_assistant_view, name='lawyer-assistant'),
]