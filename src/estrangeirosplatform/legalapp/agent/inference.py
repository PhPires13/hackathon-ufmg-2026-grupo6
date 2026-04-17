from legalapp.models import CaseRecommendation
from .pipeline import infer_recommendation_payload


def infer_case_recommendation(legal_case):
    return infer_recommendation_payload(legal_case)


def upsert_case_recommendation(legal_case):
    payload = infer_case_recommendation(legal_case)

    recommendation, _created = CaseRecommendation.objects.update_or_create(
        case=legal_case,
        defaults=payload,
    )
    return recommendation


def generate_recommendations_for_queryset(queryset):
    created_or_updated = 0
    for legal_case in queryset:
        upsert_case_recommendation(legal_case)
        created_or_updated += 1
    return created_or_updated
