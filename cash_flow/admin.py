from django.contrib import admin
from cash_flow.models import (NBFCEligibilityCashFlowHead, CollectionAndLoanBookedData, LoanDetail,
                              ProjectionCollectionData)

# Register your models here.
admin.site.register(NBFCEligibilityCashFlowHead)


class CollectionAndLoanBookedDataAdmin(admin.ModelAdmin):
    model = CollectionAndLoanBookedData
    search_fields = ['nbfc']
    list_display = ['nbfc', 'due_date', 'collection']
    list_filter = ['nbfc', 'due_date']


admin.site.register(CollectionAndLoanBookedData, CollectionAndLoanBookedDataAdmin)


class LoanDetailAdmin(admin.ModelAdmin):
    model = LoanDetail
    search_fields = ['nbfc', 'user_id', 'status', 'credit_limit', 'user_type']
    list_display = ['nbfc', 'user_id', 'credit_limit', 'status', 'user_type']
    list_filter = ['nbfc', 'status', 'user_type', 'created_at']


admin.site.register(LoanDetail, LoanDetailAdmin)


class ProjectionCollectionAdmin(admin.ModelAdmin):
    model = ProjectionCollectionData
    search_fields = ['nbfc']
    list_display = ['nbfc', 'due_date', 'collection_date', 'old_user_amount', 'new_user_amount']
    list_filter = ['nbfc', 'due_date', 'collection_date']


admin.site.register(ProjectionCollectionData, ProjectionCollectionAdmin)
