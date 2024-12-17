from ..category.models import Category
from ..item.models import Item
from ..user.models import User
from ..item.serializers import ItemCreateSerializer
from ..job.models import Job

from ..utils import Mail, Constants

import csv, codecs, json


def import_file(job_id, user_id):
    job = Job.objects.get(id=job_id)
    rows = json.loads(job.data)["rows"]

    current_user = User.objects.get(id=user_id)

    skipped_rows = []
    index = 1

    for row in rows:
        title = row['title']
        category_title = row["category_title"]
        subcategory_title = row["subcategory_title"]

        index += 1
        if title == "NULL" or len(title) == 0:
            skipped_rows.append({"row": index, "reason": "'title' is empty"})
            continue

        if category_title == "NULL" or len(category_title) == 0:
            skipped_rows.append({"row": index, "reason": "'category' is empty"})
            continue

        if subcategory_title == "NULL" or len(subcategory_title) == 0:
            skipped_rows.append({"row": index, "reason": "'subcategory' is empty"})
            continue

        category = Category.objects.filter(title__iexact=category_title).first()
        if not category:
            skipped_rows.append({"row": index, "reason": f"category: {category_title} doesn't exist"})
            continue

        subcategory = Category.objects.filter(title__iexact=subcategory_title,
                                              parent__title__iexact=category_title).first()
        if not subcategory:
            skipped_rows.append({"row": index,
                                 "reason": f"subcategory: {subcategory_title} doesn't exist or belongs to different category"})
            continue

        try:
            image = get_image(row['image_url'], subcategory, current_user.role)
        except Exception as e:
            skipped_rows.append({"row": index, "reason": f"there is an issue with the image"})
            # print(f"{index}: {row['Image url (.jpg or .png only)']} issue with image: {e}")
            continue

        data = {
            "title": title,
            "description": row["description"],
            "image": image,
            "subcategory": subcategory
        }

        item, created = Item.objects.get_or_create(title__iexact=title, defaults={**data})

        if not created:
            skipped_rows.append({"row": index, "reason": f"Item with this title: {title} already exists"})

    if len(skipped_rows) > 0:
        from ..tasks import send_mail
        skipped_rows_data = {
            "skipped_rows": skipped_rows
        }
        job.errors = json.dumps(skipped_rows_data)
        job.save()

        send_mail("send_import_items_skipped_rows", skipped_rows, current_user.email)

    return


def get_image(image_url, subcategory, user_role):
    from ..image.models import Image
    from django.core.files.base import ContentFile
    from ..image.serializers import ImageCreateSerializer
    import requests
    from io import BytesIO
    image_url = image_url.replace('\r\n', '').strip()

    if image_url == "NULL" or image_url == '':
        subcategory_image = subcategory.image
        image = Image.objects.create(thumbnail=subcategory_image.thumbnail,
                                     banner=subcategory_image.banner,
                                     original=subcategory_image.original)

        return image

    image_response = requests.get(image_url)

    content_type = image_response.headers["Content-Type"]
    if content_type not in Constants.ITEM_IMAGE_UPLOAD_ACCEPTABLE_EXTENSIONS:
        raise Exception(f"extension should be in {Constants.ITEM_IMAGE_UPLOAD_ACCEPTABLE_EXTENSIONS}")

    image_in_bytes = BytesIO(image_response.content)
    data = {
        "file": ContentFile(image_in_bytes.getvalue(), "item.png"),
        "user_type": user_role,
    }

    serializer = ImageCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    image = serializer.save()

    return image