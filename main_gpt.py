import time
import traceback

import db.manager as dbm
import gpt.mistral as gpt_mi
import gpt.ya as gpt_ya
import gpt.gemini as gpt_gm
import config

# Init
dbm.DB_CONFIG = config.DB_MYSQL

gpt_mi.MI_API = config.MI_API
gpt_mi.MI_MODEL = config.MI_MODEL
gpt_mi.MI_SYSTEM = config.MI_SYSTEM

gpt_ya.YA_OAUTH = config.YA_OAUTH
gpt_ya.YA_FOLDER_ID = config.YA_FOLDER_ID
gpt_ya.YA_GPT_REQUEST = config.YA_GPT_REQUEST

gpt_gm.GM_API = config.GM_API
gpt_gm.GM_MODEL = config.GM_MODEL
gpt_gm.GM_SYSTEM = config.GM_SYSTEM


def messages_rate():
    # MISTRAL
    for msg in dbm.message_to_rate_get('gpt_mistral_large'):
        gpt_rating = gpt_mi.mi_rating_get(msg[1])
        dbm.log_ins('GPT_MI', f'{msg[0]} = {gpt_rating}')
        dbm.message_rate_upd(msg[0], 'gpt_mistral_large', gpt_rating)        
        time.sleep(3)

    # YA
    # for msg in dbm.message_to_rate_get('gpt_ya_cls'):
    #     gpt_rating = gpt_ya.ya_rating_get(msg[1])
    #     dbm.log_ins('GPT_YA', f'{msg[0]} = {gpt_rating[0]} : {gpt_rating[1]}')
    #     dbm.message_rate_upd(msg[0], 'gpt_ya_cls', gpt_rating[0])
    #     time.sleep(3)
    
    # GEMINI
    # for msg in dbm.message_to_rate_get('gpt_gemini_flash'):
    #     gpt_rating = gpt_gm.gm_rating_get(msg[1])
    #     dbm.log_ins('GPT_GM', f'{msg[0]} = {gpt_rating}')
    #     dbm.message_rate_upd(msg[0], 'gpt_gemini_flash', gpt_rating)        
    #     time.sleep(3)

if __name__ == '__main__':
    while True:
        try:
            messages_rate()
        except Exception as ex:
            # dbm.log_ins(tp='ERR-GPT',msg=str(ex))
            dbm.log_ins(tp='ERR-GPT', msg=str(ex)+'\r\n'+traceback.format_exc())
        
        time.sleep(1*60)
