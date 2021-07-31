import StackDice as sd
from typing import Dict
import keys
import logging
import pickle

import discord
from discord.ext import commands
import gspread

global app

if __name__ == '__main__':

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s : %(message)s', '%Y-%m-%d %H:%M:%S')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_debug_handler = logging.FileHandler(filename='log.txt', encoding='utf-8')
    file_debug_handler.setLevel(logging.DEBUG)
    file_debug_handler.setFormatter(formatter)
    logger.addHandler(file_debug_handler)

    logger.info('Application start')

    app = commands.Bot(command_prefix='!')

    gc = gspread.authorize(keys.credentials)

    # d: Dict[str, str] = {}
    # pickle.dump(d, open('data/docs.txt', 'wb'))
    # pickle.dump(d, open('data/docs_alias.txt', 'wb'))
    # pickle.dump(d, open('data/sheet_data.txt', 'wb'))
    # pickle.dump(d, open('data/dice_alias.txt', 'wb'))

    data_docs: Dict[str, str] = pickle.load(open('data/docs.txt', 'rb'))
    data_pre_docs: Dict[str, str] = pickle.load(open('data/docs_alias.txt', 'rb'))
    data_player: Dict[str, str] = pickle.load(open('data/sheet_data.txt', 'rb'))
    data_dice_alias: Dict[str, str] = pickle.load(open('data/dice_alias.txt', 'rb'))

    # 사용중인 docs
    docs: Dict[str, gspread.Spreadsheet] = {}

    # 별명이 지어진 docs
    pre_docs: Dict[str, gspread.Spreadsheet] = {}
    pre_docs_uri: Dict[str, str] = {}
    for key in data_pre_docs.keys():
        pre_docs[key] = gc.open_by_url(data_pre_docs[key])

    # docs 에서 사용하는 시트
    player: Dict[str, gspread.Worksheet] = {}
    for key in data_player.keys():
        tokens = data_player[key].split('→')
        docs[key] = gc.open_by_url(tokens[0])
        player[key] = docs[key].worksheet(tokens[1])
    # sheet.url + '→' + sheet_name

    # guild:user:alias , query
    dice_alias: Dict[str, str] = {}
    for key in data_dice_alias.keys():
        dice_alias[key] = data_dice_alias[key]

    fixed_sheet_position: Dict[str, str] = {
        "근력": "P7",
        "민첩": "T7",
        "정신": "X7",
        "건강": "P9",
        "외모": "T9",
        "교육": "X9",
        "크기": "P11",
        "지능": "T11",
        "행운": "C18",
        "이성": "V15"
    }
    logger.info('Data load complete')

# TODO: dice alias


@app.event
async def on_ready():
    logger.info(f'{app.user} has connected to Discord!')
    await app.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.listening, name="!다이스"))
    active_servers = app.guilds
    logger.info("---Active Server List---")
    for guild in active_servers:
        logger.info(guild.name)
    logger.info(f"- Active Server count : {len(active_servers)} -")


@app.event
async def on_guild_join(guild):
    logger.info('Bot has been added to a new server')
    logger.info(f'Name of server: {guild}')
    logger.info(f"- Active Server count : {len(app.guilds)} -")


@app.event
async def on_guild_remove(guild):
    logger.info('Bot has been removed to a server')
    logger.info(f'Name of server: {guild}')
    logger.info(f"- Active Server count : {len(app.guilds)} -")


