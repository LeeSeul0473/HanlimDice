import random
import discord
from discord.ext import commands, tasks
import pandas as pd
import requests
from io import StringIO
import os
from dotenv import load_dotenv

# TOKEN
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# intents, client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# propertys
sheet_url = os.getenv('SHEET_URL')
sheet_data = None
attribute_url = os.getenv('ATTRIBUTE_URL')
attribute_data = None

# function define
def update_sheet() :
    global sheet_data
    response = requests.get(sheet_url)
    response.encoding = 'utf-8'
    sheet_data = pd.read_csv(StringIO(response.text), encoding='utf-8', skip_blank_lines=False, header=None)
    print('Sheet Updated!')

def update_attributePos() :
    global attribute_data
    response = requests.get(attribute_url)
    response.encoding = 'utf-8'
    attribute_data = pd.read_csv(StringIO(response.text), encoding='utf-8', skip_blank_lines=False, header=None)
    print('AttributePos Updated!')

# ping loop
@tasks.loop(hours=1)
async def keep_alive():
   print(f"Keep alive ping: {client.latency * 1000:.2f}ms")

# bot start
@client.event
async def on_ready():
   print(f'We have logged in as {client.user}')
   keep_alive.start()

# process message
@client.event
async def on_message(message): # 봇이 메시지를 받았을 때 호출됩니다
    
    if message.author == client.user: # 봇이 보낸 메세지면 무시
        return

    if message.content.startswith('/nr'):
        split = message.content.find('d')
        if (split != -1):
            m = int(message.content.split('d')[1])
            mention_n = message.content.split('d')[0]
            n = int(mention_n.split(' ')[1])
            dice_results = []
            dice_total = 0
            for i in range(0,n) :
                random_num = random.randint(1, m)
                dice_results.append(random_num)
                dice_total += random_num
            await message.channel.send(f'> ## Dice Result : {dice_total}\n> dices : {dice_results}', reference=message)
            #await message.channel.send(f'Log : m = {m}.\nmention_m = {mention_n},=, n : {n}', reference=message)

    if message.content.startswith('/hsheet'):
        global sheet_url
        split_msg = message.content.split('spreadsheets/d/')[1]
        sheet_id = split_msg.split('/')[0]
        gid = split_msg.split('#gid=')[-1]
        #await message.channel.send(f'Log : sheet_id = {sheet_id}\ngid = {gid}', reference=message)
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        update_sheet()
        await message.channel.send(f'Sheet Updated!', reference=message)

    elif message.content.startswith('/hupdate'):
        update_sheet()
        await message.channel.send(f'Sheet Updated!', reference=message)

    elif message.content.startswith('/hr'):
        roll_key = message.content.split(' ')[1]
        #await message.channel.send(f'"{roll_key}" finding...', reference=message)
        attribute = 0
        dice_result = ''

        for index, row in attribute_data.iterrows():
            if row.iloc[0] == roll_key:
                i = int(row.iloc[1])
                j = int(row.iloc[2])
                #await message.channel.send(f'i = {i}, j = {j}', reference=message)
                if sheet_data is not None:
                    #await message.channel.send(f'{roll_key} : {sheet_data.iloc[j, i]}', reference=message)
                    attribute = int(sheet_data.iloc[j, i])
                else :
                    print('SheetData is None!')
                break

        random_num = random.randint(1, 100)

        if(random_num > attribute) :
            if(random_num == 100) :
                dice_result = '대실패'
            else :
                dice_result = '실패'
        elif(random_num > attribute/2) :
            dice_result = '성공'
        elif(random_num > attribute/5) :
            dice_result = '어려운 성공'
        else :
            if(random_num == 1) :
                dice_result = '대성공'
            else :
                dice_result = '극단적 성공'

        await message.channel.send(f'> ***다이스 결과 "{roll_key}" 판정***\n> ## {dice_result}\n> Dice : {random_num}/{attribute}', reference=message)

    elif message.content.startswith('/hhelp'):
        await message.channel.send(f'> ### 명령어 모음\n > * /nr __*n*__d__*m*__ : 일반주사위 굴리기.\n > * /hr __*판정*__ : 판정.(키퍼가 입력하는 판정키워드 그대로 입력하셔야합니다.)\n > * /hsheet __*url*__ : 시트 변경\n > * /hupdate : 캐릭터 시트 내용 변경 후 업데이트', reference=message)

    elif message.content.startswith('/hattribute'):
        update_attributePos()
        await message.channel.send(f'AttributePos Updated!', reference=message)

# run
update_attributePos()
update_sheet()

client.run(TOKEN)