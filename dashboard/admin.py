from django.contrib import admin
from .models import UploadedImage, Tenant,Room, Payment
from dateutil.relativedelta import relativedelta
from tenant.models import MaintenanceRequest

admin.site.register(UploadedImage)

admin.site.register(Room)

class TenantAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'full_name', 'amount', 'lease_start', 'end_date', 'emergency_contact']

    readonly_fields = ['end_date']

    def save_model(self, request, obj, form, change):
        if not obj.end_date:
            base_amount = 2500
            months_duration = int(obj.amount // base_amount)

            if months_duration > 0:
                obj.end_date = obj.lease_start + relativedelta(months=months_duration)
            else:
                obj.end_date = obj.lease_start + relativedelta(months=1)

        super().save_model(request, obj, form, change)
        
admin.site.register(Tenant, TenantAdmin)

admin.site.register(MaintenanceRequest)

admin.site.register(Payment)