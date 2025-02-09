# import requests
import cloudscraper

# HEADERS = {
#     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#     'Accept-Encoding': 'gzip, deflate, br',
#     'Accept-Language': 'ru',
#     # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'
#     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15',
#     'sec-fetch-site':'cross-site',
#     'upgrade-insecure-requests':'1',
#     'sec-fetch-mode':'navigate',
#     'sec-fetch-dest':'document',
#     'priority':'u=0, i',
#     'x-forwarded-proto':'https',
#     'x-https':'on',
# }

TGS_CHANNELS_STOP = [
    'darknet',
    'gambling',
    'shock',
    'erotica',
    'adult',
    'other'
]

TGS_MAIN_URL = 'https://tgstat.ru'
TGS_GROUPS_URL = '/ratings/channels/public?sort=members'

# TGS_GROUPS_START = '<div class="dropdown-menu max-height-320px overflow-y-scroll">'
TGS_GROUPS_START = 'Все категории'
TGS_GROUPS_FIN = '</div>'
TGS_GROUP_URL_START = '<a class="dropdown-item " href="'
TGS_GROUP_URL_FIN = '">'
TGS_GROUP_LABEL_START = ' '
TGS_GROUP_LABEL_FIN = '</a>'

# TGS_CHANNEL_START = '<div class="card peer-item-row mb-2 ribbon-box border">'
TGS_CHANNEL_URL_START = 'https://tgstat.ru/channel/@'
TGS_CHANNEL_URL_FIN = '/stat'
TGS_CHANNEL_LABEL_START = '<div class="text-truncate font-16 text-dark mt-n1">'
TGS_CHANNEL_LABEL_FIN = '</div>'
TGS_CHANNEL_SUBS_START = '<div class="text-truncate font-14 text-dark mt-n1">'
TGS_CHANNEL_SUBS_FIN = '<span'


def doc_groups_get() -> str | None:
    scraper = cloudscraper.create_scraper(
        # disableCloudflareV1=True,
        browser={
        "browser": "firefox",
        "platform": "windows",
        },
    )
        
    # resp = requests.get(url=TGS_MAIN_URL+TGS_GROUPS_URL, headers=HEADERS)
    resp = scraper.get(url=TGS_MAIN_URL+TGS_GROUPS_URL)
    print(f'{TGS_MAIN_URL+TGS_GROUPS_URL}: {resp.status_code}')
    # print(f'Response body: {resp.text}')
    if resp.status_code == 200:
        # print(f'Response body: {resp.text}')
        res, _ = data_extract(resp.text, TGS_GROUPS_START, TGS_GROUPS_FIN, 0)
        return res
    return None

def doc_group_parse(txt: str, pos_last: int = 0) -> list[dict | None, int]:
    # Извлекаем адрес группы
    res_name, pos_last = data_extract(txt, TGS_GROUP_URL_START, TGS_GROUP_URL_FIN, pos_last)

    # Если нет адреса, значит закончили чтение
    if not res_name:
        return None, -1

    # Название группы
    res_label, pos_last = data_extract(txt, TGS_GROUP_LABEL_START, TGS_GROUP_LABEL_FIN, pos_last)
    res_label = res_label.strip()

    msg = {
        'name': res_name,
        'label': res_label,
    }

    return msg, pos_last


def doc_channels_get(channels_url:str) -> str | None:
    scraper = cloudscraper.create_scraper(
        # disableCloudflareV1=True,
        browser={
        "browser": "firefox",
        "platform": "windows",
        },
    )
        
    # resp = requests.get(url=TGS_MAIN_URL+channels_url, headers=HEADERS)
    resp = scraper.get(url=TGS_MAIN_URL+channels_url)

    print(f'{TGS_MAIN_URL+channels_url}: {resp.status_code}')
    if resp.status_code == 200:
        # print(f'Response body: {resp.text}')
        return resp.text
    return None


def doc_channel_parse(txt: str, pos_last: int = 0) -> list[dict | None, int]:
    # Извлекаем адрес канала
    res_name, pos_last = data_extract(txt, TGS_CHANNEL_URL_START, TGS_CHANNEL_URL_FIN, pos_last)

    # Если нет адреса, значит закончили чтение
    if not res_name:
        return None, -1

    # Название канала
    res_label, pos_last = data_extract(txt, TGS_CHANNEL_LABEL_START, TGS_CHANNEL_LABEL_FIN, pos_last)
    res_label = res_label.strip()

    # Подписчики
    res_subs, pos_last = data_extract(txt, TGS_CHANNEL_SUBS_START, TGS_CHANNEL_SUBS_FIN, pos_last)
    res_subs = int(res_subs.strip().replace(' ', ''))

    msg = {
        'name': res_name,
        'label': res_label,
        'subs': res_subs
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


def is_stop_channel(url:str) -> bool:
    for tg_stop in TGS_CHANNELS_STOP:
        if tg_stop in url:
            return True
    return False
