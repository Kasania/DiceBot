import StackDice as sd
from typing import Dict

import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials

global app

if __name__ == '__main__':
    app = commands.Bot(command_prefix='!')

    credentials = ServiceAccountCredentials.from_json_keyfile_name("dicebot-key.json")
    gc = gspread.authorize(credentials)
    docs: Dict[str, gspread.Spreadsheet] = {}
    player: Dict[str, gspread.Worksheet] = {}
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

@app.event
async def on_ready():
    print(f'{app.user} has connected to Discord!')
    await app.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.listening, name="!다이스"))
    active_servers = app.guilds
    for guild in active_servers:
        print(guild.name)


@app.command(name='다이스')
async def help_message(ctx: discord.ext.commands.Context):
    embed_message = discord.Embed(title=f":game_die: 주사위(다이스) 사용법",
                                  description=
                                  '`!roll NdR` `!roll Ndf`\n'
                                  '`!roll NdR + X` `!roll NdR - X` `!roll NdR * X` `!roll NdR / X`\n'
                                  '`!roll NdR < X` `!roll NdR > X` `!roll NdR <= X` `!roll NdR >= X`\n'
                                  '`!roll NdR + MdS ...`\n'
                                  '`!roll ccc`\n'
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
                                  '`!r ccc`로 CoC 7th 캐릭터 메이킹을 빠르게 진행 할 수 있습니다.'
                                  '\n\n'
                                  '(테스트 중인 기능!)\n'
                                  '`!ruse [구글스프레드시트링크] [시트이름]`으로 간편 판정 탐사자를 등록 할 수 있습니다.'
                                  'ex> `!ruse https://docs.google.com/spreadsheets/d'
                                  '/1ZzXjzplwt3lSnNNsrnQfrPtmUsHvEfgxK31XWEa2lWA \"조 종사(Niq)\"` '
                                  '\n'
                                  '`!rr [판정이름]`으로 등록한 탐사자 특성/기능치 판별을 빠르게 할 수 있습니다.'
                                  'ex> `!rr 심리학`'
                                  '\n'
                                  '`!rstat`으로 등록한 탐사자 이름과 시트 링크를 확인 할 수 있습니다.'
                                  '\n'
                                  '`!rreset`으로 등록한 탐사자를 해제할 수 있습니다.'
                                  '\n'
                                  '`TRPG 마스터는 !rclear`으로 등록된 모든 탐사자를 일괄 해제할 수 있습니다.'
                                  ,
                                  color=0xff8400)
    await ctx.send(embed=embed_message)


@app.command(name='r', pass_context=True)
async def r(ctx: discord.ext.commands.Context, *args):
    await roll(ctx, *args)


@app.command(name='roll', pass_context=True)
async def roll(ctx: discord.ext.commands.Context, *args):
    query = ''.join(args)
    print(' '.join([ctx.message.author.mention, 'query', query]))
    if args[0] == 'ccc':
        await sd.make_character(ctx)
    else:
        await sd.roll_dice(ctx, query)


# ----


def roll_sheet(worksheet: gspread.Worksheet, target):
    value = sd.dice(1, 100, [])
    if target in fixed_sheet_position.keys():
        cell = worksheet.acell(fixed_sheet_position[target])
        v = int(cell.value)
    else:
        cell = worksheet.find(target)
        row = cell.row
        col = cell.col
        v = int(worksheet.cell(row, col + 4).value)
    result = {
        v < value: "실패",
        (v < 50 and value >= 96): "대실패",
        (v / 2 < value <= v): "성공",
        (v / 5 < value <= v / 2): "어려운 성공",
        value <= v / 5: "극단적 성공",
        value == 1: "1!",
        value == 100: "100!"
    }.get(True)

    return [value, v, result]


