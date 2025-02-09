import enum
import traceback

from flask import Flask, request
from gevent import pywsgi
import logging, json
from datetime import timedelta, datetime

import db.manager as dbm
import tg.manager as tgm
import lib.helper as lbh
import config
from lib import helper

# Init
dbm.DB_CONFIG = config.DB_MYSQL
app = Flask(__name__)

# LEVELS
class MenuLevels(enum.Enum):
    unknown = 1
    error = 2
    help = 3    
    
    start = 11
    level_menu = 12
    level_menu_select = 13

    level_edit = 21
    level_edit_select = 22
    level_edit_clear = 23
    level_edit_add = 24
    level_edit_channel_get = 25
    level_edit_channel_num = 26
    
    level_chronics = 31
    level_daily = 32
    level_digest = 33


#
MSG_MENU_START = 'Привет! Это "Новости на раз-два"! \nЗдесь вы можете прочитать новости из своих любимых телеграмм каналов.'
MSG_MENU_MAIN = 'Скажите, что вы хотите услышать: "Новости дня", "Хроники", "Сводку дня" или скажите "Редактировать" для изменения списка каналов.'
MSG_HELP = '''Это навык "Новости на раз-два"!  
Я могу озвучить новости из телеграм-каналов с помощью команд "Новости дня", "Хроники" и "Сводка дня".
Редактировать список озвучиваемых телеграм-каналов можно с помощью команды "Редактировать".
Вернуться в главное меню в любой момент можно с помощью команды "Меню".
Чтобы начать, скажи "Поехали"!'''
BTNS_MENU_MAIN = [
    {'title':'Новости дня', 'hide': True},
    {'title':'Хроники', 'hide': True},
    {'title':'Сводка дня', 'hide': True},
    {'title':'Редактировать', 'hide': True}
]



MSG_CHANNEL_INPUT = 'Отправьте ссылку на телеграм-канал или скажите его название для поиска в каталоге популярных каналов.'
MSG_NO_CHANNELS = f'У вас пока нет сохраненных каналов. Давайте добавим их в список. \n{MSG_CHANNEL_INPUT}'

MSG_LEVEL_EDIT_MENU = 'Вы хотите "Добавить" канал, "Очистить" список каналов или "Вернуться" в главное меню?'
BTNS_LEVEL_EDIT_MENU = [
    {'title':'Добавить', 'hide': True},
    {'title':'Очистить', 'hide': True},
    {'title':'Меню', 'hide': True}
]

MSG_LEVEL_EDIT_MENU_10 = 'У вас уже 10 каналов. Вы хотите "Очистить" список каналов или "Вернуться" в главное меню?'
BTNS_LEVEL_EDIT_MENU_10 = [
    {'title':'Очистить', 'hide': True},
    {'title':'Меню', 'hide': True}
]

MSG_LEVEL_READING_MENU = 'Скажите "Далее", "Повторить" или "Меню"'
BTNS_LEVEL_READING = [
    {'title':'Далее', 'hide': True},
    {'title':'Повторить', 'hide': True},
    {'title':'Меню', 'hide': True}
]



@app.route('/')
def hello_world():
    return "<p>Hello, World!</p>"

# TODO: Long route path
@app.route('/post', methods=['POST'])
def main():
    req = request.json
    ya_user_id = req['session']['user_id']

    # Фиксируем начало обращения для дальнейшего анализа скорости ответов
    dbm.log_ins(tp='REQ',msg=str(req), user_id=ya_user_id)

    # Найдем ID пользователя
    db_user_id = dbm.user_get(ya_user_id=ya_user_id)
    if not db_user_id:
        db_user_id = dbm.user_ins(ya_user_id)
    else:
        db_user_id = db_user_id[0]
        dbm.user_dt_last_upd(db_user_id)

    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        },
        'session_state': {}
    }

    try:
        handle_dialog(request.json, response, db_user_id)
    except Exception as ex:
        # Если произошла ошибка при формировании ответа, то попросим пользователя начать работу заново из главного меню
        dbm.log_ins(tp='ERR-FLASK', msg=str(ex)+'\r\n'+traceback.format_exc(), user_id=ya_user_id)         
        response['session_state']['user_state'] = MenuLevels.level_menu.value
        response['response']['text'] = 'К сожалению произошла ошибка в работе навыка. Мы уже работаем над устранением проблемы. А пока давайте вернемся в "Меню".'
        response['response']['buttons'] = [{'title':'Меню', 'hide': True}]

    # Фиксируем конец обращения для дальнейшего анализа скорости ответов
    dbm.log_ins(tp='RESP',msg=str(json.dumps(response)), user_id=ya_user_id)
    return json.dumps(response)


