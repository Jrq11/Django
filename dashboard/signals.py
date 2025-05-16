from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Tenant, Room, Payment
from django.db.models import F
from decimal import Decimal

@receiver(post_save, sender=Tenant)
def update_room_availability_on_tenant_save(sender, instance, **kwargs):
    room = instance.room_number
    room.availability = 'Occupied'
    room.save()

@receiver(post_delete, sender=Tenant)
def update_room_availability_on_tenant_delete(sender, instance, **kwargs):
    room = instance.room_number
    room.availability = 'Vacant'
    room.save()
    
@receiver(post_save, sender=Payment)
def update_tenant_amount_and_end_date_on_create(sender, instance, created, **kwargs):
    if created:
        tenant = instance.tenant
        tenant.amount += Decimal(instance.amount)
        tenant.save()

@receiver(post_delete, sender=Payment)
def subtract_payment_and_recompute_end_date_on_delete(sender, instance, **kwargs):
    tenant = instance.tenant
    tenant.amount -= Decimal(instance.amount)
    tenant.save()