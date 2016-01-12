import logging
import asyncio
import aiohttp

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)


class BaseBot(object):

    def __init__(self, token):
        api_url = "{}{}".format('https://api.telegram.org/bot', token)
        get_command_url = '{}/{}'.format(api_url, 'getUpdates')
        self.SEND_MESSAGE_URL = '{}/{}'.format(api_url, 'sendMessage')
        self.OFFSET_COMMAND_URL = '{}{}'.format(get_command_url, '?offset={}')

    _ALLOW_COMMANDS = {
        'test': 'test_message',  # key == command from the user, value == name of your method
        '/chat_id': 'get_chat_id'
    }

    _update_id = 0  # TODO

    @property
    def update_id(self):
        return self._update_id

    @update_id.setter
    def update_id(self, new_update_id):
        self._update_id = new_update_id

    @property
    def allow_commands(self):
        return self._ALLOW_COMMANDS

    @allow_commands.setter
    def allow_commands(self, commands):
        self._ALLOW_COMMANDS.update(commands)

    @asyncio.coroutine
    def _get_command(self, url):
        response = yield from aiohttp.request('GET', url)
        return (yield from response.read_and_close(decode=True))

    @asyncio.coroutine
    def _command_handler(self):
        while True:
            response = yield from self._get_command(self.OFFSET_COMMAND_URL.format(self.update_id + 1))
            if response['result']:
                logging.info('MESSAGE FROM {} '.format(response['result'][0]['message']['from']['first_name']))
                self.update_id = response['result'][0]['update_id']
                command, args = self._parse_command(response['result'][0]['message']['text'])
                chat_id = response['result'][0]['message']['from']['id']

                try:
                    yield from self._choose_method(chat_id, command, args)
                except Exception as e:
                    logging.error(str(e))
                    data = self.gen_data(chat_id, 'Error executing the command {}'.format(command))
                    yield from self._set_command(data)

            yield from asyncio.sleep(3)

    def _parse_command(self, text):
        if not text:
            return '', []
        cmd_list = text.split()
        return cmd_list[0], cmd_list[1:]

    @asyncio.coroutine
    def _choose_method(self, chat_id, command, args):
        if command in self.allow_commands.keys():
            method = getattr(self, self.allow_commands[command])
            yield from method(chat_id, *args)
            logging.info('COMMAND COMPLETED SUCCESSFULLY. CHAT_ID: {} '.format(chat_id))
        else:
            data = self.gen_data(chat_id, 'Command {} not found.'.format(command))
            logging.warning('COMMAND {} NOT FOUND. CHAT_ID: {} '.format(command, chat_id))
            yield from self._set_command(data)

    @asyncio.coroutine
    def _set_command(self, data):
        yield from aiohttp.request('POST', self.SEND_MESSAGE_URL, data=data)

    def gen_data(self, chat_id, text):
        return {'chat_id': chat_id, 'text': text}

    @asyncio.coroutine
    def test_message(self, chat_id):
        data = self.gen_data(chat_id, 'Test message')
        yield from self._set_command(data)

    @asyncio.coroutine
    def get_chat_id(self, chat_id):
        data = self.gen_data(chat_id, chat_id)
        yield from self._set_command(data)

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._command_handler())
        loop.close()