# companies/views.py
from rest_framework import viewsets
from .models import Company
from .serializers import CompanySerializer
# [MODIFIED] Use the specific permission for Super Admins.
from core.permissions import IsSuperAdmin

class CompanyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows companies to be viewed or edited.
    """
    queryset = Company.objects.all().order_by('name')
    serializer_class = CompanySerializer
    # [FIXED] Only Super Admins can view or manage companies.
    permission_classes = [IsSuperAdmin]