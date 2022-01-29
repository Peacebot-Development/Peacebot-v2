import os

from peacebot.core.bot import Peacebot

bot = Peacebot()

# if os.name != "nt":
#     import uvloop

#     uvloop.install()

if __name__ == "__main__":
    bot.run()
