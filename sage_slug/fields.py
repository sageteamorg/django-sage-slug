from typing import Callable, Union, List, Tuple, Optional
from django.db import models
from django.utils.text import slugify as django_slugify
from django.db.models.signals import pre_save
from django.dispatch import receiver

class SAGESlugField(models.SlugField):
    """
    SAGESlugField extends Django's SlugField to automatically populate the slug
    from another field, enforce uniqueness, and use a custom slugify function.

    Key Features:
    - Auto-population from another field or callable.
    - Ensures global or partial uniqueness (with respect to other fields).
    - Custom slugify function support.
    - Dynamic updates on every save (optional).
    - Unicode support for slugs.

    :param populate_from: The name of the attribute or a callable to populate the slug.
    :param sep: Separator for automatically incremented slug indices (default: '-').
    :param slugify: Custom slugify function (default: Django's `slugify`).
    :param unique_with: Ensures uniqueness with respect to other fields (e.g., 'pub_date').
    :param always_update: If True, the slug is updated each time the instance is saved.
    :param allow_unicode: If True, allows Unicode characters in the slug.
    """

    def __init__(
        self,
        populate_from: Optional[Union[str, Callable]] = None,
        sep: str = "-",
        slugify: Optional[Callable[[str], str]] = None,
        unique_with: Optional[Union[str, List[str], Tuple[str, ...]]] = None,
        always_update: bool = False,
        allow_unicode: bool = False,
        **kwargs,
    ):
        kwargs.setdefault("max_length", 50)

        if populate_from:
            kwargs.setdefault("editable", False)

        super().__init__(**kwargs)

        self.populate_from = populate_from
        self.sep = sep
        self.slugify = slugify or django_slugify
        self.unique_with = (
            unique_with
            if isinstance(unique_with, (list, tuple))
            else (unique_with,)
            if unique_with
            else ()
        )
        self.always_update = always_update
        self.allow_unicode = allow_unicode

    def get_prepopulated_value(self, instance: models.Model) -> str:
        """
        Retrieve the value to populate the slug from the specified source.

        :param instance: The model instance being saved.
        :return: The value to use for generating the slug.
        """
        if callable(self.populate_from):
            return self.populate_from(instance)
        elif isinstance(self.populate_from, str):
            return getattr(instance, self.populate_from, "")
        return ""

    def generate_unique_slug(self, instance: models.Model, slug: str) -> str:
        """
        Generate a unique slug by appending an index if necessary.

        :param instance: The model instance being saved.
        :param slug: The base slug to make unique.
        :return: A unique slug.
        """
        model = instance.__class__
        original_slug = slug
        index = 1

        # Check for uniqueness
        while self.is_slug_exists(model, slug, instance):
            slug = f"{original_slug}{self.sep}{index}"
            index += 1

        return slug

    def is_slug_exists(
        self, model: models.Model, slug: str, instance: models.Model
    ) -> bool:
        """
        Check if the slug already exists, considering uniqueness constraints.

        :param model: The model class.
        :param slug: The slug to check.
        :param instance: The model instance being saved.
        :return: True if the slug exists, False otherwise.
        """
        queryset = model._default_manager.all()

        if instance.pk:
            queryset = queryset.exclude(pk=instance.pk)

        if self.unique:
            return queryset.filter(**{self.attname: slug}).exists()

        if self.unique_with:
            filters = {field: getattr(instance, field) for field in self.unique_with}
            filters[self.attname] = slug
            return queryset.filter(**filters).exists()

        return False

    def contribute_to_class(self, cls: type, name: str) -> None:
        """
        Add the field to the model class and connect the pre_save signal.

        :param cls: The model class.
        :param name: The name of the field.
        """
        super().contribute_to_class(cls, name)

        @receiver(pre_save, sender=cls)
        def generate_slug(sender, instance, **kwargs):
            """
            Signal handler to generate and set the slug before saving the instance.
            """
            value = getattr(instance, self.attname)

            if self.always_update or (self.populate_from and not value):
                value = self.get_prepopulated_value(instance)
                if value:
                    value = self.slugify(value)

            if value and (self.unique or self.unique_with):
                value = self.generate_unique_slug(instance, value)

            setattr(instance, self.attname, value)

    def deconstruct(self) -> tuple:
        """
        Deconstruct the field for migrations.

        :return: A tuple containing the field's name, path, args, and kwargs.
        """
        name, path, args, kwargs = super().deconstruct()

        if self.populate_from:
            kwargs["populate_from"] = self.populate_from
        if self.sep != "-":
            kwargs["sep"] = self.sep
        if self.slugify != django_slugify:
            kwargs["slugify"] = self.slugify
        if self.unique_with:
            kwargs["unique_with"] = self.unique_with
        if self.always_update:
            kwargs["always_update"] = self.always_update
        if self.allow_unicode:
            kwargs["allow_unicode"] = self.allow_unicode

        return name, path, args, kwargs