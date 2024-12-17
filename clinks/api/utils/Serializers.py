from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist

from ..utils import Message, Exception, Constants


def get_optimized_fields(fields, fields_to_be_optimized, optimization_type):
    optimized_fields = []

    for field_to_be_optimized in fields_to_be_optimized:
        field = fields[field_to_be_optimized]

        if not needs_optimisation(field, optimization_type):
            continue

        nested_optimized_fields = []
        get_nested_optimised_fields(field_to_be_optimized, field, nested_optimized_fields, optimization_type)

        if len(nested_optimized_fields) == 0:
            nested_optimized_fields = [field_to_be_optimized]

        optimized_fields = optimized_fields + nested_optimized_fields

    return optimized_fields


def needs_optimisation(field, optimization_type):
    if issubclass(field.__class__, serializers.PrimaryKeyRelatedField):
        return True
    if optimization_type == "select_related" and issubclass(field.__class__, serializers.Serializer):
        return True
    if optimization_type == "prefetch_related" and issubclass(field.__class__, serializers.ListSerializer):
        return True

    return False


def get_nested_optimised_fields(key, nested, nested_optimized_fields, optimization_type):
    if not hasattr(nested, "get_fields"):
        return

    fields = nested.get_fields()
    for field in fields:
        current = fields[field]

        if not needs_optimisation(current, optimization_type):
            continue

        nested_optimized_fields.append(f"{key}__{field}")
        get_nested_optimised_fields(f"{key}__{field}", current, nested_optimized_fields, optimization_type)


class BaseModelSerializer(serializers.ModelSerializer):
    optimisation_enabled = True

    def optimise(self, queryset):
        if not self.optimisation_enabled:
            return queryset

        if not hasattr(self, "get_select_related_fields") and not hasattr(self, "get_prefetch_related_fields"):
            print(f"\033[93m{self.__class__} query not optimised\x1b[0m")
            return queryset

        select_related_fields = None
        prefetch_related_fields = None

        fields = self.get_fields()

        if hasattr(self, "get_select_related_fields"):
            select_related_fields_to_be_optimized = self.get_select_related_fields()
            select_related_fields = get_optimized_fields(fields, select_related_fields_to_be_optimized, "select_related")

        if hasattr(self, "get_prefetch_related_fields"):
            prefetch_related_fields_to_be_optimized = self.get_prefetch_related_fields()
            prefetch_related_fields = get_optimized_fields(fields, prefetch_related_fields_to_be_optimized,
                                                         "prefetch_related")

        if select_related_fields:
            queryset = queryset.select_related(*select_related_fields)

        if prefetch_related_fields:
            queryset = queryset.prefetch_related(*prefetch_related_fields)

        return queryset

    def raise_validation_error(self, key, error):
        data = dict()
        data[key] = error
        raise serializers.ValidationError(data)

    def validate_enum_field(self, key, value, options):
        if value not in options:
            return self.raise_validation_error(key, f"'{key} needs to be one of {options}'")

        return value

    def run_validation(self, *args, **kwargs):
        if not self.partial:
            with MonkeyPatchPartial(self.root):
                return super().run_validation(*args, **kwargs)
        return super().run_validation(*args, **kwargs)

    def save_nested_object_list(self, parent_key, parent_class, nested_class, nested_class_data,
                                nested_edit_serializer, nested_create_serializer, primary_key="id"):

        nested_class.objects.filter(**{f"{parent_key}__id": parent_class.id}).all().delete()

        if not nested_class_data:
            return parent_class

        order = 0

        for data in nested_class_data:
            data["order"] = order
            self.save_nested_object(parent_key, parent_class, nested_class, data, nested_edit_serializer, nested_create_serializer, primary_key)
            order += 1

        return parent_class

    def save_nested_object(self, parent_key, parent_class, nested_class, nested_class_data,
                           nested_edit_serializer, nested_create_serializer, primary_key="id"):

        if primary_key in nested_class_data:
            nested_class_data["deleted_at"] = None
            id = nested_class_data[primary_key]
            object = nested_class.all_objects.get(**{f"{primary_key}": id})
            serializer = nested_edit_serializer(instance=object, data=nested_class_data, partial=True)
            serializer.update(object, nested_class_data)
        else:
            nested_class_data[f"{parent_key}"] = parent_class
            serializer = nested_create_serializer(data=nested_class_data)
            serializer.create(nested_class_data)

        return parent_class


class BaseSerializer(serializers.Serializer):

    def optimise(self, queryset):
        return queryset.select_related(self.get_select_related_fields()) \
            .prefetch_related(self.get_prefetch_related_fields())

    def raise_validation_error(self, key, error):
        raise serializers.ValidationError(error)

    @staticmethod
    def get_select_related_fields():
        return []

    @staticmethod
    def get_prefetch_related_fields():
        return []

    def run_validation(self, *args, **kwargs):
        if not self.partial:
            with MonkeyPatchPartial(self.root):
                return super().run_validation(*args, **kwargs)
        return super().run_validation(*args, **kwargs)


class CreateModelSerializer(BaseModelSerializer):
    class Meta:
        pass

    def update(self, instance, validated_data):
        raise Exception.raiseError(Message.create("Create Model Serializer does not support 'update'"))


class CreateSerializer(BaseSerializer):

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        raise Exception.raiseError(Message.create("Create Serializer does not support 'update'"))


class EditModelSerializer(BaseModelSerializer):
    class Meta:
        pass

    def create(self, validated_data):
        raise Exception.raiseError(Message.create("Edit Model Serializer does not support 'create'"))


class EditSerializer(BaseSerializer):

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        raise Exception.raiseError(Message.create("Edit Serializer does not support 'create'"))


class ValidateSerializer(BaseSerializer):

    def create(self, validated_data):
        raise Exception.raiseError(Message.create("Validate Serializer does not support 'create'"))

    def update(self, instance, validated_data):
        raise Exception.raiseError(Message.create("Validate Serializer does not support 'update'"))


class ListModelSerializer(BaseModelSerializer):

    class Meta:
        pass

    def create(self, validated_data):
        raise Exception.raiseError(Message.create("List Model Serializer does not support 'creeate'"))

    def update(self, instance, validated_data):
        raise Exception.raiseError(Message.create("List Model Serializer does not support 'update'"))


class ListSerializer(BaseSerializer):
    def create(self, validated_data):
        raise Exception.raiseError(Message.create("List Serializer does not support 'creeate'"))

    def update(self, instance, validated_data):
        raise Exception.raiseError(Message.create("List Serializer does not support 'update'"))


class ValidateModelSerializer(BaseModelSerializer):
    class Meta:
        pass

    def create(self, validated_data):
        raise Exception.raiseError(Message.create("Validate Model Serializer does not support 'create'"))

    def update(self, instance, validated_data):
        raise Exception.raiseError(Message.create("Validate Model Serializer does not support 'update'"))


# https://github.com/encode/django-rest-framework/issues/6599
# returns the original pk instead of the object
class PrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):

    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        try:
            res = self.get_queryset().get(pk=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)
        else:
            return data


class MonkeyPatchPartial:
    """
    Work around bug #3847 in djangorestframework by monkey-patching the partial
    attribute of the root serializer during the call to validate_empty_values.
    """

    def __init__(self, root):
        self._root = root

    def __enter__(self):
        self._old = getattr(self._root, 'partial')
        setattr(self._root, 'partial', False)

    def __exit__(self, *args):
        setattr(self._root, 'partial', self._old)