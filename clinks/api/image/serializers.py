from rest_framework import serializers

from .models import Image

from ..utils import File, ImageSize, Constants, Api

from ..utils.Serializers import CreateModelSerializer, ListModelSerializer

import uuid


class ImageCreateSerializer(CreateModelSerializer):
    file = serializers.ImageField()

    user_type = serializers.CharField()

    class Meta:
        model = Image
        fields = ["file", "user_type"]

    def validate_file(self, file):
        extension = File.get_extension(file)
        if not extension:
            error = "Failed to read file, type must be one of {}".format(Constants.IMAGE_UPLOAD_ACCEPTABLE_EXTENSIONS)
            raise serializers.ValidationError(error)

        return file

    def validate(self, attrs):
        attrs = self.set_image_links(attrs)

        return attrs

    def set_image_links(self, attrs):
        file = attrs.pop('file')
        user_type = attrs.pop("user_type")

        path = "/images"

        if user_type == Constants.USER_ROLE_CUSTOMER:
            path += "/customers"

        else:
            path += "/companies"

        links = self.upload_photo(file, path)

        attrs["thumbnail"] = links["thumbnail"]
        attrs["banner"] = links["banner"]
        attrs["original"] = links["original"]

        return attrs

    def upload_photo(self, file, path):
        extension = File.get_extension(file)

        thumbnail_image_data = ImageSize.resize(file, ImageSize.THUMBNAIL)
        banner_image_data = ImageSize.resize(file, ImageSize.BANNER)
        original_image_data = ImageSize.resize(file)

        uid = uuid.uuid4()

        thumbnail_image_full_path_name = "{}/thumbnail_image_{}.{}".format(path, uid, extension)
        banner_image_full_path_name = "{}/banner_image_{}.{}".format(path, uid, extension)
        original_image_full_path_name = "{}/original_image_{}.{}".format(path, uid, extension)

        # Pass in the file, path on S3, name
        File.upload(banner_image_data, banner_image_full_path_name)
        File.upload(thumbnail_image_data, thumbnail_image_full_path_name)
        File.upload(original_image_data, original_image_full_path_name)

        return {
            "banner": banner_image_full_path_name,
            "thumbnail": thumbnail_image_full_path_name,
            "original": original_image_full_path_name
        }


class ImageListSerializer(ListModelSerializer):

    thumbnail = serializers.SerializerMethodField()
    banner = serializers.SerializerMethodField()
    original = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = "__all__"

    def get_banner(self, image):
        if not image.banner:
            return None

        return self.get_image_url(image.banner)

    def get_thumbnail(self, image):
        if not image.thumbnail:
            return None

        return self.get_image_url(image.thumbnail)

    def get_original(self, image):
        if not image.original:
            return None

        return self.get_image_url(image.original)

    def get_image_url(self, image_url):
        if not image_url:
            return None

        if image_url.startswith("http"):
            return image_url

        return "https://" + Api.AWS_CLOUD_FRONT_DOMAIN + image_url


class ImageDetailSerializer(ImageListSerializer):
    pass
