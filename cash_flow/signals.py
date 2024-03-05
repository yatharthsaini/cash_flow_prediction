from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from cash_flow.models import NBFCEligibilityCashFlowHead


@receiver(post_save, sender=NBFCEligibilityCashFlowHead, dispatch_uid="cache_for_should_assign_and_should_check")
@receiver(post_delete, sender=NBFCEligibilityCashFlowHead, dispatch_uid="cache_for_should_assign_and_should_check")
def create_should_check_and_should_assign(sender, instance, **kwargs):
    """
    signal function to create cache for should check and should assign attribute and cache time =~ 10 years
    :return:
    """
    try:
        should_check_branches = set(
            NBFCEligibilityCashFlowHead.objects.filter(should_check=True).values_list('nbfc_id', flat=True))
        cache.set('should_check', list(should_check_branches), timeout=315360000)
        should_assign_branches = set(
            NBFCEligibilityCashFlowHead.objects.filter(should_assign=True).values_list('nbfc_id', flat=True))
        cache.set('should_assign', list(should_assign_branches), timeout=315360000)
    except Exception as e:
        print(e)
