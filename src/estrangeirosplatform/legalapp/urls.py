from django.urls import path

from .views import legal_case_list

app_name = 'legalapp'

urlpatterns = [
	path('legalcases', legal_case_list, name='legalcases'),
]