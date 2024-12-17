import boto
import logging
import base64, uuid, six, imghdr
from django.core.files.base import ContentFile
from boto.s3.key import Key

import base64, hashlib, hmac, time, os

from ..utils import Constants, Api

# set boto lib debug to critical
logging.getLogger('boto').setLevel(logging.CRITICAL)
# connect to the bucket

os.environ['S3_USE_SIGV4'] = 'True'

s3 = boto.connect_s3(Api.AWS_ACCESS_KEY_ID, Api.AWS_SECRET_ACCESS_KEY, host='s3.eu-west-1.amazonaws.com')
bucket = s3.get_bucket(Api.AWS_S3_BUCKET_NAME)

IMAGE_UPLOAD_ACCEPTABLE_EXTENSIONS = ["png", "jpg", "jpeg", "gif", "svg"]


def upload(data, full_path, content_type=None):

    try:
        # create a key to keep track of our file in the storage
        k = Key(bucket)

        # location of the file on S3
        k.key = full_path

        if content_type:
            k.content_type = content_type

        # Upload
        k.set_contents_from_string(data)

        # we need to make it public so it can be accessed publicly
        k.make_public()

    except Exception as error:
        return "Upload error: {}".format(error)


def get_extension(file):
    ext = file.name.split(".")
    return ext[len(ext)-1].lower()


def get_image_extension(file):

    allowed_extensions = Constants.IMAGE_UPLOAD_ACCEPTABLE_EXTENSIONS

    ext = file.name.split(".")

    if ext[len(ext)-1].lower() in allowed_extensions:
        return ext[len(ext)-1].lower()
    else:
        return "jpg"


def to_internal_value(data):
    # Check if this is a base64 string
    if isinstance(data, six.string_types):
        # Check if the base64 string is in the "data:" format
        if 'data:' in data and ';base64,' in data:
            # Break out the header from the base64 content
            header, data = data.split(';base64,')

        # Try to decode the file. Return validation error if it fails.
        try:
            decoded_file = base64.b64decode(data)
        except TypeError:
            print("Invalid file")

        # Generate file name:
        file_name = str(uuid.uuid4())[:12]  # 12 characters are more than enough.
        # Get the file name extension:
        file_extension = get_file_extension(file_name, decoded_file)
        complete_file_name = "%s.%s" % (file_name, file_extension,)

        data = ContentFile(decoded_file, name=complete_file_name)

    return data


def get_file_extension(file_name, decoded_file):
    extension = imghdr.what(file_name, decoded_file)
    extension = "jpg" if extension == "jpeg" else extension

    return extension


def get_upload_link(file):
    link = s3.generate_url_sigv4(1000, 'PUT', Api.AWS_S3_BUCKET_NAME, file.url[1:])
    return link


def delete(file_url):
    if not file_url:
        return

    k = Key(bucket)
    k.key = file_url
    k.delete()


def exists(file_url):
    k = Key(bucket)
    k.key = file_url
    return k.exists()



