from rest_framework.routers import DefaultRouter
from .views import GenericFileUploadView
from django.urls import path, include

router = DefaultRouter(trailing_slash=False)

router.register("file-upload", GenericFileUploadView)

urlpatterns = [
    path("", include(router.urls))
]
