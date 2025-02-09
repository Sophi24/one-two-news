import time
import traceback

import db.manager as dbm
import tg.manager as tgm
import tg.stat_tgs as tgs
import config

# Init
dbm.DB_CONFIG = config.DB_MYSQL


def channels_update(is_fast_update:bool=False):
    # for channel_name in TELE_CHANELS:
    
    # Загрузим список каналов из БД
    for channel in dbm.channels_get(is_fast_update):
        print('>>>', channel)

        # Загрузим сообщения через веб-интерфейс телеграмм
        channel_name = channel[1]
        doc = tgm.doc_get(channel_name)

        # Обновим данные канала в БД
        channel_label = tgm.doc_chanel_parse(doc)
        print('>>> CHANNEL', channel_name, channel_label)
        channel_id = dbm.channel_ins(channel_name, channel_label)

        # Загрузим сообщения в БД
        pos_in_doc = 0
        msg_count = 0
        id_first = None

        while pos_in_doc >= 0:
            print('=================================================')
            el, pos_in_doc = tgm.doc_msg_parse(doc, pos_in_doc)
            if el and el['text'] and el['id'] and el['views'] and el['date']:
                if not id_first:
                    id_first = el['id']
                
                if 'erid' in el['text'].lower():
                    continue
                
                dbm.message_ins(channel_id, el['text'], el['id'], el['views'], el['date'])
                # print('>>> DOC TO INS')
                # print(el)
                print(channel_id, el['id'], el['views'], el['date'])
                msg_count += 1

        dbm.log_ins('UPD',f'{channel[1]} = {msg_count}')
        
        # Загрузим дополнительный блок сообщений, если выполняется экстренное обновление
        if is_fast_update and id_first:
            doc = tgm.doc_get(f'{channel_name}?before={id_first}')

            pos_in_doc = 0
            msg_count = 0

            while pos_in_doc >= 0:
                print('=================================================')
                el, pos_in_doc = tgm.doc_msg_parse(doc, pos_in_doc)
                if el and el['text'] and el['id'] and el['views'] and el['date']:                    
                    if 'erid' in el['text'].lower():
                        continue
                    
                    dbm.message_ins(channel_id, el['text'], el['id'], el['views'], el['date'])
                    # print('>>> DOC TO INS')
                    # print(el)
                    print(channel_id, el['id'], el['views'], el['date'])
                    msg_count += 1
            
            dbm.log_ins('UPD',f'{channel[1]} = {msg_count} additional')
        
        # Снимем отметку экстренного обновления
        if is_fast_update:
            dbm.channel_upd(channel_name, False)
            dbm.log_ins('UPD',f'{channel[1]} to_update = false')


def tgs_update():
    # GROUPS
    doc = tgs.doc_groups_get()
    # print(doc)
    if doc:
        # TODO: DISABLE
        # dbm.channel_tgs_clr()
        pos_in_doc = 0
        while pos_in_doc >= 0:
            el, pos_in_doc = tgs.doc_group_parse(doc, pos_in_doc)
            print(el)
            if el and not tgs.is_stop_channel(el['name']):
                # CHANNELS in GROUP
                time.sleep(30)
                doc_chn = tgs.doc_channels_get(el['name'])
                # print(doc_chn)
                if doc_chn:
                    # TODO: DEL ONLY CHANNEL
                    pos_in_doc_chn = 0
                    while pos_in_doc_chn >= 0:
                        el_ch, pos_in_doc_chn = tgs.doc_channel_parse(doc_chn, pos_in_doc_chn)
                        if el_ch:
                            print(el_ch, pos_in_doc_chn)
                            dbm.channel_tgs_ins(el_ch['name'], el_ch['label'], el_ch['subs'], el['label'])
            # exit(0)
    else:
        # TODO: Report
        pass


if __name__ == '__main__':
    sleep_cycles = 0
    
    while True:
        # Загрузка сообщений
        try:
            # Обновление всех каналов = один раз за несколько циклов
            if sleep_cycles > 10*5:
                # dbm.log_ins('UPD',f'cycle = {sleep_cycles}')
                channels_update()
                sleep_cycles = 0
            # Обновление каналов с отметкой экстренного обновления = каждый цикл
            else:
                # dbm.log_ins('UPD',f'FAST, cycle = {sleep_cycles}')
                channels_update(True)
        except Exception as ex:
            dbm.log_ins(tp='ERR-LOADER', msg=str(ex)+'\r\n'+traceback.format_exc())

        sleep_cycles += 1
        time.sleep(config.TG_MSG_SLEEP_SEC)
        
        # Обновление списка каналов из TGSTAT
        # TODO: Обновить алгоритм обновления с учётом блокировки при частых обращениях
        # tgs_sleep_cycles += 1
        # if tgs_sleep_cycles >= config.TG_STAT_CYCLES:
        #     tgs_sleep_cycles = 0
        #     tgs_update()
