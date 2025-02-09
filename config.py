# DATABASE
DB_MYSQL = {
    'host':'192.168.1.115',
    'database':'db_tg',
    'user':'root',
    'password':"PUT PASSWORD HERE"
}

# TG
TG_MSG_SLEEP_SEC = 0.1*60
TG_STAT_CYCLES = 250
BOT_TOKEN = 'PUT TOKEN HERE'
BOT_CHAT_IDS = ['PUT ID HERE']

# DIGEST
DG_REQ_MIN_PERIOD = 30*60

# MISTRAL
MI_API = 'PUT TOKEN HERE'
MI_MODEL = 'mistral-large-latest'
MI_SYSTEM = 'KNOW-HOW'
MI_MODEL_EMB = 'open-mistral-nemo'
MI_SYSTEM_CH = '''KNOW-HOW'''

# YA
YA_OAUTH = 'PUT TOKEN HERE'
YA_FOLDER_ID = 'PUT ID HERE'
YA_GPT_REQUEST = {
    'modelUri': f'cls://{YA_FOLDER_ID}/yandexgpt/latest',
    'text': None,
    'task_description': 'Определи категории статьи по её тексту',
    'labels': [
        'негативная информация', 
        'реклама товаров и услуг',
        'политика',
        'финансы',
        'военные действия',
        'насилие',
        'грубость',
        'наркотики',
        'алкоголь',
        'курение',
        'половые отношения',
        'культура',
        'технологии',
        'спорт',
    ]
}

# GEMINI
GM_API = 'PUT TOKEN HERE'
GM_MODEL = 'gemini-1.5-flash'
GM_SYSTEM = 'KNOW-HOW'

GM_SYSTEM_DG = '''KNOW-HOW'''