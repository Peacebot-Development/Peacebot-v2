import lightbulb
from hikari import ButtonStyle
from hikari.api.special_endpoints import ActionRowBuilder


def create_source_button(
    ctx: lightbulb.context.Context, source: str
) -> ActionRowBuilder:
    button = (
        ctx.bot.rest.build_action_row()
        .add_button(ButtonStyle.LINK, source)
        .set_label("Source")
        .add_to_container()
    )

    return button