def handle_dialog(req:dict, res:dict, db_user_id:int) -> None:
    #########################################################################################
    # СОБЕРЕМ ДАННЫЕ ДЛЯ ОБРАБОТКИ СООБЩЕНИЯ ПОЛЬЗОВАТЕЛЯ
    #########################################################################################

    # Идентификатор пользователя
    if 'user' in req['session']:
        user_id = req['session']['user']['user_id']
    else:
        user_id = req['session']['application']['application_id']

    # Сообщение пользователя
    if 'original_utterance' in req['request']:
        user_input = req['request']['original_utterance'].lower().strip()
    else:
        user_input = None

    # Команда пользователя (используется при поиске канала по номеру)
    if 'command' in req['request']:
        user_command = req['request']['command']
    else:
        user_command = None
        
    # Формирование ответа пользователю
    user_output = 'ОшибкА'
    user_output_tts = None
    user_buttons = []

    # Опеределение ветки диалога
    user_state = MenuLevels.unknown
    user_req = MenuLevels.unknown
    
    # Дополнительные переменные
    is_rep = False

    # Дополнительные переменные для сохранения состояния диалога между запросами
    ch_list = []
    user_msg_last_id = None
    user_msg_first_id = None
    user_digest_id = None
    user_digest_pos = None
    
    # Восстанавливаем значения переменных из "сессии" (объект, который передаётся между запросами пользователя)
    if 'state' in req and 'session' in req['state']:
        if 'user_state' in req['state']['session']:
            user_state = MenuLevels(int(req['state']['session']['user_state']))
        if 'channels_list' in req['state']['session']:
            ch_list = req['state']['session']['channels_list']
        if 'msg_last_id' in req['state']['session']:
            user_msg_last_id = int(req['state']['session']['msg_last_id'])
        if 'msg_first_id' in req['state']['session']:
            user_msg_first_id = int(req['state']['session']['msg_first_id'])
        if 'digest_id' in req['state']['session']:
            user_digest_id = int(req['state']['session']['digest_id'])
        if 'digest_pos' in req['state']['session']:
            user_digest_pos = int(req['state']['session']['digest_pos'])

    msg_log = f'USER_STATE: {user_state}\nUSER_INPUT: {user_input}\nuser_msg_last_id: {user_msg_last_id}\nuser_msg_first_id: {user_msg_first_id}\nuser_digest_id: {user_digest_id}\nuser_digest_pos: {user_digest_pos}'
    print('#####################')
    print('>>> REQUEST')
    print(f'>>> USER_STATE: {user_state}')
    print(f'>>> USER_INPUT: {user_input}')


    #########################################################################################
    # ОПРЕДЕЛИМ ВЕТКУ ДИАЛОГА
    #########################################################################################
    if req['session']['new']:
        user_state = MenuLevels.start
        user_req = MenuLevels.level_menu

    # Обработка названия канала выполняется в первую очередь, т.к. название может содержать ключевые слова (помощь, меню и т.п.)
    elif user_state == MenuLevels.level_edit_channel_get:
        user_req = MenuLevels.level_edit_channel_get
    
    elif 'помощь' in user_input or 'что ты умеешь' in user_input:
        user_req = MenuLevels.help
    
    # =======================================================================================
    # Главное меню
    # =======================================================================================
    
    elif 'меню' in user_input or 'главн' in user_input or 'верну' in user_input:
        user_req = MenuLevels.level_menu

    elif user_state == MenuLevels.level_menu:
        user_req = MenuLevels.level_menu

    elif user_state == MenuLevels.level_menu_select:
        if 'новос' in user_input and ('ден' in user_input or 'дня' in user_input):
            user_req = MenuLevels.level_daily
        elif 'хроник' in user_input:
            user_req = MenuLevels.level_chronics
        elif 'сводк' in user_input:
            user_req = MenuLevels.level_digest
        elif 'редакт' in user_input:
            user_req = MenuLevels.level_edit
        else:
            user_req = MenuLevels.error
            
    # =======================================================================================
    # Редактирование списка каналов
    # =======================================================================================

    elif user_state == MenuLevels.level_edit_select:
        channels_list = dbm.user_channels_get(db_user_id)
        if 'добави' in user_input:
            user_req = MenuLevels.level_edit_add
        elif 'очист' in user_input and channels_list:
            user_req = MenuLevels.level_edit_clear
        else:
            user_req = MenuLevels.error

    elif user_state==MenuLevels.level_edit_channel_num:
        user_req = MenuLevels.level_edit_channel_num

    # =======================================================================================
    # Чтение
    # =======================================================================================

    elif user_state == MenuLevels.level_daily:
        if 'далее' in user_input:
            user_req = MenuLevels.level_daily
        elif 'снова' in user_input or 'повтор' in user_input:
            user_req = MenuLevels.level_daily
            is_rep = True
        else:
            user_req = MenuLevels.error

    elif user_state == MenuLevels.level_chronics:
        if 'далее' in user_input:
            user_req = MenuLevels.level_chronics
        elif 'снова' in user_input or 'повтор' in user_input:
            user_req = MenuLevels.level_chronics
            is_rep = True
        else:
            user_req = MenuLevels.error

    elif user_state == MenuLevels.level_digest:
        if 'далее' in user_input or 'продолж' in user_input:
            user_req = MenuLevels.level_digest
        else:
            user_req = MenuLevels.error

    msg_log += f'\nUSER_REQ: {user_req}'
    print(f'>>> USER_REQ: {user_req}')
    dbm.log_ins('PROC', msg_log, user_id)
    
    #########################################################################################
    # ВЫПОЛНИМ КОД ДЛЯ ВЕТКИ ДИАЛОГА
    #########################################################################################
    
    match(user_req):
        
        case MenuLevels.error:
            user_output = 'Некорректный ввод. Давайте вернемся в "Меню".'
            user_buttons.append({'title':'Меню', 'hide': True})
            user_state = MenuLevels.level_menu

        case MenuLevels.help:
            user_output = MSG_HELP
            user_buttons.append({'title':'Поехали', 'hide': True})
            user_state = MenuLevels.level_menu


        # =======================================================================================
        # Главное меню
        # =======================================================================================
        
        case MenuLevels.level_menu:
            channels_list = dbm.user_channels_get(db_user_id)
            if channels_list:
                user_output = (f'{MSG_MENU_START} \n' if user_state==MenuLevels.start else '') + f'{MSG_MENU_MAIN}'
                user_buttons = BTNS_MENU_MAIN
                user_state = MenuLevels.level_menu_select
            elif not channels_list:
                user_output = (f'{MSG_MENU_START} \n' if user_state==MenuLevels.start else '') + f'{MSG_NO_CHANNELS}'
                user_state = MenuLevels.level_edit_channel_get
                 
        # =======================================================================================
        # Редактирование списка каналов
        # =======================================================================================

        case MenuLevels.level_edit:
            channels_list =  [x[2] for x in dbm.user_channels_get(db_user_id)]
            if channels_list:
                if len(channels_list) >9:
                    user_output = 'Ваш список каналов: \n' + ', \n'.join([str(x) for x in channels_list]) + f'. \n\n{MSG_LEVEL_EDIT_MENU_10}'
                    user_buttons = BTNS_LEVEL_EDIT_MENU_10
                else:
                    user_output = 'Ваш список каналов: \n' + ', \n'.join([str(x) for x in channels_list]) + f'. \n\n{MSG_LEVEL_EDIT_MENU}'
                    user_buttons = BTNS_LEVEL_EDIT_MENU
                user_state = MenuLevels.level_edit_select
            else:
                user_output = f'{MSG_NO_CHANNELS}'
                user_state = MenuLevels.level_edit_channel_get

        # =======================================================================================
        case MenuLevels.level_edit_add:
            channels_list = dbm.user_channels_get(db_user_id)
            if len(channels_list)<10:
                user_output = f'{MSG_CHANNEL_INPUT}'
                user_state = MenuLevels.level_edit_channel_get
            else:
                channels_list =  [x[2] for x in dbm.user_channels_get(db_user_id)]
                user_output = 'Ваш список каналов: \n' + ', \n'.join([str(x) for x in channels_list]) + f'. \n\n{MSG_LEVEL_EDIT_MENU_10}'
                user_buttons = BTNS_LEVEL_EDIT_MENU_10
                user_state = MenuLevels.level_edit_select

        # =======================================================================================
        case MenuLevels.level_edit_clear:
            dbm.user_channels_del(db_user_id)
            user_output = f'Список каналов очищен. \n\n{MSG_NO_CHANNELS}'
            user_state = MenuLevels.level_edit_channel_get

        # =======================================================================================
        case MenuLevels.level_edit_channel_get:
            # Проверка на наличие ссылки на канал
            prefix = 'https://t.me/' # https://t.me/skillboxru
            ind = user_input.find(prefix)
            
            # >>> Если введена ссылка
            if ind >= 0:
                channel_name = user_input[ind+len(prefix):]
                channel_name = channel_name.split()[0]
                # Проверка доступности канала
                doc = tgm.doc_get(channel_name)
                channel_label = tgm.doc_chanel_parse(doc)
                
                # По ссылке нет канала
                if 'Telegram: Contact @' in channel_label or '<title>Telegram: Contact @' in doc or 'Join group chat' in channel_label:
                    channels_list =  [x[2] for x in dbm.user_channels_get(db_user_id)]
                    if channels_list:
                        user_output = f'Не удалось найти канал по предоставленной ссылке! \n\nВаш список каналов: \n ' + ', \n'.join([str(x) for x in channels_list]) + f'. \n\n{MSG_LEVEL_EDIT_MENU}'
                        user_buttons = BTNS_LEVEL_EDIT_MENU
                        user_state = MenuLevels.level_edit_select
                    else:
                        user_output = f'Не удалось найти канал по предоставленной ссылке! \n\n{MSG_NO_CHANNELS}'
                        user_state = MenuLevels.level_edit_channel_get
                # По ссылке есть канал
                else:
                    channel_id = dbm.channel_ins(channel_name, channel_label)
                    dbm.user_channels_ins(db_user_id, channel_id)
                    channels_list =  [x[2] for x in dbm.user_channels_get(db_user_id)]
                    if len(channels_list) >9:
                        user_output = f'Канал "{channel_label}" успешно добавлен. \nВаш список каналов: \n ' + ', \n'.join([str(x) for x in channels_list]) + f'. \n\n{MSG_LEVEL_EDIT_MENU_10}'
                        user_buttons = BTNS_LEVEL_EDIT_MENU_10
                    else:
                        user_output = f'Канал "{channel_label}" успешно добавлен. \nВаш список каналов: \n ' + ', \n'.join([str(x) for x in channels_list]) + f'. \n\n{MSG_LEVEL_EDIT_MENU}'
                        user_buttons = BTNS_LEVEL_EDIT_MENU
                    user_state = MenuLevels.level_edit_select
            
            # >>> Если введено слово, ищем в списке популярных каналов
            else:
                recs = dbm.channel_tgs_get()
                recs = lbh.channels_find(recs, user_input)
                user_output = 'Скажите номер найденного канала: \n'
                # TODO: Найден только один канал
                if len(recs)>0:
                    for idx, r in enumerate(recs):
                        user_output += f'{idx+1} - {r[2]} \n'
                        user_buttons.append({'title':idx+1, 'hide': True})
                    user_output += '\nЕсли среди данных каналов нет подходящего, то скажите Нет.'
                    user_buttons.append({'title':'Нет', 'hide': True})
                    user_state = MenuLevels.level_edit_channel_num
                    res['session_state']['channels_list'] = recs
                else:
                    channels_list = dbm.user_channels_get(db_user_id)
                    if channels_list:
                        user_output = f'Не найден канал. \n\n{MSG_LEVEL_EDIT_MENU}'
                        user_buttons = BTNS_LEVEL_EDIT_MENU
                        user_state = MenuLevels.level_edit_select
                    else:
                        user_output = f'Не найден канал. \n\n{MSG_NO_CHANNELS}'
                        user_state = MenuLevels.level_edit_channel_get
                
        # =======================================================================================
        case MenuLevels.level_edit_channel_num:
            # Если ответ цифрой
            if user_command and str(user_command).isdigit():
                user_command = int(user_command)
                if user_command<=len(ch_list):
                    channel_name = ch_list[user_command-1][1]
                    channel_label = ch_list[user_command-1][2]
                    channel_id = dbm.channel_ins(channel_name, channel_label)
                    dbm.user_channels_ins(db_user_id, channel_id) 
                    channels_list =  [x[2] for x in dbm.user_channels_get(db_user_id)]
                    if len(channels_list) >9:
                        user_output = f'Канал "{channel_label}" успешно добавлен. \nВаш список каналов: \n' + ', \n'.join([str(x) for x in channels_list]) + f'. \n\n{MSG_LEVEL_EDIT_MENU_10}'
                        user_buttons = BTNS_LEVEL_EDIT_MENU_10
                    else:
                        user_output = f'Канал "{channel_label}" успешно добавлен. \nВаш список каналов: \n' + ', \n'.join([str(x) for x in channels_list]) + f'. \n\n{MSG_LEVEL_EDIT_MENU}'
                        user_buttons = BTNS_LEVEL_EDIT_MENU
                    user_state = MenuLevels.level_edit_select
            # Если любой другой ответ
            else:
                channels_list = dbm.user_channels_get(db_user_id)
                if channels_list:
                    user_output = f'Не выбран канал. \n\n{MSG_LEVEL_EDIT_MENU}'
                    user_buttons = BTNS_LEVEL_EDIT_MENU
                    user_state = MenuLevels.level_edit_select
                else:
                    user_output = f'Не выбран канал. \n\n{MSG_NO_CHANNELS}'
                    user_state = MenuLevels.level_edit_channel_get


        # =======================================================================================
        # Чтение
        # =======================================================================================

        case MenuLevels.level_chronics:
            msg = dbm.message_last_get(db_user_id, (user_msg_last_id + 1 if is_rep else user_msg_last_id))
            
            if not msg:
                user_output = f'Новостей больше нет. {MSG_MENU_MAIN}'
                user_buttons = BTNS_MENU_MAIN
                user_state = MenuLevels.level_menu_select
            
            else:            
                res['session_state']['msg_last_id'] = msg[0]
                txt = msg[2]
                # TODO: Сокрашение текста через нейронку
                txt = helper.text_reformat(txt)
                if len(txt) > 900:
                    txt = txt[0:900]
                user_output = f'{txt} \n\nПолучено из канала {msg[3]}. \n\n{MSG_LEVEL_READING_MENU}'
                user_output_tts = f'{txt}. sil <[500]> Получено из канала {msg[3]}. sil <[1500]> \n\n{MSG_LEVEL_READING_MENU}'
                user_buttons = BTNS_LEVEL_READING
                user_state = MenuLevels.level_chronics

        # =======================================================================================
        case MenuLevels.level_daily:
            if user_msg_first_id:
                msg = dbm.message_first_get(db_user_id, msg_first_id=(user_msg_first_id - 1 if is_rep else user_msg_first_id))
            else:                
                msg = dbm.message_first_get(db_user_id, msg_dt=datetime.today() - timedelta(hours=24))
            
            if not msg:
                user_output = f'Новостей за сегодня больше нет. {MSG_MENU_MAIN}'
                user_buttons = BTNS_MENU_MAIN
                user_state = MenuLevels.level_menu_select
                
            else:
                res['session_state']['msg_first_id'] = msg[0]
                txt = msg[2]
                # TODO: Сокрашение текста через нейронку
                txt = helper.text_reformat(txt)
                if len(txt) > 900:
                    txt = txt[0:900]                
                user_output = f'{txt} \n\nПолучено из канала {msg[3]}. \n\n{MSG_LEVEL_READING_MENU}'
                user_output_tts = f'{txt}. sil <[500]> Получено из канала {msg[3]}. sil <[1500]> \n\n{MSG_LEVEL_READING_MENU}'
                user_buttons = BTNS_LEVEL_READING
                user_state = MenuLevels.level_daily

        # =======================================================================================
        case MenuLevels.level_digest:
            # Если продолжается чтение
            if user_digest_id and user_digest_pos:
                # Продолжаем читать
                msg = dbm.user_digest_get(user_digest_id)
                msg_list = helper.digest_to_list(msg[1])
                
                digest_txt = helper.text_reformat(msg_list[user_digest_pos])
                if len(digest_txt)>900:
                    digest_txt = digest_txt[:900]

                user_digest_pos = user_digest_pos + 1
                user_output = digest_txt
                
                if user_digest_pos < len(msg_list):
                    user_output+='\n Скажите "Далее".'
                    user_buttons.append({'title':'Далее', 'hide': True})
                    res['session_state']['digest_pos'] = user_digest_pos
                    res['session_state']['digest_id'] = user_digest_id
                    user_state = MenuLevels.level_digest
                else:
                    user_output+=f' \nБольше новостей нет. \n\n{MSG_MENU_MAIN}'
                    user_buttons = BTNS_MENU_MAIN
                    user_state = MenuLevels.level_menu_select
            # Если первое обращение
            else:
                msg = dbm.user_digest_ins(db_user_id, 0)
                if msg[1]:
                    # Вернем ранее сформированный дайджест с позиции
                    msg_list = helper.digest_to_list(msg[1])

                    if len(msg_list) == 0:
                        user_output = f'К сожалению новостей нет. \n\n{MSG_MENU_MAIN}'
                        user_buttons = BTNS_MENU_MAIN
                        user_state = MenuLevels.level_menu_select
                    else:
                        digest_txt = helper.text_reformat(msg_list[0])
                        if len(digest_txt)>900:
                            digest_txt = digest_txt[:900]
                        
                        user_digest_pos = 1
                        user_output = digest_txt
                        
                        if user_digest_pos < len(msg_list):
                            user_output+='\n Скажите "Далее".'
                            user_buttons.append({'title':'Далее', 'hide': True})
                            res['session_state']['digest_pos'] = user_digest_pos
                            res['session_state']['digest_id'] = msg[0]
                            user_state = MenuLevels.level_digest
                        else:
                            user_output+=f' \nБольше новостей нет. \n\n{MSG_MENU_MAIN}'
                            user_buttons = BTNS_MENU_MAIN
                            user_state = MenuLevels.level_menu_select
                else:
                    if not user_digest_id:
                        # Запустим создание нового дайджеста
                        user_output = 'Выполнение запроса займёт некоторое время. Через несколько секунд скажите "Продолжить". А пока мы включим музыку.'
                        user_output_tts = 'Выполнение запроса займёт некоторое время. Через несколько секунд скажите "Продолжить". А пока мы включим музыку. <speaker audio="alice-music-drum-loop-2.opus">'
                        user_buttons.append({'title':'Продолжить', 'hide': True})
                        res['session_state']['digest_id'] = msg[0]
                        user_state = MenuLevels.level_digest
                    else:
                        # Пока нет текста дайджеста, ждём
                        user_output = 'Запрос ещё обрабатывается. Через несколько секунд скажите "Продолжить". А пока мы включим музыку.'
                        user_output_tts = 'Запрос ещё обрабатывается. Через несколько секунд скажите "Продолжить". А пока мы включим музыку. <speaker audio="alice-music-drum-loop-2.opus">'
                        user_buttons.append({'title':'Продолжить', 'hide': True})
                        res['session_state']['digest_id'] = user_digest_id
                        user_state = MenuLevels.level_digest

        # =======================================================================================
        case _:
            user_output = 'ОШИБКА: Не найдена ветка диалога! Давайте вернемся в "Меню".'
            user_buttons.append({'title':'Меню', 'hide': True})
            user_state = MenuLevels.level_menu


    #########################################################################################
    # ФОРМИРУЕМ ОТВЕТ ПОЛЬЗОВАТЕЛЮ
    #########################################################################################

    # Проверка длины ответа
    if len(user_output)>1000:
        user_output = user_output[:1000]

    if user_output_tts and len(user_output_tts)>1000:
        user_output_tts = user_output_tts[:1000]

    # Ответ пользователю
    res['session_state']['user_state'] = user_state.value
    res['response']['text'] = f'{user_output}'
    res['response']['tts'] = user_output_tts if user_output_tts else user_output
    res['response']['buttons'] = user_buttons

    print('#####################')
    print('>>> REPOSNE')
    print(res['response']['text'])
    for b in res['response']['buttons']:
        print(' ', b)
    print('#####################')
    