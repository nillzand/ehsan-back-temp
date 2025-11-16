# users/auth_views.py

from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer # اطمینان از ایمپورت صحیح

class MyTokenObtainPairView(TokenObtainPairView):
    """
    Custom view for obtaining a JWT pair.
    Adds user role and username to the token payload.
    """
    serializer_class = MyTokenObtainPairSerializer # اطمینان از استفاده صحیح