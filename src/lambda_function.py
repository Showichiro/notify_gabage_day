import pandas as pd
import calendar
import json
from linebot import LineBotApi
from linebot.models import (
    MessageEvent, TextMessage, QuickReplyButton, MessageAction, QuickReply, TextSendMessage)
from datetime import datetime, timedelta, timezone
import os
import locale

df_burnable = pd.read_csv('./data/burnable.csv')
df_unburnable = pd.read_csv('./data/unburnable.csv')
df_recycle = pd.read_csv('./data/recycle.csv')

df_dict = {'burnable': df_burnable,
           'unburnable': df_unburnable, 'recycle': df_recycle}

default_message = 'ゴミの日ではありません'

LINE_ACCESS_TOKEN = os.environ['LINE_ACCESS_TOKEN']
line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)


def lambda_handler(event, content):
    area = event['area']
    user_id = event['userId']
    JST = timezone(timedelta(hours=+9), 'JST')
    datetime_now = datetime.now(JST)
    message = ''
    print('select today or tomorrow')
    if datetime_now.hour <= 12:
        message = '今日は' + create_message(area, datetime_now)
    else:
        datetime_tomorrow = datetime_now.replace(day=(datetime_now.day+1))
        message = '明日は' + create_message(area, datetime_tomorrow)
    if default_message in message:
        print('no message')
        return None
    else:
        print('push message')
        try:
            response = push_message(user_id, message)
            return None
        except Exception as e:
            print(e)
            return None


def create_message(area: str, datetime_now: datetime) -> str:
    nth_dow = get_nth_dow(
        datetime_now.year, datetime_now.month, datetime_now.day)
    message = default_message
    for gabage_name in df_dict.keys():
        if is_gabage_day(area, nth_dow, gabage_name):
            message = convert_gabage_name_en_to_ja(gabage_name) + "の日です"
            break
    return message


def get_nth_week(day: int) -> int:
    return (day - 1) // 7 + 1


def get_nth_dow(year: int, month: int, day: int) -> tuple:
    return get_nth_week(day), convert_number_to_week(calendar.weekday(year, month, day))


def is_gabage_day(area: str, nth_dow: tuple, gabage_name: str) -> bool:
    df = df_dict[gabage_name]
    df = df.set_index('Area')
    number = df.loc[area, nth_dow[1]]
    if number == 5 or str(nth_dow[0]) in str(number):
        return True
    else:
        return False


def convert_gabage_name_en_to_ja(gabage_name: str) -> str:
    if gabage_name is 'burnable':
        return "燃やすごみ"
    elif gabage_name is 'unburnable':
        return '燃やさないごみ'
    elif gabage_name is 'recycle':
        return '資源ごみ'


def push_message(user_id: str, message: str) -> dict:
    return line_bot_api.push_message(user_id, TextSendMessage(text=message))

def convert_number_to_week(number:int) -> str:
    locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
    return calendar.day_name[number]