@app.command(name='다이스')
async def help_message(ctx: discord.ext.commands.Context):
    logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'help1']))
    embed_message = discord.Embed(title=f":game_die: 주사위(다이스) 사용법",
                                  description=
                                  '`!roll NdR` `!roll Ndf`\n'
                                  '`!roll NdR + X` `!roll NdR - X` `!roll NdR * X` `!roll NdR / X`\n'
                                  '`!roll NdR < X` `!roll NdR > X` `!roll NdR <= X` `!roll NdR >= X`\n'
                                  '`!roll NdRhX` `!roll NdRlX`\n'
                                  '`!roll NdR + MdS ...`\n'
                                  '`!ra [name] [expr]`\n'
                                  '`!rs [name]`\n'
                                  '`!rt [name] [expr]`\n'
                                  '\n'
                                  '※ `!r NdR`로 입력하실 수도 있습니다.\n'
                                  '\n'
                                  '**N**은 **주사위의 개수**입니다.(N이 없으면 1로 간주합니다.)\n'
                                  '**R**은 주사위 하나의 면의 수입니다.\n'
                                  '**R** 대신 알파벳 **f**를 넣으면 **페이트 다이스**를 굴리실 수 있습니다.\n'
                                  '사칙연산과 괄호연산을 지원합니다.\n'
                                  '\n'
                                  '`!r (3d6+4df)*5+5d8`처럼 여러개의 주사위를 연결해서 굴리실 수 있습니다.\n'
                                  '\n'
                                  '`!r 1d100 < 50`처럼 판정값의 성공/실패를 체크할 수 있습니다.\n'
                                  '\n'
                                  '`!r 20d100h10`을 사용하면 20개의 d100 주사위를 굴린후, 상위 10개의 주사위 값을 사용 할 수 있습니다.\n'
                                  '`!r 10d100l1`을 사용하면 10개의 d100 주사위를 굴린후, 하위 1개의 주사위 값을 사용 할 수 있습니다.\n'
                                  '\n'
                                  '`!ra attack 1d100>=80`처럼 특정 주사위 표현식에 별명을 설정 할 수 있습니다.\n'
                                  '`!rs attack`처럼 `!ra` 명령을 통해 별명을 설정한 주사위 표현식을 굴릴 수 있습니다.\n'
                                  '`!rt attack +1d6`처럼 !ra 명령을 통해 별명을 설정한 주사위 표현식에 추가 표현식을 합하여 굴릴 수 있습니다.\n'
                                  '\n'
                                  '`!다이스2`로 CoC 7th 특화기능 명령어를 확인 하실 수 있습니다.\n\n'
                                  '`!다이스3`로 CoC 7th 세션 마스터용 명령어를 확인 하실 수 있습니다.',
                                  color=0xff8400)
    await ctx.send(embed=embed_message)


@app.command(name='다이스2')
async def help_message2(ctx: discord.ext.commands.Context):
    logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'help2']))
    embed_message = discord.Embed(title=f":game_die: 주사위(다이스) 사용법",
                                  description=
                                  '**CoC 7th 특화기능**\n'
                                  '`!roll ccc`\n'
                                  '`!ruse [시트링크] [시트이름]`\n'
                                  '`!ruse [시트별명] [시트이름]`\n'
                                  '`!rr [특성치/기능치] (보정치)`\n'
                                  '`!rstat`\n'
                                  '`!rreset`\n'
                                  '\n'
                                  '`!r ccc`로 CoC 7th 캐릭터 메이킹을 빠르게 진행 할 수 있습니다.\n'
                                  '`!ruse [구글스프레드시트링크] [시트이름]`으로 간편 판정 탐사자를 등록 할 수 있습니다.\n'
                                  'ex> `!ruse https://docs.google.com/spreadsheets/d/'
                                  '1CzAo97L-ioGFHo_d8MC64nxAKiLchd-MkixYL4mxjwE \"조 종사(Niq)\"` \n\n'
                                  '마스터가 시트 별명을 미리 등록한 경우, \n'
                                  '`!ruse [시트별명] [시트이름]`으로 간편 판정 탐사자를 등록 할 수 있습니다.\n'
                                  'ex> `!ruse 테스트용별명 \"조 종사(Niq)\"` '
                                  '\n'
                                  '\n'
                                  '`!rr [판정이름]`으로 등록한 탐사자 특성/기능치 판별을 빠르게 할 수 있습니다.'
                                  '\n'
                                  '`!rr [판정이름] [일반표현식]`으로 보정치를 설정 할 수 있습니다. **(띄어쓰기 필수!)**'
                                  '\n'
                                  '`!rr [판정이름] b[개수]` `!rr [판정이름] p[개수]`으로 보너스/페널티 주사위를 사용 할 수 있습니다. **(띄어쓰기 필수!)**'
                                  '\n'
                                  'ex> `!rr 심리학` `!rr 심리학 +20` `!rr 심리학 -((4d6)/5)` `!rr 심리학 b4` `!rr 심리학 p3` '
                                  '\n'
                                  '\n'
                                  '`!rstat`으로 등록한 탐사자 이름과 시트 링크를 확인 할 수 있습니다.'
                                  '\n'
                                  '\n'
                                  '`!rreset`으로 등록한 탐사자를 해제할 수 있습니다.'
                                  '\n'
                                  ,
                                  color=0xff8400)
    await ctx.send(embed=embed_message)


