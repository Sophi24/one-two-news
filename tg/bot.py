import json
import logging

import requests


class Bot:
    def __init__(self, bot_token: str, chat_ids: list[int]):
        self._bot_token = bot_token
        self._chat_ids = chat_ids
        self._offset_last = 0

        # https://core.telegram.org/bots/api#getme
        self._url_bot_info = rf'https://api.telegram.org/bot{self._bot_token}/getMe'

        # # https://core.telegram.org/bots/api#getupdates
        self._url_update_last = rf'https://api.telegram.org/bot{self._bot_token}/getUpdates?offset=-1'
        self._url_updates_get = rf'https://api.telegram.org/bot{self._bot_token}/getUpdates?timeout=25&offset='

        # https://core.telegram.org/bots/api#sendmessage
        self._url_send_message = rf'https://api.telegram.org/bot{self._bot_token}/sendMessage'

        self._keyboard = json.dumps({'keyboard':[['/stat']],"one_time_keyboard":False,"resize_keyboard":True})

    def bot_test(self) -> bool | str:
        logging.info('Request bot info')

        try:
            resp = requests.get(url=self._url_bot_info)
            logging.debug(f'Response status: {resp.status_code}')
            if resp.status_code == 200:
                j = resp.json()
                logging.debug(f'Response body: {resp.text}')
                if ('ok' in j and j['ok']
                        and 'result' in j
                        and 'is_bot' in j['result'] and j['result']['is_bot']):
                    logging.debug(f'Bot check is OK: {j['result']['id']} - {j['result']['username']}')
                    return True
        except Exception as ex:
            logging.error(str(ex))
            return False

        return False

    def chat_id_get_last(self) -> int | None:
        logging.info('Request LAST ID')
        resp = requests.get(url=self._url_update_last)
        logging.debug(f'Response status: {resp.status_code}')
        if resp.status_code == 200:
            j = resp.json()
            logging.debug(f'Response body: {resp.text}')
            if 'ok' in j and j['ok'] and 'result' in j:
                
                if len(j['result']) > 0:
                    self._offset_last = j['result'][-1]['update_id'] + 1
                
                for r in j['result']:
                    if 'message' in r and 'from' in r['message']:
                        logging.info(f'LAST ID = {r['message']['from']['id']}')
                        return r['message']['from']['id']
        return None

    def message_send(self, msg_chat_id: int, msg_text: str, msg_is_notification: bool) -> bool:
        #logging.info('Send message')

        try:
            msg_json = {
                'text': msg_text,
                'chat_id': msg_chat_id,
                'parse_mode': 'HTML',
                'disable_notification': not msg_is_notification,
                'reply_markup': self._keyboard
            }
            #logging.debug(rf'Request data: {msg_json}')
            resp = requests.post(url=self._url_send_message, data=msg_json)
            #logging.debug(f'Response status: {resp.status_code}')
            if resp.status_code == 200:
                j = resp.json()
                #logging.debug(f'Response body: {resp.text}')
                if 'ok' in j and j['ok'] and 'result' in j:
                    #logging.info(f'Send message: {j['ok']}')
                    return True
        except Exception as ex:
            #logging.error(str(ex))
            return False

        return False
    
    def updates_get(self) -> dict | None:
        logging.info('Request last updates')
        resp = requests.get(url=self._url_updates_get + str(self._offset_last))
        logging.debug(f'Response status: {resp.status_code}')
        
        if resp.status_code == 200:
            j = resp.json()
            logging.debug(f'Response body: {resp.text}')
            
            if 'ok' in j and j['ok'] and 'result' in j and len(j['result']) > 0:
                self._offset_last = j['result'][-1]['update_id'] + 1
                return j['result']
            
        return None