from django.urls import path

from .views import legal_cases_page, create_case_page

app_name = 'legalapp'

urlpatterns = [
	path('legal-cases', legal_cases_page, name='legal-cases'),
	path('create-case', create_case_page, name='create-case'),
]