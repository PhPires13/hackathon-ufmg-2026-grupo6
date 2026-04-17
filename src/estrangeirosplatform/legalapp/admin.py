from django.contrib import admin

from .models import CaseDocument, CaseRecommendation, LegalCase

admin.site.register(LegalCase)
admin.site.register(CaseDocument)
admin.site.register(CaseRecommendation)
