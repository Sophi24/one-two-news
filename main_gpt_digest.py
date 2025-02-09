import time
from datetime import datetime, timedelta
import traceback

import db.manager as dbm
# import gpt.mistral as gpt_mi
# import gpt.ya as gpt_ya
import gpt.gemini as gpt_gm
import config

# Init
dbm.DB_CONFIG = config.DB_MYSQL

# gpt_mi.MI_API = config.MI_API
# gpt_mi.MI_MODEL = config.MI_MODEL
# gpt_mi.MI_SYSTEM = config.GM_SYSTEM_DG #!

# gpt_ya.YA_OAUTH = config.YA_OAUTH
# gpt_ya.YA_FOLDER_ID = config.YA_FOLDER_ID
# gpt_ya.YA_GPT_REQUEST = config.YA_GPT_REQUEST

gpt_gm.GM_API = config.GM_API
gpt_gm.GM_MODEL = config.GM_MODEL
# gpt_gm.GM_SYSTEM = config.GM_SYSTEM
gpt_gm.GM_SYSTEM_DG = config.GM_SYSTEM_DG


def messages_rate():
    # MISTRAL
    # for dg in dbm.digest_to_do_get():
    #     # Collect messages
    #     messages = ''
    #     for msg in dbm.messages_by_date_get(dg[1], dg[2], datetime.now()-timedelta(days=1)):
    #         messages += '\n|' + msg[1]
    #     # print(messages)
    #     gpt_digest = gpt_mi.mi_rating_get('Текст новостей: \n' + messages)
    #     dbm.log_ins('GPT_MI_DG', gpt_digest[:15500] if len(gpt_digest)>15500 else gpt_digest)
    #     dbm.digest_upd(dg[0], messages, gpt_digest)        
    #     time.sleep(3)

    # YA
    # for msg in dbm.message_to_rate_get('gpt_ya_cls'):
    #     gpt_rating = gpt_ya.ya_rating_get(msg[1])
    #     dbm.log_ins('GPT_YA', f'{msg[0]} = {gpt_rating[0]} : {gpt_rating[1]}')
    #     dbm.message_rate_upd(msg[0], 'gpt_ya_cls', gpt_rating[0])
    #     time.sleep(3)
    
    # GEMINI
    for dg in dbm.digest_to_do_get():
        dbm.log_ins(tp='GPT_GM_DG', msg=f'TASK {dg[0]} START')
        # Collect messages
        messages = ''
        for msg in dbm.messages_by_date_get(dg[1], dg[2], datetime.now()-timedelta(days=1)):
            messages += '\n|' + msg[1]
        # print(messages)
        gpt_digest = gpt_gm.gm_digest_get('Текст новостей: \n' + messages)
        dbm.log_ins(tp='GPT_GM_DG', msg=f'TASK {dg[0]} COMPETED')
        dbm.log_ins('GPT_GM_DG', gpt_digest[:15500] if len(gpt_digest)>15500 else gpt_digest)
        
        dbm.digest_upd(dg[0], messages, gpt_digest)
        dbm.log_ins(tp='GPT_GM_DG', msg=f'TASK {dg[0]} SAVED')
        time.sleep(3)

if __name__ == '__main__':    
    dbm.log_ins(tp='GPT-DIGEST', msg='START')
    while True:
        try:
            messages_rate()
        except Exception as ex:
            dbm.log_ins(tp='ERR-GPT-DIGEST', msg=str(ex)+'\r\n'+traceback.format_exc())

        time.sleep(5)