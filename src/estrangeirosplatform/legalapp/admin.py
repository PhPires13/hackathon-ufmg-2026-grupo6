from django.contrib import admin

from .models import CaseDocument, CaseRecommendation, LegalCase, LawyerAction

admin.site.register(LegalCase)
admin.site.register(CaseDocument)
admin.site.register(CaseRecommendation)
admin.site.register(LawyerAction)
