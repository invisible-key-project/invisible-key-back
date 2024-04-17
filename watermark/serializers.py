from rest_framework import serializers

from watermark.models import ImageModel


class ImageUploadSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = ImageModel
        fields = ('image',)