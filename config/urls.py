"""addison_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path

from core.views import UploadFileView, GetAWSKeyView

urlpatterns = [
    path('addison/superadmin/', admin.site.urls),
    url('addison/upload-file', UploadFileView.as_view()),
    url('addison/aws-key', GetAWSKeyView.as_view()),
    path('addison/user/', include('accounts.urls')),
    path('addison/admin/', include('admins.urls')),
    path('addison/payments/', include('payments.urls')),
]