@app.command(name='다이스3')
async def help_message2(ctx: discord.ext.commands.Context):
    logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'help3']))
    embed_message = discord.Embed(title=f":game_die: 주사위(다이스) 사용법",
                                  description=
                                  '**CoC 7th 특화기능**\n'
                                  '**TRPG 마스터 전용**\n'
                                  '`!radd [시트 별명] [시트링크] `\n'
                                  '`!rremove [시트 별명]`\n'
                                  '`!rremoveall`\n'
                                  '`!rclear`\n'
                                  '\n'
                                  '`!radd [구글스프레드시트링크] [시트이름]`으로 시트 링크에 별명을 설정할 수 있습니다.\n'
                                  'ex> `!radd 테스트용별명 https://docs.google.com/spreadsheets/d/'
                                  '1CzAo97L-ioGFHo_d8MC64nxAKiLchd-MkixYL4mxjwE`'
                                  '\n'
                                  '\n'
                                  '`!rremove [시트별명]`으로 등록된 시트 별명을 해제할 수 있습니다.'
                                  '\n'
                                  '\n'
                                  '`!rremoveall`으로 등록된 모든 시트 별명을 일괄 해제할 수 있습니다.'
                                  '\n'
                                  '\n'
                                  '`!rclear`으로 등록된 모든 탐사자를 일괄 해제할 수 있습니다.'

                                  ,
                                  color=0xff8400)
    await ctx.send(embed=embed_message)


@app.command(name='r', pass_context=True)
async def r(ctx: discord.ext.commands.Context, *args):
    await roll(ctx, *args)


@app.command(name='roll', pass_context=True)
async def roll(ctx: discord.ext.commands.Context, *args):
    query = ''.join(args)
    logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'query', query]))
    if args[0] == 'ccc':
        await sd.make_character(ctx)
    else:
        await sd.roll_dice(ctx, query)


@app.command(name='ra', pass_context=True)
async def alias_dice(ctx: discord.ext.commands.Context, *args):
    name = args[0]
    query = ''.join(args[1:])
    key = str(ctx.guild) + str(ctx.author)
    logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'dice alias', ''.join(args)]))

    dice_alias[key+":"+name] = query
    data_dice_alias[key+":"+name] = query
    pickle.dump(data_dice_alias, open('data/dice_alias.txt', 'wb'))

    embed_message = discord.Embed(title="주사위 별명이 등록되었습니다.")
    embed_message.add_field(name="플레이어", value=ctx.message.author.mention, inline=False)
    embed_message.add_field(name="주사위 별명", value=name, inline=False)
    embed_message.add_field(name="주사위 명령", value=query, inline=False)
    await ctx.send(embed=embed_message)


@app.command(name='rs', pass_context=True)
async def roll_alias_dice(ctx: discord.ext.commands.Context, *args):
    name = args[0]
    key = str(ctx.guild) + str(ctx.author)
    logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'roll alias', ''.join(args)]))
    if key+":"+name in dice_alias.keys():
        await roll(ctx, dice_alias[key+":"+name])
    else:
        embed_message = discord.Embed(title="존재하지 않는 주사위 별명입니다.")
        await ctx.send(embed=embed_message)


@app.command(name='rt', pass_context=True)
async def roll_alias_dice_with_addition(ctx: discord.ext.commands.Context, *args):
    name = args[0]
    key = str(ctx.guild) + str(ctx.author)
    logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'roll alias', ''.join(args)]))
    if key+":"+name in dice_alias.keys():
        await roll(ctx, dice_alias[key+":"+name]+''.join(args[1:]))
    else:
        embed_message = discord.Embed(title="존재하지 않는 주사위 별명입니다.")
        await ctx.send(embed=embed_message)

# ----


def get_sheet_value(worksheet: gspread.Worksheet, target):
    if target in fixed_sheet_position.keys():
        cell = worksheet.acell(fixed_sheet_position[target])
        v = int(cell.value)
    else:
        cell = worksheet.find(target)
        row = cell.row
        col = cell.col
        v = int(worksheet.cell(row, col + 4).value)
    return v


def judgement(value, v):
    result = {
        v < value: "실패",
        (v < 50 and value >= 96): "대실패",
        (v / 2 < value <= v): "성공",
        (v / 5 < value <= v / 2): "어려운 성공",
        value <= v / 5: "극단적 성공",
        value == 1: "1!",
        value == 100: "100!"
    }.get(True)
    return [value, result]


