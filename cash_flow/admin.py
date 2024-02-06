from django.contrib import admin
from cash_flow.models import NBFCEligibilityCashFlowHead, CollectionAndLoanBookedData, LoanDetail

# Register your models here.
admin.site.register(NBFCEligibilityCashFlowHead)

class CollectionAndLoanBookedDataAdmin(admin.ModelAdmin):
    model = CollectionAndLoanBookedData
    list_display = ['nbfc', 'due_date', 'collection']
admin.site.register(CollectionAndLoanBookedData, CollectionAndLoanBookedDataAdmin)

class LoanDetailAdmin(admin.ModelAdmin):
    model = LoanDetail
    list_display = ['nbfc', 'due_date', 'collection']
admin.site.register(LoanDetail, LoanDetailAdmin)
