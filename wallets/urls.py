# wallets/urls.py
from django.urls import path
from .views import WalletDepositView, MyCompanyWalletView, CompanyWalletDepositView, WalletWithdrawView

urlpatterns = [
    # URL for Super Admins to deposit funds into any company wallet
    path('<int:company_id>/deposit/', WalletDepositView.as_view(), name='wallet-deposit'),
    # URL for Super Admins to withdraw funds
    path('<int:company_id>/withdraw/', WalletWithdrawView.as_view(), name='wallet-withdraw'),
    # URL for Company Admins to view their own company wallet
    path('my-company/', MyCompanyWalletView.as_view(), name='my-company-wallet'),
    # URL for Company Admins to deposit into their own wallet
    path('my-company/deposit/', CompanyWalletDepositView.as_view(), name='company-wallet-deposit'),
]