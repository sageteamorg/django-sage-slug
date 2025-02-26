from typing import Any, Union

from django.conf import settings


class SageSlugConfig:
    """A configuration handler.

    allowing dynamic settings loading from the Django settings, with
    default fallbacks.

    """
    CONFIG_PREFIX = "SAGESLUG_"

    def __init__(self) -> None:
        self.debug = self.get_setting(f"{self.CONFIG_PREFIX}TYPE_MAPPING", {
        'product_slug': 'product',
        'category_slug': 'category',
        'post_slug': 'post',
    })
        
    
    def get_setting(self, setting_name: str, default_value: Any) -> Union[str, bool]:
        """Retrieve a setting from Django settings with a default fallback."""
        return getattr(settings, setting_name, default_value)


# Create a global config object
sageslug_config = SageSlugConfig()