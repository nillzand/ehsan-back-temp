# wallets/urls.py
from django.urls import path
# [MODIFIED] Import the new view
from .views import WalletDepositView, MyCompanyWalletView

urlpatterns = [
    # URL for Super Admins to deposit funds into any company wallet
    path('<int:company_id>/deposit/', WalletDepositView.as_view(), name='wallet-deposit'),

    # [NEW] URL for Company Admins to view their own company wallet
    path('my-company/', MyCompanyWalletView.as_view(), name='my-company-wallet'),
]