@app.command(name='rr', pass_context=True)
async def roll2(ctx: discord.ext.commands.Context, *args):
    key = str(ctx.guild) + str(ctx.author)
    if key in player:
        sheet = player[key]
        result = roll_sheet(sheet, args[0])
        embed_message = discord.Embed(title=f":game_die: {args[0]} 판정 : {result[2]}!", color=0xff8400)
        embed_message.add_field(name="플레이어", value=ctx.message.author.mention, inline=False)
        embed_message.add_field(name="판정값", value=f"{result[0]} <= {result[1]}", inline=False)
        await ctx.send(embed=embed_message)
    else:
        embed_message = discord.Embed(title=f"등록된 탐사자가 없습니다.", description=f"플레이어 : {ctx.author.mention}",
                                      color=0xff8400)
        await ctx.send(embed=embed_message)


@app.command(name='ruse', pass_context=True)
async def use_sheet(ctx: discord.ext.commands.Context, *args):
    try:
        user = ctx.author
        guild: discord.guild.Guild = ctx.guild

        uri = args[0]
        doc = gc.open_by_url(uri)
        sheet_name = args[1]
        sheet = doc.worksheet(sheet_name)
        docs[str(guild)+str(user)] = doc
        player[str(guild)+str(user)] = sheet
        embed_message = discord.Embed(title=f"지금부터 \"{sheet.acell('E7').value}\" 탐사자를 사용합니다.",
                                      description=f"플레이어 : {ctx.author.mention}", color=0xff8400)
        await ctx.send(embed=embed_message)

    except gspread.exceptions.APIError as e:
        err_text = str(e.response)
        if err_text == '<Response [403]>':
            embed_message = discord.Embed(title=f":x: 시트의 접근권한이 없습니다.", description='시트의 접근권한을 변경해 주세요.',
                                          color=0xff8400)
            await ctx.send(embed=embed_message)
    except gspread.exceptions.WorksheetNotFound:
        embed_message = discord.Embed(title=":x: 올바르지 않은 시트이름입니다.", color=0xff8400)
        await ctx.send(embed=embed_message)
    except Exception as e:
        embed_message = discord.Embed(title=f":x: 명령을 수행하는데 실패했습니다.", description=str(e), color=0xff8400)
        await ctx.send(embed=embed_message)


@app.command(name='rreset', pass_context=True)
async def add_sheet(ctx: discord.ext.commands.Context):
    key = str(ctx.guild) + str(ctx.author)
    try:
        if key in player:
            del player[key]
            embed_message = discord.Embed(title=f"탐사자 등록을 해제했습니다.", description=f"플레이어 : {ctx.author.mention}",
                                          color=0xff8400)
            await ctx.send(embed=embed_message)
        else:
            embed_message = discord.Embed(title=f"등록된 탐사자가 없습니다.", description=f"플레이어 : {ctx.author.mention}",
                                          color=0xff8400)
            await ctx.send(embed=embed_message)
    except Exception as e:
        embed_message = discord.Embed(title=f":x: 명령을 수행하는데 실패했습니다.", description=str(e), color=0xff8400)
        await ctx.send(embed=embed_message)


@app.command(name='rstat', pass_context=True)
async def stat_sheet(ctx: discord.ext.commands.Context):
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
        embed_message = discord.Embed(title=f":x: 명령을 수행하는데 실패했습니다.", description=str(e), color=0xff8400)
        await ctx.send(embed=embed_message)


# TODO: role(TRPG-Master) can remove registered player sheets
@app.command(name='rclear', pass_context=True)
async def stat_sheet(ctx: discord.ext.commands.Context):
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
        if len(message) > 0:
            embed_message = discord.Embed(title=f":x: 다음 플레이어 시트를 등록 해제했습니다.",
                                          description=f"마스터: {ctx.author.mention}",
                                          color=0xff8400)
            embed_message.add_field(name="등록 해제 목록", value='\n'.join(message), inline=False)
        else:
            embed_message = discord.Embed(title=f":x: 플레이어 시트를 등록 해제할 플레이어가 없습니다.",
                                          description=f"마스터: {ctx.author.mention}",
                                          color=0xff8400)
    else:
        embed_message = discord.Embed(title=f":x: 명령을 수행할 권한이 없습니다.", color=0xff8400)
    await ctx.send(embed=embed_message)

    
app.run(open("./TOKEN").readline())
