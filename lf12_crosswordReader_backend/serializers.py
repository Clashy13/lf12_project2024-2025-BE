from rest_framework import serializers
from .models import CrosswordModel


class OverviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrosswordModel
        fields = ["id", "title", "uploaded_at"]


class ImagePathSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrosswordModel
        fields = ["original_image", "solved_image"]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if hasattr(instance, "original_image"):
            ret["original_image"] = self.fields["original_image"].to_representation(
                instance.original_image
            )
        if hasattr(instance, "solved_image"):
            ret["solved_image"] = self.fields["solved_image"].to_representation(
                instance.solved_image
            )
        return ret


class CreateImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrosswordModel
        fields = ["original_image"]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if hasattr(instance, "image"):
            ret["original_image"] = self.fields["original_image"].to_representation(
                instance.image
            )
        return ret
