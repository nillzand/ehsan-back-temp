# back/surveys/views.py
from rest_framework import viewsets, permissions
from .models import Survey
from .serializers import SurveySerializer

class SurveyViewSet(viewsets.ModelViewSet):
    """
    API endpoint برای ثبت و مشاهده نظرسنجی‌ها.
    """
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        [اصلاح] کوئری امن‌تر شده تا از کرش کردن به دلیل وجود food_item=NULL جلوگیری شود.
        """
        user = self.request.user
        # به جای 'order__food_item'، فقط تا 'order' جوین می‌زنیم
        base_query = Survey.objects.select_related('user', 'order')

        if user.is_staff or user.role in ['SUPER_ADMIN', 'COMPANY_ADMIN']:
            # برای ادمین‌ها، اطلاعات شرکت کاربر را نیز برای نمایش بهتر جوین می‌زنیم
            return base_query.select_related('user__company').all()
        
        return base_query.filter(user=user)

    def perform_create(self, serializer):
        """
        کاربر ثبت‌کننده نظر را به صورت خودکار کاربر لاگین کرده قرار می‌دهد.
        """
        serializer.save(user=self.request.user)