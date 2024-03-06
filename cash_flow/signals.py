from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from cash_flow.models import NBFCEligibilityCashFlowHead
from cash_flow.tasks import populate_should_assign_should_check_cache


@receiver(post_save, sender=NBFCEligibilityCashFlowHead, dispatch_uid="cache_for_should_assign_and_should_check")
@receiver(post_delete, sender=NBFCEligibilityCashFlowHead, dispatch_uid="cache_for_should_assign_and_should_check")
def create_should_check_and_should_assign(sender, instance, **kwargs):
    """
    signal function to create cache for should check and should assign attribute and cache time =~ 10 years
    :return:
    """
    populate_should_assign_should_check_cache()
