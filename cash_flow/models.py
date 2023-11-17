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
    fields :
        ndfc : stores the name of a nbfc
        collection_json : stores the collection data for a particular nbfc
    """
    nbfc = models.CharField(unique=True, max_length=200)
    collection_json = models.JSONField()


class ProjectionCollectionData(CreatedUpdatedAtMixin):
    """
    model for storing total amount and due date against a nbfc
    fields :
        nbfc : stores the name of a particular nbfc
        due_date : stores a particular due date
        amount : total amount for a nbfc
    """
    nbfc = models.ForeignKey(NbfcWiseCollectionData, null=True, on_delete=models.CASCADE)
    due_date = models.DateField()
    amount = models.FloatField()

    class Meta:
        ordering = ('-created_at',)

