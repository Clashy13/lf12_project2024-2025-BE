import os
import shutil
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lf12_crosswordReader_backend.settings')
django.setup()

from lf12_crosswordReader_backend.models import CrosswordModel

def clear_table_and_media():
    print("Clearing the CrosswordImage table...")
    CrosswordModel.objects.all().delete()
    print("Table cleared.")

    media_path = os.path.join(settings.BASE_DIR, 'media')

    if os.path.exists(media_path):
        print(f"Deleting the media folder at {media_path}...")
        shutil.rmtree(media_path)
        print("Media folder deleted.")
    else:
        print("Media folder does not exist.")

if __name__ == "__main__":
    clear_table_and_media()
