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


class UserPermissionModel(CreatedUpdatedAtMixin):
    """
        model to maintain the user permission
    """
    user_id = models.BigIntegerField()
    email = models.EmailField(null=True, blank=True)
    role = models.CharField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


class NbfcWiseCollectionData(CreatedUpdatedAtMixin):
    """
        model for storing the nbfc name and corresponding collection json against it.
        nbfc : stores the name of a nbfc -> str
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
        return f"{self.nbfc}"

    nbfc = models.CharField(unique=True, max_length=200)
    collection_json = models.JSONField()

    class Meta:
        ordering = ('-created_at',)


class ProjectionCollectionData(CreatedUpdatedAtMixin):
    """
        model for storing total amount and due date against a nbfc
        nbfc : stores the name of a particular nbfc -> str
        due_date : stores a particular due date -> date field
        amount : total amount for a nbfc -> float
    """
    def __str__(self):
        return f"{self.nbfc} is the nbfc with total amount: {self.amount}"

    nbfc = models.ForeignKey(NbfcWiseCollectionData, null=True, on_delete=models.CASCADE)
    due_date = models.DateField()
    amount = models.FloatField()

    class Meta:
        ordering = ('-created_at',)

