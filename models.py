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


class AutoResponseModel(Model):
    """Defining a Autoresponse Model to store autoresponses for each guild"""

    id = fields.UUIDField(pk=True)
    trigger = fields.TextField(description="Trigger for the autoresponse")
    response = fields.TextField(
        description="Response to be sent after being triggered from the trigger",
    )
    enabled = fields.BooleanField(
        default=True, description="Boolean to show of the trigger is enabled"
    )
    allowed_channel = fields.BigIntField(
        default=None,
        null=True,
        description="The only channel where the autoresponse is allowed to run",
    )
    extra_text = fields.BooleanField(
        default=False,
        description="If the autoresponse should be run even when extra text is passed",
    )
    guild = fields.ForeignKeyField("main.GuildModel", related_name="Autoresponses")
    created_by = fields.BigIntField(
        description="ID of the user who created the autoresponse",
    )
    mentions = fields.BooleanField(
        default=False,
        description="If the autoresponse should mention the user/ role/ everyone",
    )

    class Meta:
        table = "autoresponses"
        table_description = "Represents the autoresponses for each GuildModel"
        unique_together = (("guild", "trigger"),)
