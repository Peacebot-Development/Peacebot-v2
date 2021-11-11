from tortoise import fields
from tortoise.models import Model

from peacebot import bot_config


class GuildModel(Model):
    """Defining a Guild Model to store prefix and id of the guild."""

    id = fields.BigIntField(pk=True, description="ID of the Guild")
    prefix = fields.TextField(
        default=bot_config.prefix,
        max_length=10,
        description="Custom Prefix for the guild",
    )

    class Meta:
        """Class to set the table name and description"""

        table = "guilds"
        table_description = "Stores information about the guild."
