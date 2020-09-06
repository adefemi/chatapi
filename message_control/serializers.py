from rest_framework.serializers import ModelSerializer
from .models import GenericFileUpload


class GenericFileUploadSerializer(ModelSerializer):

    class Meta:
        model = GenericFileUpload
        fields = "__all__"
