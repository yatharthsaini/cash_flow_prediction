from django.db import models


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

    def __str__(self):
        return f"{self.branch_name} is the nbfc_name"


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

    class Meta:
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
