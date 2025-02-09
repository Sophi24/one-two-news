import requests
from datetime import datetime, timezone
import html

TELE_URL = 'https://t.me/s/'
TELE_URL_BEFORE = '?before='

TELE_CHANEL_NAME_START = '<meta property="og:title" content="'
TELE_CHANEL_NAME_FIN = '">'

TELE_MSG_SIZE = 2000

TELE_ELEMENT_START = '<div class="tgme_widget_message_wrap js-widget_message_wrap">'
TELE_ELEMENT_FIN = 'tgme_widget_message_footer'

TELE_MSG_MARKER_START = '<div class="tgme_widget_message_text js-message_text" dir="auto">'
TELE_MSG_MARKER_FIN = '</div>'

TELE_META_MARKER_START = '<div class="tgme_widget_message_info short js-message_info">'
TELE_META_MARKER_FIN = '</div>'
TELE_META_VIEWS_START = '<span class="tgme_widget_message_views">'
TELE_META_VIEWS_FIN = '</span>'
TELE_META_ID_START = '<a class="tgme_widget_message_date" href="https://t.me/'
TELE_META_ID_FIN = '">'
TELE_META_DATE_START = '<time datetime="'
TELE_META_DATE_FIN = '"'

HTML_TAGS = [
    ['<a', '</a>'],
    ['<i', '</i>'],
    ['<tg-emoji', '</tg-emoji>'],
    ['<', '>']
]

HTML_SYMBOLS = [
    ['.&nbsp;', ' '],
    ['&quot;', '"']
]


def doc_get(channel_name: str) -> str | None:
    resp = requests.get(url=TELE_URL + channel_name)
    if resp.status_code == 200:
        return resp.text
    return None


def doc_before_get(channel_name: str, before_id: int) -> str | None:
    resp = requests.get(url=TELE_URL + channel_name + TELE_URL_BEFORE + str(before_id))
    if resp.status_code == 200:
        return resp.text
    return None


def doc_chanel_parse(txt: str, pos_last: int = 0) -> str | None:
    # CHANEL INFO
    # Извлекаем название канала
    res_chanel_name, _ = data_extract(txt, TELE_CHANEL_NAME_START, TELE_CHANEL_NAME_FIN, pos_last)
    return res_chanel_name


def doc_msg_parse(txt: str, pos_last: int = 0) -> list[dict | None, int]:
    # MSG
    # Извлекаем текст сообщения
    res_msg, pos_last = data_extract(txt, TELE_MSG_MARKER_START, TELE_MSG_MARKER_FIN, pos_last)

    # Если нет текста, значит закончили чтение документы
    if not res_msg:
        return None, -1

    # Обрезаем текст сообщения (уточнить, под размер токенов нейросети)
    if len(res_msg) > TELE_MSG_SIZE:
        res_msg = res_msg[:TELE_MSG_SIZE]

    # Очистка тела сообщения. Оставляем только текст.
    res_msg = html_remove(res_msg)
    print(res_msg)

    # META
    # Извлекаем метаданные

    # Число просмотров
    res_views, pos_last = data_extract(txt, TELE_META_VIEWS_START, TELE_META_VIEWS_FIN, pos_last)
    if res_views:
        res_views = int(res_views.replace('K', '00').replace('M', '00.000').replace('.', ''))
    
    #  ID сообщения
    res_id, pos_last = data_extract(txt, TELE_META_ID_START, TELE_META_ID_FIN, pos_last)
    if res_id:
        res_id = int(res_id.split('/')[1])

    # Дата сообщения
    res_date, pos_last = data_extract(txt, TELE_META_DATE_START, TELE_META_DATE_FIN, pos_last)
    if res_date:
        res_date = datetime.fromisoformat(res_date)

    # Признак редактирования -  edited

    msg = {
        'text': res_msg,
        'views': res_views,
        'id': res_id,
        'date': res_date
    }

    return msg, pos_last


def data_extract(txt: str, tag_start: str, tag_fin: str, pos_last: int = 0) -> list[str | None, int]:
    p1 = txt.find(tag_start, pos_last)
    if p1 < 0:
        return None, pos_last
    p2 = txt.find(tag_fin, p1 + len(tag_start))
    if p2 < 0:
        return None, pos_last
    return txt[p1 + len(tag_start): p2], p2 + len(tag_fin)


def tag_remove(txt: str, tag_start: str, tag_fin: str) -> str:
    while True:
        p1 = txt.find(tag_start)
        if p1 < 0:
            break
        p2 = txt.find(tag_fin, p1)
        if p2 < 0:
            break
        txt = txt.replace(txt[p1: p2] + tag_fin, '')
    return txt


def html_remove(txt: str) -> str:
    for tag in HTML_TAGS:
        txt = tag_remove(txt, tag[0], tag[1])
    for tag in HTML_SYMBOLS:
        txt = txt.replace(tag[0], tag[1])
    txt = html.unescape(txt)    
    return txt