def calc_bonus(value, num, dices):
    dice = list()
    sd.dice(num, 10, dice)
    d = dice[0][:-1]
    d.sort()
    v = value % 10
    if v == 0:
        if value // 10 > d[0]:
            result = v + d[0] * 10
        else:
            result = value
    else:
        if 10 in d:
            result = v
        else:
            if value // 10 > d[0]:
                result = v + d[0] * 10
            else:
                result = value
    d = [x if x != 10 else 0 for x in d]
    d.sort()
    dices.append([x * 10 for x in d])
    return result


def calc_penalty(value, num, dices):
    dice = list()
    sd.dice(num, 10, dice)
    d = dice[0][:-1]
    d.sort()
    v = value % 10
    if v == 0:
        if 10 in d:
            result = 100
        else:
            d = [x if x != 10 else 0 for x in d]
            d.sort()
            if value // 10 < d[-1]:
                result = v + d[-1] * 10
            else:
                result = value
    else:
        d = [x if x != 10 else 0 for x in d]
        d.sort()
        if value // 10 < d[-1]:
            result = v + d[-1] * 10
        else:
            result = value
    dices.append([x * 10 for x in d])
    return result


@app.command(name='rr', pass_context=True)
async def roll2(ctx: discord.ext.commands.Context, *args):
    logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'rr', ' '.join(args)]))
    key = str(ctx.guild) + str(ctx.author)
    try:

        if key in player:
            sheet = player[key]
            sheet_value = get_sheet_value(sheet, args[0])
            dice_value = sd.dice(1, 100, [])
            dices = [dice_value]
            if len(args) > 1:
                if str(args[1]).startswith('b'):
                    expr = sd.calc_expr(''.join(args[1:])[1:], dices, [])
                    dice_value = calc_bonus(dice_value, expr, dices)
                elif str(args[1]).startswith('p'):
                    expr = sd.calc_expr(''.join(args[1:])[1:], dices, [])
                    dice_value = calc_penalty(dice_value, expr, dices)
                else:
                    expr = str(dice_value) + ''.join(args[1:])
                    dice_value = sd.calc_expr(expr, dices, [])
            jud = judgement(dice_value, sheet_value)
            embed_message = discord.Embed(title=f":game_die: {args[0]} 판정 : {jud[1]}!", color=0xff8400)
            embed_message.add_field(name="플레이어", value=ctx.message.author.mention, inline=False)
            embed_message.add_field(name="판정값", value=f"{jud[0]} <= {sheet_value}", inline=False)

            if len(dices) > 1:
                embed_message.add_field(name="주사위 목록",
                                        value='\n'.join(map(str, dices)), inline=False)

            await ctx.send(embed=embed_message)
        else:
            embed_message = discord.Embed(title=f"등록된 탐사자가 없습니다.", description=f"플레이어 : {ctx.author.mention}",
                                          color=0xff8400)
            await ctx.send(embed=embed_message)

    except Exception as e:
        embed_message = discord.Embed(title=f":x: 지원하지 않는 명령어입니다.", description=f"플레이어 : {ctx.author.mention}",
                                      color=0xff8400)
        logger.info(e)
        await ctx.send(embed=embed_message)


@app.command(name='radd', pass_context=True)
async def alias_sheet(ctx: discord.ext.commands.Context, *args):
    logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'radd', ' '.join(args)]))
    roles = [role for role in ctx.author.roles if role.name == "TRPG 마스터"]

    name = args[0]
    uri = args[1]

    if len(roles) > 0:
        try:
            guild: discord.guild.Guild = ctx.guild
            doc = gc.open_by_url(uri)
            key = str(guild) + str(name)
            if key in pre_docs.keys():
                embed_message = discord.Embed(title=f"{name} 이름의 시트 별명은 이미 존재합니다.",
                                              description=f"마스터 : {ctx.author.mention}", color=0xff8400)
                embed_message.add_field(name="시트링크", value=pre_docs[key].url, inline=False)
                await ctx.send(embed=embed_message)
            else:
                pre_docs[key] = doc
                data_pre_docs[key] = uri
                pickle.dump(data_pre_docs, open("data/docs_alias.txt", "wb"))
                embed_message = discord.Embed(title=f"{name} 시트 별명을 등록했습니다.",
                                              description=f"마스터 : {ctx.author.mention}", color=0xff8400)
                embed_message.add_field(name="시트링크", value=pre_docs[key].url, inline=False)
                await ctx.send(embed=embed_message)

        except gspread.exceptions.APIError as e:
            err_text = str(e.response)
            if err_text == '<Response [403]>':
                embed_message = discord.Embed(title=f":x: 시트의 접근권한이 없습니다.",
                                              description=f"마스터 : {ctx.author.mention} \n 시트의 접근권한을 변경해 주세요.",
                                              color=0xff8400)
                await ctx.send(embed=embed_message)
    else:
        embed_message = discord.Embed(title=f":x: 명령을 수행할 권한이 없습니다.",
                                      description=f"플레이어 : {ctx.author.mention}", color=0xff8400)
        await ctx.send(embed=embed_message)


