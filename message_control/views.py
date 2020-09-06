from rest_framework.viewsets import ModelViewSet
from .serializers import GenericFileUpload, GenericFileUploadSerializer


class GenericFileUploadView(ModelViewSet):
    queryset = GenericFileUpload.objects.all()
    serializer_class = GenericFileUploadSerializer
