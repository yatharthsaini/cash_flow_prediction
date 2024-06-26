from django.db import models
from django.db.models import Q

LOAN_TYPE_CHOICES = (
        ('P', 'PAYDAY'),
        ('E', 'PERSONAL_LOAN')
    )

LOAN_STATUS_CHOICES = (
        ('I', 'Initiated'),
        ('P', 'Passed'),
        ('F', 'Failed'),
    )

USER_TYPE_CHOICES = (
    ('O', 'Old'),
    ('N', 'New'),
)

REQUEST_TYPE = (
    ('CL', 'Credit Limit'),
    ('LAN', 'Loan Application'),
    ('LAD', 'Loan Applied'),
    ('LF', 'Loan failed'),
    ('BE', 'Booking Expired'),
)


class CreatedUpdatedAtMixin(models.Model):
    """
        Base model for only created_at and
        updated_at which is inherited by all
        the model classes...
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SetForFutureDateMixin(models.Model):
    """
    Base Model for having the start date, end_date and the boolean flag for set for future dates
    """
    start_date = models.DateField()
    end_date = models.DateField(null=True)

    class Meta:
        abstract = True


class UserPermissionModel(CreatedUpdatedAtMixin):
    """
        model to maintain the user permission
    """
    user_id = models.BigIntegerField()
    email = models.EmailField(null=True, blank=True)
    role = models.CharField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


class NbfcBranchMaster(CreatedUpdatedAtMixin):
    branch_name = models.CharField(max_length=250)
    is_enable = models.BooleanField(default=True)
    delay_in_disbursal = models.FloatField(null=True)

    def __str__(self):
        return f"{self.branch_name} - {self.id}"


class NbfcWiseCollectionData(CreatedUpdatedAtMixin):
    """
        model for storing the nbfc id and corresponding collection json against it.
        nbfc : stores the corresponding id for a NBFC
        collection_json : stores the collection data for a particular nbfc
        format :
        {
            <due_date> : {
                "New" : {
                : value in percentage,
                : value in percentage,
                : value in percentage,
                : value in percentage,
                },
                "Old" : {
                : value in percentage,
                : value in percentage,
                : value in percentage,
                : value in percentage,
                }
            }
        }
    """
    def __str__(self):
        return f"{self.nbfc} is the nbfc"

    nbfc = models.ForeignKey(NbfcBranchMaster, on_delete=models.CASCADE)
    collection_json = models.JSONField(null=True)
    due_date = models.DateField()

    class Meta:
        unique_together = ('nbfc', 'due_date')
        ordering = ('-created_at',)


class ProjectionCollectionData(CreatedUpdatedAtMixin):
    """
        model for storing total amount and due date against a
        nbfc : stores the name of a particular nbfc -> str
        due_date : stores a particular due date -> date field
        collection_date : stores the date of collection that is varying from the due_date by -7 to -45
        amount : total amount for a nbfc -> float
    """
    def __str__(self):
        return f"{self.nbfc} is the nbfc with total amount: {self.amount}"

    nbfc = models.ForeignKey(NbfcBranchMaster, on_delete=models.CASCADE)
    due_date = models.DateField()
    collection_date = models.DateField()
    amount = models.FloatField()
    old_user_amount = models.FloatField()
    new_user_amount = models.FloatField()
    due_amount = models.FloatField()

    class Meta:
        ordering = ('-created_at',)


class CollectionAndLoanBookedData(CreatedUpdatedAtMixin):
    """
    model for storing the real time fields of collection and loan_booked which are real-time stored for
    a particular nbfc and due_Date
    collection: a float value
    loan_booked: a float value
    """
    nbfc = models.ForeignKey(NbfcBranchMaster, on_delete=models.CASCADE)
    due_date = models.DateField()
    collection = models.FloatField(null=True)
    loan_booked = models.FloatField(null=True)
    last_day_balance = models.FloatField(default=0)

    def __str__(self):
        return (f"{self.nbfc} with due_date {self.due_date} with collection {self.collection} and "
                f"loan_booked {self.loan_booked}")

    class Meta:
        ordering = ('-created_at',)


class CapitalInflowData(CreatedUpdatedAtMixin, SetForFutureDateMixin):
    """
    model for storing capital inflow data
    """
    nbfc = models.ForeignKey(NbfcBranchMaster, on_delete=models.CASCADE)
    capital_inflow = models.FloatField()

    def __str__(self):
        return (f"{self.nbfc} with capital_inflow {self.capital_inflow} with start_date {self.start_date}"
                f"and end_date {self.end_date}")

    class Meta:
        ordering = ('-created_at',)


class HoldCashData(CreatedUpdatedAtMixin, SetForFutureDateMixin):
    """
    model for storing the hold cash data
    """
    nbfc = models.ForeignKey(NbfcBranchMaster, on_delete=models.CASCADE)
    hold_cash = models.FloatField()

    def __str__(self):
        return (f"{self.nbfc} with hold_cash {self.hold_cash} with the start_date {self.start_date} "
                f"and end_date {self.end_date}")

    class Meta:
        ordering = ('-created_at',)


class UserRatioData(CreatedUpdatedAtMixin, SetForFutureDateMixin):
    """
    model for storing the old to new ratio
    """
    nbfc = models.ForeignKey(NbfcBranchMaster, on_delete=models.CASCADE)
    old_percentage = models.FloatField()
    new_percentage = models.FloatField()

    def __str__(self):
        return (f"{self.nbfc} with old_user_percentage as {self.old_percentage} with start_date {self.start_date} and "
                f"end_date {self.end_date}")

    class Meta:
        ordering = ('-created_at',)


class NBFCEligibilityCashFlowHead(CreatedUpdatedAtMixin):
    """
    model for storing the NBFC eligibility parameters
    """

    nbfc = models.ForeignKey(NbfcBranchMaster, on_delete=models.CASCADE)
    loan_type = models.CharField(max_length=3, choices=LOAN_TYPE_CHOICES)
    min_cibil_score = models.IntegerField()
    min_loan_tenure = models.IntegerField()
    max_loan_tenure = models.IntegerField()
    min_loan_amount = models.FloatField()
    max_loan_amount = models.FloatField()
    should_check = models.BooleanField(default=True)
    should_assign = models.BooleanField(default=True)
    min_age = models.IntegerField(null=True)
    max_age = models.IntegerField(null=True)
    ckyc = models.BooleanField(default=False)
    ekyc = models.BooleanField(default=False)
    mkyc = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nbfc} is the nbfc_id of the branch"

    class Meta:
        ordering = ('-created_at',)


class LoanDetail(CreatedUpdatedAtMixin):
    """
    model to store the loan detail fields such as loan_id, user_id, nbfc, credit_limit, amount, status
    """
    nbfc = models.ForeignKey(NbfcBranchMaster, on_delete=models.CASCADE)
    credit_limit = models.FloatField()
    loan_id = models.IntegerField(null=True)
    loan_type = models.CharField(max_length=5)
    user_id = models.IntegerField()
    amount = models.FloatField(null=True)
    status = models.CharField(max_length=1, choices=LOAN_STATUS_CHOICES, null=True)
    user_type = models.CharField(max_length=1, choices=USER_TYPE_CHOICES, default='O')
    cibil_score = models.IntegerField()
    is_booked = models.BooleanField(default=False)
    age = models.IntegerField(null=True)
    ckyc = models.BooleanField(default=False)
    ekyc = models.BooleanField(default=False)
    mkyc = models.BooleanField(default=False)


class LoanBookedLogs(CreatedUpdatedAtMixin):
    """
    model to store the loan booked logs of a particular loan
    """
    loan = models.ForeignKey(LoanDetail, on_delete=models.CASCADE)
    amount = models.FloatField()
    log_text = models.TextField()
    request_type = models.CharField(max_length=3, choices=REQUEST_TYPE, default="CL")


class CollectionLogs(CreatedUpdatedAtMixin):
    """
    models to store the collection logs of a particular loan
    amount here is the difference of amount in collection between two celery tasks of populating the
    collection amount
    """
    collection = models.ForeignKey(CollectionAndLoanBookedData, on_delete=models.CASCADE)
    amount = models.FloatField()
    log_text = models.CharField(max_length=50, default='Collection amount updated')

    class Meta:
        ordering = ('-created_at',)
