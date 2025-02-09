from datetime import datetime, timedelta
import mysql.connector

DB_CONFIG = {}

def db_get():
    db = mysql.connector.connect(
        host=DB_CONFIG['host'],
        database=DB_CONFIG['database'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )
    return db


def log_ins(tp:str=None, msg:str=None, user_id:str=None) -> int:
    if len(msg)>15000:
        msg = msg [0:15000]
    db = db_get()
    db_cursor = db.cursor()
    sql = 'INSERT INTO t_logs (tp, msg, user_id) VALUES (%s, %s, %s)'
    db_cursor.execute(sql, [tp, msg, user_id])
    db.commit()
    return db_cursor.lastrowid

def log_last_id_get() -> int:
    db = db_get()
    db_cursor = db.cursor()
    sql = '''
        SELECT id
        FROM t_logs
        ORDER BY id DESC
        LIMIT 1;
    '''
    db_cursor.execute(sql)
    db_res = db_cursor.fetchone()
    return db_res[0]

def log_new_get(id_last:int) -> list:
    db = db_get()
    db_cursor = db.cursor()
    sql = '''
        SELECT 
            id, dt, tp, msg, user_id
        FROM t_logs
        WHERE id>%s and tp LIKE 'ERR%'
        ORDER BY id ASC;
    '''
    db_cursor.execute(sql, [id_last])
    db_res = db_cursor.fetchall()
    return db_res


def channels_get(is_fast_update:bool=False) -> list:
    db = db_get()
    db_cursor = db.cursor()
    sql = f'SELECT id, tg_name, tg_label FROM t_channels {'WHERE to_update = TRUE' if is_fast_update else ''}'
    db_cursor.execute(sql)
    db_res = db_cursor.fetchall()
    print(db_res)
    return db_res


def channel_ins(tg_name:str, tg_label:str) -> int:
    db = db_get()
    db_cursor = db.cursor()

    # Проверим, что уже есть такой канал в базе
    sql = 'SELECT id, tg_label FROM t_channels WHERE tg_name=%s'
    val = [tg_name]
    db_cursor.execute(sql, val)
    db_res = db_cursor.fetchone()

    # Если уже есть канал в базе, то сравним заголовок и при необходимости обновим
    if db_res:
        rec_id = db_res[0]
        rec_label = db_res[1]
        if rec_label != tg_label:
            sql = 'UPDATE t_channels SET tg_label=%s WHERE id=%s'
            val = [tg_label, rec_id]
            db_cursor.execute(sql, val)
            db.commit()
        return rec_id
    # Иначе вставка канала в таблицу
    else:
        sql = 'INSERT INTO t_channels (tg_name, tg_label) VALUES (%s, %s)'
        val = (tg_name, tg_label)
        db_cursor.execute(sql, val)
        db.commit()
        return db_cursor.lastrowid


def channel_upd(tg_name:str, to_update:bool) -> bool:
    db = db_get()
    db_cursor = db.cursor()
    sql = 'UPDATE t_channels SET to_update=%s WHERE tg_name=%s'
    val = [to_update, tg_name]
    db_cursor.execute(sql, val)
    db.commit()
    return to_update


def channel_tgs_get() -> list:
    db = db_get()
    db_cursor = db.cursor()
    sql = 'SELECT id, tg_name, tg_label, tg_subs, tg_group FROM t_channels_tgs ORDER BY tg_subs DESC'
    db_cursor.execute(sql)
    db_res = db_cursor.fetchall()
    return db_res


def channel_tgs_clr() -> None:
    db = db_get()
    db_cursor = db.cursor()
    sql = 'DELETE FROM t_channels_tgs'
    db_cursor.execute(sql)
    db.commit()
    return None


def channel_tgs_ins(tg_name: str, tg_label: str, tg_subs: int, tg_group: str) -> int:
    db = db_get()
    db_cursor = db.cursor()
    sql = 'INSERT INTO t_channels_tgs (tg_name, tg_label, tg_subs, tg_group) VALUES (%s, %s, %s, %s)'
    val = (tg_name, tg_label, tg_subs, tg_group)
    db_cursor.execute(sql, val)
    db.commit()
    return db_cursor.lastrowid



def message_last_get(db_user_id:int, msg_last_id:int=None, channel_id=None) -> list:
    db = db_get()
    db_cursor = db.cursor()
    sql = '''
        SELECT 
            t_m.id, t_m.channel_id, t_m.msg_text, t_c.tg_label,
            t_m.msg_id, t_m.msg_views, t_m.msg_date, 
            t_m.gpt_mistral_large, t_m.gpt_ya_cls, t_m.gpt_gemini_flash
        FROM t_messages t_m
            LEFT JOIN t_channels_users t_cu ON t_m.channel_id = t_cu.channel_id
            LEFT JOIN t_channels t_c ON t_cu.channel_id = t_c.id            
        WHERE t_m.id<COALESCE(%s, ~0)
            AND t_cu.user_id=%s
        ORDER BY msg_date DESC
        LIMIT 1;
    '''
    db_cursor.execute(sql, [msg_last_id, db_user_id])
    db_res = db_cursor.fetchone()
    print(msg_last_id, '===', db_res)
    return db_res

def message_first_get(db_user_id:int, msg_first_id:int=None, msg_dt:datetime=None, channel_id=None) -> list:
    db = db_get()
    db_cursor = db.cursor()
    sql = '''
        SELECT 
            t_m.id, t_m.channel_id, t_m.msg_text, t_c.tg_label,
            t_m.msg_id, t_m.msg_views, t_m.msg_date, 
            t_m.gpt_mistral_large, t_m.gpt_ya_cls, t_m.gpt_gemini_flash
        FROM t_messages t_m
            LEFT JOIN t_channels_users t_cu ON t_m.channel_id = t_cu.channel_id
            LEFT JOIN t_channels t_c ON t_cu.channel_id = t_c.id            
        WHERE t_m.msg_date>=COALESCE(%s, '1000-01-01 00:00:00')
            AND t_cu.user_id=%s
            AND t_m.id>COALESCE(%s, 0)
        ORDER BY msg_date ASC
        LIMIT 1;
    '''
    db_cursor.execute(sql, [msg_dt, db_user_id, msg_first_id])
    db_res = db_cursor.fetchone()
    print(msg_dt, '===', db_res)
    return db_res


def message_to_rate_get(model_name:str, channel_id=None) -> list:
    db = db_get()
    db_cursor = db.cursor()
    sql = f'''
            SELECT id, msg_text
            FROM t_messages
            WHERE {model_name} is null
            ORDER BY msg_date DESC
            LIMIT 10;
    '''
    db_cursor.execute(sql)
    db_res = db_cursor.fetchall()
    return db_res


def message_rate_upd(rec_id:int, model_name:str, msg_rate:str) -> int:
    db = db_get()
    db_cursor = db.cursor()
    sql = f'UPDATE t_messages SET {model_name}=%s WHERE id=%s'
    db_cursor.execute(sql, [msg_rate, rec_id])
    db.commit()
    return rec_id


def message_ins(channel_id: int, msg_text: str, msg_id: int, msg_views: int, msg_date: datetime) -> int:
    db = db_get()
    db_cursor = db.cursor()

    # Проверим, что уже есть такое сообщение в базе
    sql = 'SELECT id FROM t_messages WHERE channel_id=%s and msg_id=%s'
    val = [channel_id, msg_id]
    db_cursor.execute(sql, val)
    db_res = db_cursor.fetchone()
    print(db_res)

    # Если уже есть такое сообщение в базе, то обновим (как минимум обновятся данные о количестве просмотров)
    if db_res:
        rec_id = db_res[0]
        sql = 'UPDATE t_messages SET msg_text=%s, msg_views=%s WHERE id=%s'
        val = [msg_text, msg_views, rec_id]
        db_cursor.execute(sql, val)
        db.commit()
        return rec_id
    # Иначе вставка сообщения в таблицу
    else:
        sql = 'INSERT INTO t_messages (channel_id, msg_text, msg_id, msg_views, msg_date) VALUES (%s,%s,%s,%s,%s)'
        val = (channel_id, msg_text, msg_id, msg_views, msg_date)
        db_cursor.execute(sql, val)
        db.commit()
        return db_cursor.lastrowid

def messages_by_date_get(db_user_id:int, db_channel_id:int, datetime_from:datetime) -> list:
    db = db_get()
    db_cursor = db.cursor()
    sql = '''
            SELECT t_m.id, t_m.msg_text
            FROM t_messages t_m
            	LEFT JOIN t_channels_users t_cu ON t_m.channel_id = t_cu.channel_id 
            WHERE t_cu.user_id = %s and (t_m.channel_id = %s ''' + (' or 1=1 ' if db_channel_id==0 else '') + ''') and t_m.msg_date > %s
            ORDER BY msg_date DESC
            LIMIT 50;
    '''
    print(sql)
    val = [db_user_id, db_channel_id, datetime_from]
    db_cursor.execute(sql, val)
    db_res = db_cursor.fetchall()
    return db_res


# USERS
def user_ins(ya_id: str) -> int:
    db = db_get()
    db_cursor = db.cursor()
    sql = 'INSERT INTO t_users (ya_id) VALUES (%s)'
    val = (ya_id,)
    db_cursor.execute(sql, val)
    db.commit()
    return db_cursor.lastrowid

def user_dt_last_upd(db_user_id:int) -> None:
    db = db_get()
    db_cursor = db.cursor()
    sql = '''
            UPDATE db_tg.t_users
            SET dt_last=NOW()
            WHERE id=%s
    '''
    val = (db_user_id,)
    db_cursor.execute(sql, val)
    db.commit()

def user_get(db_user_id:int=0, ya_user_id:str='') -> list|None:
    db = db_get()
    db_cursor = db.cursor()
    sql = f'''
            SELECT id, ya_id, dt_first, dt_last
            FROM t_users
            WHERE {'id' if db_user_id>0 else 'ya_id'}=%s
            LIMIT 1;
    '''
    db_cursor.execute(sql, [db_user_id if db_user_id>0 else ya_user_id])
    db_res = db_cursor.fetchone()    
    return db_res


# CHANNELS

def user_channels_get(db_user_id:int) -> list|None:
    db = db_get()
    db_cursor = db.cursor()
    sql = '''
        SELECT 
        tcu.channel_id,
        tc.tg_name,
        tc.tg_label 
        FROM t_channels_users AS tcu 
        LEFT JOIN t_channels AS tc ON tcu.channel_id = tc.id 
        WHERE tcu.user_id = %s
'''
    val = [db_user_id]
    db_cursor.execute(sql, val)
    db_res = db_cursor.fetchall()
    return db_res

def user_channels_ins(db_user_id:int, db_channel_id:int) -> int:
    db = db_get()
    db_cursor = db.cursor()

    # Проверим, что нет такой связки
    sql = 'SELECT id FROM t_channels_users WHERE channel_id=%s AND user_id=%s'
    val = [db_channel_id, db_user_id]
    db_cursor.execute(sql, val)
    db_res = db_cursor.fetchone()
    
    # Если нет связки    
    if not db_res:
        sql = 'INSERT INTO t_channels_users (channel_id, user_id) VALUES (%s,%s)'
        val = [db_channel_id, db_user_id]
        db_cursor.execute(sql, val)
        db.commit()
        return db_cursor.lastrowid
    
    return db_res[0]

def user_channels_del(db_user_id:int) -> int:
    db = db_get()
    db_cursor = db.cursor()

    sql = 'DELETE FROM t_channels_users WHERE user_id = %s'
    val = [db_user_id]
    db_cursor.execute(sql, val)
    db.commit()
    return db_cursor.rowcount


# DIGESTS

def user_digest_ins(db_user_id:int, db_channel_id:int=0, ) -> list:
    db = db_get()
    db_cursor = db.cursor()

    # Проверим, что нет ранее сделанного запроса
    sql = 'SELECT td.id, td.resp_txt FROM t_digests td WHERE user_id = %s and channel_id = %s and req_dt > %s ORDER BY resp_dt DESC'
    val = [db_user_id, db_channel_id, datetime.now() - timedelta(seconds=5*60) ]
    db_cursor.execute(sql, val)
    db_res = db_cursor.fetchone()
    
    # Если нет связки    
    if not db_res:
        sql = 'INSERT INTO t_digests (user_id, channel_id) VALUES (%s,%s)'
        val = [db_user_id, db_channel_id]
        db_cursor.execute(sql, val)
        db.commit()
        return [db_cursor.lastrowid, None]
    
    return db_res

def user_digest_get(db_digest_id:int) -> list:
    db = db_get()
    db_cursor = db.cursor()

    # Проверим, что нет ранее сделанного запроса
    sql = 'SELECT td.id, td.resp_txt FROM t_digests td WHERE td.id = %s'
    val = [db_digest_id]
    db_cursor.execute(sql, val)
    db_res = db_cursor.fetchone()
    
    return db_res

def digest_to_do_get() -> list:
    db = db_get()
    db_cursor = db.cursor()
    sql = f'SELECT id, user_id, channel_id FROM t_digests WHERE resp_dt IS NULL ORDER BY id ASC'
    db_cursor.execute(sql)
    db_res = db_cursor.fetchall()
    return db_res

def digest_upd(dg_id:int, req_txt:str, resp_txt:str) -> int:
    db = db_get()
    db_cursor = db.cursor()
    sql = 'UPDATE t_digests SET req_txt=%s, resp_txt=%s, resp_dt=%s WHERE id=%s'
    db_cursor.execute(sql, [req_txt, resp_txt, datetime.now(), dg_id])
    db.commit()
    return dg_id