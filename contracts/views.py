# contracts/views.py
from rest_framework import viewsets
from .models import Contract
from .serializers import ContractSerializer
from core.permissions import IsSuperAdmin

class ContractViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Super Admins to create, view, and manage service contracts.
    """
    queryset = Contract.objects.select_related('company').all().order_by('-start_date')
    serializer_class = ContractSerializer
    permission_classes = [IsSuperAdmin]