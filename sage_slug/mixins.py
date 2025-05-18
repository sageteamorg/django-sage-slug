from django.db import models
from django.utils.text import slugify
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from .models import SAGESlugField, SlugSwap
from typing import Optional, Any, Type

class SageSlugSwapMixin(models.Model):
    """
    A mixin class that adds a title and slug field to a model.

    The `SageSlugSwapMixin` provides a standardized way to include title and slug fields in
    various models. It includes a `title` field, which is a CharField with a maximum
    length of 255 characters and is unique across the model it's used in. The `slug`
    field is a SAGESlugField used for URL-friendly representations of the `title`, also
    unique and limited to 255 characters.
    """
    title = models.CharField(
        _("Title"),
        max_length=255,
        unique=True,
        help_text=_("Enter a unique title."),
        db_comment="Stores the unique title of the instance.",
    )

    slug = SAGESlugField(
        verbose_name=_("Slug"),
        max_length=255,
        unique=True,
        editable=False,
        allow_unicode=True,
        help_text=_(
            "Slug is a newspaper term. A short label for "
            "something containing only letters, numbers, underscores, "
            "or hyphens. They are generally used in URLs."
        ),
        db_comment="Stores the URL-friendly slug derived from the title. Used for SEO-friendly URLs and routing.",
    )

    @admin.display(description=_("title"), ordering=("-title"))
    def get_title(self) -> str:
        """
        Returns the title of the instance, shortened to 30 characters if necessary.

        This method is used to display a shortened version of the title in the Django
        admin interface if the title is longer than 30 characters. It appends ellipses
        to indicate that the title has been truncated.

        Returns:
            str: The full title if it's less than 30 characters, otherwise the first 30
            characters followed by '...'.
        """
        TRUNCATE_SIZE = 30
        return (
            self.title if len(self.title) < TRUNCATE_SIZE else (self.title[:30] + "...")
        )


    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override of the model save method to handle slug generation and tracking.

        This method:
        1. Generates a new unique slug
        2. Checks if the slug has changed
        3. Saves the model with the new slug
        4. If the slug changed, handles the slug swap logic

        Args:
            *args: Variable length argument list for the save method
            **kwargs: Arbitrary keyword arguments for the save method

        Returns:
            None
        """
        new_slug = self.__generate_unique_slug()
        old_slug = self.slug
        slug_changed = self.__check_slug_changed(new_slug)

        self.slug = new_slug
        super().save(*args, **kwargs)

        if slug_changed:
            self.__handle_slug_swap_logic(old_slug, new_slug)


    def get_slug_source_field(self) -> str:
        """
        Get the field value to be used as the source for slug generation.

        This method can be overridden in child classes to use a different field
        as the source for the slug. By default, it uses 'title'.

        Returns:
            str: The value to be used for generating the slug
        """
        return getattr(self, 'title')

    def __generate_new_slug_base(self) -> str:
        """
        Generate the base slug from the source field.

        This method creates the initial slug from the source field value
        using Django's slugify function.

        Returns:
            str: The base slug before uniqueness checking
        """
        return slugify(self.get_slug_source_field(), allow_unicode=True)

    def __check_slug_changed(self, new_slug: str) -> bool:
        """
        Check if the slug has changed from its previous value.

        Args:
            new_slug (str): The newly generated slug to compare against

        Returns:
            bool: True if the slug has changed, False otherwise
        """
        pk = getattr(self, 'pk', None)
        if not pk:
            return False
        try:
            old_instance = type(self).objects.get(pk=pk)
            return old_instance.slug != new_slug
        except type(self).DoesNotExist:
            return False

    def __generate_unique_slug(self) -> str:
        """
        Generate a unique slug for the model instance.

        This method:
        1. Generates a base slug
        2. Checks if it's unique
        3. If not unique, appends a number and increments until finding a unique slug

        Returns:
            str: A unique slug for the model instance
        """
        new_slug_base = self.__generate_new_slug_base()
        new_slug = new_slug_base
        unique = False
        counter = 1
        while not unique:
            if type(self).objects.filter(slug=new_slug).exclude(pk=self.pk).exists():
                new_slug = f"{new_slug_base}-{counter}"
                counter += 1
            else:
                unique = True
        return new_slug

    def __handle_slug_swap_logic(self, old_slug: str, new_slug: str) -> None:
        """
        Handle the creation or update of slug swap records.

        This method creates or updates a SlugSwap record to track changes
        in slugs, which can be used for maintaining URL history and redirects.

        Args:
            old_slug (str): The previous slug value
            new_slug (str): The new slug value

        Returns:
            None
        """
        pk = getattr(self, 'pk', None)
        if pk:
            SlugSwap.objects.update_or_create(
                old_slug=old_slug,
                defaults={
                    'new_slug': new_slug,
                    'content_type': ContentType.objects.get_for_model(self),
                    'object_id': pk
                }
            )

    def get_absolute_url(self) -> str:
        """
        Get the absolute URL for this instance.

        This method should be overridden in child classes to define
        the proper URL pattern for the model.

        Returns:
            str: The absolute URL for this instance

        Raises:
            NotImplementedError: If the child class doesn't implement this method
        """
        raise NotImplementedError(
            f"Please implement get_absolute_url() for {self.__class__.__name__}"
        )

    class Meta:
        """The Meta class of the TitleSlugMixin has an attribute abstract = True,
        making it an abstract class and the fields defined in it will be used in the
        child classes. The Meta class does not have any other attributes.
        """
        abstract = True