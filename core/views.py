# start of core/views.py
# core/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def welcome(request):
    """
    A simple view that welcomes users and points them to the main API entry points.
    """
    return Response({
        'message': 'Welcome to the Catering Service API.',
        'api_entrypoint': request.build_absolute_uri('api/'),
        'admin_panel': request.build_absolute_uri('admin/'),
    })

# end of core/views.py