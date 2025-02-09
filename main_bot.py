import time

from tg.bot import Bot
import config
import db.manager as dbm

def message_send(message_text: str) -> None:
    for chat_id in config.BOT_CHAT_IDS:
        is_ok = lm_bot.message_send(int(chat_id), message_text, False)

def monitoring():
    id_last = dbm.log_last_id_get()
    while True:
        print('check')
        recs = dbm.log_new_get(id_last)
        print(recs)
        if recs:
            for r in recs:
                print(r)
                id_last = r[0]
                msg = f'{r[2]}\r\n{r[1]} - {r[0]}\r\n{r[4]}\r\n{r[3]}'
                message_send(msg)
        
        time.sleep(10)


if __name__ == '__main__':
    dbm.DB_CONFIG = config.DB_MYSQL
    lm_bot = Bot(config.BOT_TOKEN, config.BOT_CHAT_IDS)
    
    while True:
        try:
            print('Bot monitor start')
            message_send('🚀 Bot monitor start 🚀')
            monitoring()
        except Exception as ex:
            message_send('⛔ Monitoring err:\r\n'+str(ex))
    
        time.sleep(1*60)