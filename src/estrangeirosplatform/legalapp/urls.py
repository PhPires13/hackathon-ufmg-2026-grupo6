from django.urls import path

from .views import (
	case_detail_page,
	create_case_page,
	cases_list_page,
	monitoramento_aderencia_page,
)

app_name = 'legalapp'

urlpatterns = [
	path('', cases_list_page, name='home'),
	path('cases-list', cases_list_page, name='cases-list'),
	path('case-detail/<int:case_id>', case_detail_page, name='case-detail'),
	path('create-case', create_case_page, name='create-case'),
	path('monitoramento-aderencia/', monitoramento_aderencia_page, name='monitoramento-aderencia'),
]