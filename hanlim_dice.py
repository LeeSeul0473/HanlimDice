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
attribute_url = os.getenv('ATTRIBUTE_URL')
attribute_data = None

main_character = {0:'mc'}
sheet_url = {'mc' : os.getenv('MC_SHEET_URL')}
sheet_data = {'mc' : None}



# function define
def update_attributePos() :
    global attribute_data
    response = requests.get(attribute_url)
    response.encoding = 'utf-8'
    attribute_data = pd.read_csv(StringIO(response.text), encoding='utf-8', skip_blank_lines=False, header=None)
    print('AttributePos Updated!')

def update_sheet(character_name) :
    global sheet_data
    response = requests.get(sheet_url[character_name])
    response.encoding = 'utf-8'
    sheet_data.update({character_name: pd.read_csv(StringIO(response.text), encoding='utf-8', skip_blank_lines=False, header=None)})
    print('Sheet Updated!')

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


    if message.content.startswith('/d'):
        splits = message.content.split('d')
        m = int(splits[2])
        mention_n = splits[1]
        n = int(mention_n[-1])
        dice_results = []
        dice_total = 0
        for i in range(0,n) :
            random_num = random.randint(1, m)
            dice_results.append(random_num)
            dice_total += random_num
        await message.channel.send(f'> ## Dice Result : {dice_total}\n> dices : {dice_results}', reference=message)
        #await message.channel.send(f'Log : m = {m}.\nmention_m = {mention_n},=, n : {n}', reference=message)


    if message.content.startswith('/sheet'):
        global sheet_url
        global main_character

        #get character
        if 'n:' in message.content:
            character_name = message.content.split('n:')[1]
        else :
            character_name = f"{message.author.display_name}_mc"
        # print(f'Character Name : {character_name}.')

        main_character.update({message.author.id : character_name})

        #get url
        split_msg = message.content.split('spreadsheets/d/')[1]
        sheet_id = split_msg.split('/')[0]
        gid_msg = split_msg.split('#gid=')[-1]
        gid = gid_msg.split(' ')[0]
        #await message.channel.send(f'Log : sheet_id = {sheet_id}\ngid = {gid}', reference=message)
        sheet_url.update({character_name : f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"})

        #update sheet
        update_sheet(character_name)

        if f"{message.author.display_name}_mc" not in sheet_url :
            character_name = f"{message.author.display_name}_mc"
            sheet_url.update({character_name: f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"})
            update_sheet(character_name)
            print(f"{message.author.display_name}_mc also added.")

        #return
        await message.channel.send(f'Sheet Updated!', reference=message)



    elif message.content.startswith('/update'):
        # get character name
        if 'n:' in message.content:
            character_name = message.content.split('n:')[1]
        else :
            character_name = f"{message.author.display_name}_mc"
        # print(f'Character Name : {character_name}.')

        if character_name not in sheet_url :
            character_name = 'mc'

        #update sheet
        update_sheet(character_name)

        # return
        await message.channel.send(f'Sheet Updated!', reference=message)



    elif message.content.startswith('/r'):
        character_name = ''

        # get character name
        if 'n:' in message.content:
            character_name = message.content.split('n:')[1]
        else :
            character_name = f"{message.author.display_name}_mc"
        # print(f'Character Name : {character_name}.')

        #default character
        if character_name not in sheet_url :
            character_name = 'mc'
            print('character name set : mc')

        compare_sheet = sheet_data[character_name]

        roll_key = message.content.split(' ')[1]
        #await message.channel.send(f'"{roll_key}" finding...', reference=message)
        attribute = 0
        dice_result = ''

        for index, row in attribute_data.iterrows():
            if row.iloc[0] == roll_key:
                i = int(row.iloc[1])
                j = int(row.iloc[2])
                #await message.channel.send(f'i = {i}, j = {j}', reference=message)
                if compare_sheet is not None:
                    #await message.channel.send(f'{roll_key} : {sheet_data.iloc[j, i]}', reference=message)
                    attribute = int(compare_sheet.iloc[j, i])
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
        await message.channel.send(f'> ### 명령어 모음\n > * /d __*n*__d__*m*__ : 일반주사위 굴리기.\n > * /r __*판정*__ n:__*캐릭터이름*__ : 판정.\n >   * 키퍼가 입력하는 판정키워드 그대로 입력하셔야합니다.\n >   * n:을 입력하지 않을 경우 자동생성된 이름의 캐릭터로 판정합니다.\n > * /sheet __*url*__ n:__*캐릭터이름*__ : 캐릭터 시트 추가\n >    * n:을 입력하지 않을 경우 사용자 닉네임으로 캐릭터가 자동 생성(또는 교체)됩니다.\n > * /update : 캐릭터 시트 내용 변경 후 업데이트\n >    * n:을 입력하지 않을 경우 자동생성된 이름의 캐릭터가 업데이트됩니다.', reference=message)

    elif message.content.startswith('/hattribute'):
        update_attributePos()
        await message.channel.send(f'AttributePos Updated!', reference=message)

# run
update_attributePos()
update_sheet('mc')

client.run(TOKEN)