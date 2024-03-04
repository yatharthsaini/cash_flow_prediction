from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache

from cash_flow.models import NBFCEligibilityCashFlowHead


@receiver(post_save, sender=NBFCEligibilityCashFlowHead)
def create_should_check_cache(sender, instance, **kwargs):
    """
    signal function to create cache for should check attribute
    :return:
    """
    try:
        should_check_branches = list(
            NBFCEligibilityCashFlowHead.objects.filter(should_check=True).values_list('nbfc_id', flat=True))
        cache.set('should_check', should_check_branches, timeout=None)
    except Exception as e:
        print(e)


@receiver(post_save, sender=NBFCEligibilityCashFlowHead)
def create_should_assign_cache(sender, instance, **kwargs):
    """
    signal function to create cache for should assign attribute
    :return:
    """
    try:
        should_assign_branches = list(
            NBFCEligibilityCashFlowHead.objects.filter(should_assign=True).values_list('nbfc_id', flat=True))
        cache.set('should_check', should_assign_branches, timeout=None)
    except Exception as e:
        print(e)
