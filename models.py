from tortoise import fields
from tortoise.models import Model

from peacebot import bot_config


class CustomModel(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    updated_at = fields.DatetimeField(null=True, auto_now=True)

    class Meta:
        abstract = True


class GuildModel(CustomModel):
    """Defining a Guild Model to store prefix and id of the guild."""

    id = fields.BigIntField(pk=True, description="ID of the Guild")
    prefix = fields.TextField(
        default=bot_config.prefix,
        max_length=10,
        description="Custom Prefix for the guild",
    )
    mod_log_channel = fields.BigIntField(
        description="Mod Log channel for the guild!", null=True
    )

    class Meta:
        """Class to set the table name and description"""

        table = "guilds"
        table_description = "Stores information about the guild."


class AutoResponseModel(CustomModel):
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


class ModerationRoles(CustomModel):
    id = fields.IntField(pk=True)
    admin_role = fields.BigIntField(description="ID of the Admin role", null=True)
    mod_role = fields.BigIntField(description="ID of the Mod role", null=True)
    moderation_role = fields.BigIntField(
        description="ID of the General Moderation Role", null=True
    )
    guild = fields.ForeignKeyField("main.GuildModel", related_name="ModerationRoles")

    class Meta:
        table = "staff_roles"
        table_description = "Stores the roles for the moderation"
        unique = "guild"


class ModLogs(CustomModel):
    id = fields.IntField(description="ID of the Case", pk=True)
    guild = fields.ForeignKeyField("main.GuildModel", related_name="ModLogs")
    moderator = fields.TextField(description="Moderator that performed the action")
    target = fields.TextField(description="Victim of the moderation action")
    reason = fields.TextField(description="Reason of Moderation Action")
    type = fields.TextField(description="Type of Moderation action")
    timestamp = fields.DatetimeField(
        description="Timestamp of the action", auto_now=True
    )
    message = fields.TextField(description="Message Link of the action")
    channel = fields.TextField(description="Channel of action")

    class Meta:
        table = "mod_logs"
        table_description = "Stores all the moderation actions"
        unique = "guild"