@app.command(name='rremove', pass_context=True)
async def remove_sheet(ctx: discord.ext.commands.Context, *args):
    logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'rremove', ' '.join(args)]))
    roles = [role for role in ctx.author.roles if role.name == "TRPG 마스터"]

    name = args[0]
    if len(roles) > 0:
        guild: discord.guild.Guild = ctx.guild
        key = str(guild) + str(name)
        if key in pre_docs.keys():
            del pre_docs[key]
            del data_pre_docs[key]
            pickle.dump(data_pre_docs, open("data/docs_alias.txt", "wb"))
            embed_message = discord.Embed(title=f"{name} 이름의 시트 별명을 등록 해제했습니다.",
                                          description=f"마스터 : {ctx.author.mention}", color=0xff8400)
            await ctx.send(embed=embed_message)
        else:
            embed_message = discord.Embed(title=f"{name} 이름의 시트 별명은 존재하지 않습니다.",
                                          description=f"마스터 : {ctx.author.mention}", color=0xff8400)
            await ctx.send(embed=embed_message)
    else:
        embed_message = discord.Embed(title=f":x: 명령을 수행할 권한이 없습니다.",
                                      description=f"플레이어 : {ctx.author.mention}", color=0xff8400)
        await ctx.send(embed=embed_message)


@app.command(name='rremoveall', pass_context=True)
async def remove_all_sheet(ctx: discord.ext.commands.Context):
    logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'rremoveall']))
    roles = [role for role in ctx.author.roles if role.name == "TRPG 마스터"]

    if len(roles) > 0:
        deleted_sheet = []
        for pd in pre_docs:
            if pd.startswith(str(ctx.guild)):
                deleted_sheet.append(pd)
        message = []
        for ds in deleted_sheet:
            message.append(pre_docs[ds].url)
            del pre_docs[ds]
            del data_pre_docs[ds]

        if len(message) > 0:
            pickle.dump(data_pre_docs, open("data/docs_alias.txt", "wb"))
            embed_message = discord.Embed(title=f":x: 다음 시트 별명을 등록 해제했습니다.",
                                          description=f"마스터: {ctx.author.mention}",
                                          color=0xff8400)
            embed_message.add_field(name="등록 해제 목록", value='\n'.join(message), inline=False)
            await ctx.send(embed=embed_message)
        else:
            embed_message = discord.Embed(title=f":x: 등록 해제할 시트 별명이 없습니다.",
                                          description=f"마스터: {ctx.author.mention}",
                                          color=0xff8400)
            await ctx.send(embed=embed_message)
    else:
        embed_message = discord.Embed(title=f":x: 명령을 수행할 권한이 없습니다.",
                                      description=f"플레이어 : {ctx.author.mention}", color=0xff8400)
        await ctx.send(embed=embed_message)


@app.command(name='ruse', pass_context=True)
async def use_player_sheet(ctx: discord.ext.commands.Context, *args):
    logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'ruse', ' '.join(args)]))
    try:
        user = ctx.author
        guild: discord.guild.Guild = ctx.guild

        uri = args[0]
        key = str(guild) + str(uri)
        if key in pre_docs:
            doc = pre_docs[key]
            sheet_url = data_pre_docs[key]
        else:
            try:
                doc = gc.open_by_url(uri)
                sheet_url = uri
            except gspread.exceptions.NoValidUrlKeyFound:
                raise Exception

        sheet_name = ' '.join(args[1:])
        sheet = doc.worksheet(sheet_name)
        docs[str(guild)+str(user)] = doc
        player[str(guild)+str(user)] = sheet

        data_player[str(guild) + str(user)] = sheet_url + '→' + sheet_name
        pickle.dump(data_player, open("data/sheet_data.txt", "wb"))

        embed_message = discord.Embed(title=f"지금부터 \"{sheet.acell('E7').value}\" 탐사자를 사용합니다.",
                                      description=f"플레이어 : {ctx.author.mention}", color=0xff8400)
        await ctx.send(embed=embed_message)

    except gspread.exceptions.APIError as e:
        err_text = str(e.response)
        if err_text == '<Response [403]>':
            embed_message = discord.Embed(title=f":x: 시트의 접근권한이 없습니다.",
                                          description=f"플레이어 : {ctx.author.mention} \n 시트의 접근권한을 변경해 주세요.",
                                          color=0xff8400)
            await ctx.send(embed=embed_message)
    except gspread.exceptions.WorksheetNotFound:
        embed_message = discord.Embed(title=":x: 올바르지 않은 시트이름입니다.", color=0xff8400)
        await ctx.send(embed=embed_message)


