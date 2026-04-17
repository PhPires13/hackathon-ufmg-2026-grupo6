from django.urls import path

from .views import (
    adherence_monitoring_view,
    effectiveness_monitoring_view,
    lawyer_assistant_view,
)


app_name = 'legalapp'

urlpatterns = [
    path('assistente-advogado/', lawyer_assistant_view, name='lawyer-assistant'),
    path('monitoramento-aderencia/', adherence_monitoring_view, name='adherence-monitoring'),
    path('monitoramento-efetividade/', effectiveness_monitoring_view, name='effectiveness-monitoring'),
]