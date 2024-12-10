import os
import uuid
from django.db import models

def get_file_path(instance, filename, path):
    ext = filename.split('.')[-1]
    if instance.pk:
        filename = f"{instance.pk}.{ext}"
    else:
        filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join(path, filename)


def original_image_path(instance, filename):
    return get_file_path(instance, filename, 'original/')


def solved_image_path(instance, filename):
    return get_file_path(instance, filename, 'solved/')


class CrosswordModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    original_image = models.ImageField(upload_to=original_image_path)
    solved_image = models.ImageField(upload_to=solved_image_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