@app.command(name='rreset', pass_context=True)
async def reset_player_sheet(ctx: discord.ext.commands.Context):
    logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'rreset']))
    key = str(ctx.guild) + str(ctx.author)
    try:
        if key in player:
            del player[key]
            del data_player[key]
            pickle.dump(data_player, open("data/sheet_data.txt", "wb"))
            embed_message = discord.Embed(title=f"탐사자 등록을 해제했습니다.", description=f"플레이어 : {ctx.author.mention}",
                                          color=0xff8400)
            await ctx.send(embed=embed_message)
        else:
            embed_message = discord.Embed(title=f"등록된 탐사자가 없습니다.", description=f"플레이어 : {ctx.author.mention}",
                                          color=0xff8400)
            await ctx.send(embed=embed_message)
    except Exception as e:
        embed_message = discord.Embed(title=f":x: 명령을 수행하는데 실패했습니다.",
                                      description=f"플레이어 : {ctx.author.mention}", color=0xff8400)
        logger.info(e)
        await ctx.send(embed=embed_message)


@app.command(name='rstat', pass_context=True)
async def stat_player_sheet(ctx: discord.ext.commands.Context):
    logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'rstat']))
    try:
        key = str(ctx.guild)+str(ctx.author)
        if key in player:
            sheet = player[key]
            embed_message = discord.Embed(title=f"현재 사용하고 있는 탐사자는 \"{sheet.acell('E7').value}\"입니다.",
                                          description=f"플레이어: {ctx.author.mention}", color=0xff8400)
            embed_message.add_field(name="시트링크", value=docs[key].url + ' # ' + sheet.title, inline=False)
            await ctx.send(embed=embed_message)
        else:
            embed_message = discord.Embed(title=f"등록된 탐사자가 없습니다.", description=f"플레이어 : {ctx.author.mention}",
                                          color=0xff8400)
            await ctx.send(embed=embed_message)
    except Exception as e:
        embed_message = discord.Embed(title=f":x: 명령을 수행하는데 실패했습니다.",
                                      description=f"플레이어 : {ctx.author.mention}", color=0xff8400)
        logger.info(e)
        await ctx.send(embed=embed_message)


@app.command(name='rclear', pass_context=True)
async def clear_player_sheet(ctx: discord.ext.commands.Context):
    logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'rclaer']))
    roles = [role for role in ctx.author.roles if role.name == "TRPG 마스터"]

    if len(roles) > 0:

        deleted_user = []
        for pl in player:
            if pl.startswith(str(ctx.guild)):
                deleted_user.append(pl)
        message = []
        for du in deleted_user:
            message.append(player[du].title)
            del player[du]
            del data_player[du]

        if len(message) > 0:
            pickle.dump(data_player, open("data/sheet_data.txt", "wb"))
            embed_message = discord.Embed(title=f":x: 다음 플레이어 시트를 등록 해제했습니다.",
                                          description=f"마스터: {ctx.author.mention}",
                                          color=0xff8400)
            embed_message.add_field(name="등록 해제 목록", value='\n'.join(message), inline=False)
        else:
            embed_message = discord.Embed(title=f":x: 등록 해제할 플레이어 시트가 없습니다.",
                                          description=f"마스터: {ctx.author.mention}",
                                          color=0xff8400)
    else:
        embed_message = discord.Embed(title=f":x: 명령을 수행할 권한이 없습니다.",
                                      description=f"플레이어 : {ctx.author.mention}", color=0xff8400)
    await ctx.send(embed=embed_message)

app.run(keys.TOKEN)

