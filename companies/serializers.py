# back/companies/serializers.py
from rest_framework import serializers
from .models import Company
from schedules.models import Schedule

class CompanySerializer(serializers.ModelSerializer):
    # فیلد `active_schedule` به صراحت تعریف شد تا اطمینان حاصل شود
    # که در زمان ساخت و ویرایش شرکت، قابل ویرایش است.
    active_schedule = serializers.PrimaryKeyRelatedField(
        queryset=Schedule.objects.all(),
        allow_null=True, # اجازه می‌دهد که شرکتی برنامه اختصاصی نداشته باشد
        required=False
    )

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'contact_person', 'contact_phone', 'address', 'created_at',
            'active_schedule'
        ]