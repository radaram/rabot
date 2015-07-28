import asyncio

from base_bot import BaseBot

class CustomBot(BaseBot):

    COMMANDS = {
        'hello': 'hello'
    }

    def __init__(self):
        self.allow_commands = self.COMMANDS

    @asyncio.coroutine
    def hello(self, chat_id):
        data = self.gen_data(chat_id, 'Hello!.')
        yield from self._set_command(data)


if __name__ == '__main__':
    CustomBot().run()
