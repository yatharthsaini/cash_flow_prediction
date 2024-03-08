from django.contrib import admin
from cash_flow.models import (NBFCEligibilityCashFlowHead, CollectionAndLoanBookedData, LoanDetail,
                              ProjectionCollectionData, NbfcBranchMaster, NbfcWiseCollectionData, CapitalInflowData,
                              HoldCashData, UserRatioData, LoanBookedLogs, CollectionLogs, UserPermissionModel)


class NBFCEligibilityAdmin(admin.ModelAdmin):
    model = NBFCEligibilityCashFlowHead
    search_fields = ['nbfc']
    list_display = ['nbfc', 'loan_type', 'min_cibil_score', 'min_loan_tenure', 'max_loan_tenure', 'min_loan_amount',
                    'max_loan_amount', 'min_age', 'max_age', 'should_check', 'should_assign']
    list_filter = ['loan_type']


# Register your models here.
admin.site.register(NBFCEligibilityCashFlowHead, NBFCEligibilityAdmin)


class CollectionAndLoanBookedDataAdmin(admin.ModelAdmin):
    model = CollectionAndLoanBookedData
    search_fields = ['nbfc']
    list_display = ['nbfc', 'due_date', 'collection', 'created_at', 'updated_at']
    list_filter = ['nbfc', 'due_date', 'created_at', 'updated_at']


admin.site.register(CollectionAndLoanBookedData, CollectionAndLoanBookedDataAdmin)


class LoanDetailAdmin(admin.ModelAdmin):
    model = LoanDetail
    search_fields = ['nbfc', 'user_id', 'status', 'credit_limit', 'user_type']
    list_display = ['id', 'loan_id', 'loan_type', 'nbfc', 'user_id', 'credit_limit', 'status', 'user_type', 'age', 'created_at', 'updated_at']
    list_filter = ['nbfc', 'status', 'user_type', 'created_at', 'updated_at']


admin.site.register(LoanDetail, LoanDetailAdmin)


class ProjectionCollectionAdmin(admin.ModelAdmin):
    model = ProjectionCollectionData
    search_fields = ['nbfc']
    list_display = ['nbfc', 'due_date', 'collection_date', 'old_user_amount', 'new_user_amount', 'created_at']
    list_filter = ['nbfc', 'due_date', 'collection_date', 'created_at']


admin.site.register(ProjectionCollectionData, ProjectionCollectionAdmin)


class NbfcBranchMasterAdmin(admin.ModelAdmin):
    model = NbfcBranchMaster
    search_fields = ['id', 'branch_name']
    list_display = ['id', 'branch_name', 'delay_in_disbursal', 'created_at', 'updated_at']
    list_filter = ['id', 'branch_name', 'created_at', 'updated_at']


admin.site.register(NbfcBranchMaster, NbfcBranchMasterAdmin)


class NbfcWiseCollectionAdmin(admin.ModelAdmin):
    model = NbfcWiseCollectionData
    search_fields = ['nbfc']
    list_display = ['nbfc', 'due_date', 'created_at', 'updated_at']
    list_filter = ['nbfc', 'due_date', 'created_at', 'updated_at']


admin.site.register(NbfcWiseCollectionData, NbfcWiseCollectionAdmin)


class CapitalInflowAdmin(admin.ModelAdmin):
    model = CapitalInflowData
    search_fields = ['nbfc']
    list_display = ['nbfc', 'capital_inflow', 'created_at', 'updated_at']
    list_filter = ['nbfc', 'created_at', 'updated_at']


admin.site.register(CapitalInflowData, CapitalInflowAdmin)


class HoldCashAdmin(admin.ModelAdmin):
    model = HoldCashData
    search_fields = ['nbfc']
    list_display = ['nbfc', 'hold_cash', 'created_at', 'updated_at']
    list_filter = ['nbfc', 'created_at', 'updated_at']


admin.site.register(HoldCashData, HoldCashAdmin)


class UserRatioAdmin(admin.ModelAdmin):
    model = UserRatioData
    search_fields = ['nbfc']
    list_display = ['nbfc', 'old_percentage', 'new_percentage', 'created_at', 'updated_at']
    list_filter = ['nbfc', 'created_at', 'updated_at']


admin.site.register(UserRatioData, UserRatioAdmin)


class LoanBookedLogsAdmin(admin.ModelAdmin):
    model = LoanBookedLogs
    search_fields = ['loan']
    list_display = ['loan', 'log_text', 'amount', 'request_type', 'created_at', 'updated_at']
    list_filter = ['request_type', 'log_text', 'created_at', 'updated_at']


admin.site.register(LoanBookedLogs, LoanBookedLogsAdmin)


class CollectionLogsAdmin(admin.ModelAdmin):
    model = CollectionLogs
    search_fields = ['collection']
    list_display = ['collection', 'amount', 'log_text', 'created_at', 'updated_at']
    list_filter = ['log_text', 'created_at', 'updated_at']


admin.site.register(CollectionLogs, CollectionLogsAdmin)


class UserPermissionAdmin(admin.ModelAdmin):
    model = UserPermissionModel
    search_fields = ['user_id', 'email']
    list_display = ['user_id', 'email', 'role', 'is_active']
    list_filter = ['role']


admin.site.register(UserPermissionModel, UserPermissionAdmin)
