from django.urls import path

from .views import case_detail_page, create_case_page, legal_cases_page

app_name = 'legalapp'

urlpatterns = [
	path('', legal_cases_page, name='home'),
	path('legal-cases', legal_cases_page, name='legal-cases'),
	path('legal-cases/<int:case_id>', case_detail_page, name='case-detail'),
	path('create-case', create_case_page, name='create-case'),
]