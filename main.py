import random
from typing import Dict

import discord
import gspread
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials


class Stack:
    def __init__(self):
        self.data = []

    def size(self):
        return len(self.data)

    def is_empty(self):
        return self.size() == 0

    def push(self, item):
        self.data.append(item)

    def pop(self):
        return self.data.pop()

    def peek(self):
        return self.data[-1]


def split_tokens(expr_str):
    tokens = []
    val = 0
    val_processing = False
    for c in expr_str:
        if c == ' ':
            continue
        if c in '0123456789':
            val = val * 10 + int(c)
            val_processing = True
            if val > 100000:
                raise AssertionError()
        else:
            if val_processing:
                tokens.append(val)
                val = 0
            val_processing = False
            tokens.append(c)

    if val_processing:
        tokens.append(val)

    return tokens


# .replace('<=', '#')
# .replace('>=', '$')
def convert_expr(token_list):
    prec = {
        'f': 6,
        'd': 5,
        '*': 4,
        '/': 4,
        '+': 3,
        '-': 3,
        '#': 2,
        '$': 2,
        '<': 2,
        '>': 2,
        '(': 1
    }
    op_stack = Stack()
    postfix_list = []
    for token in token_list:
        if type(token) is int:
            postfix_list.append(token)

        elif token == '(':
            op_stack.push(token)

        elif token == ')':
            while op_stack.peek() != '(':
                postfix_list.append(op_stack.pop())
            op_stack.pop()

        else:
            if op_stack.is_empty():
                op_stack.push(token)
            else:
                while op_stack.size() > 0:
                    if prec[op_stack.peek()] >= prec[token]:
                        postfix_list.append(op_stack.pop())
                    else:
                        break
                op_stack.push(token)
    while not op_stack.is_empty():
        postfix_list.append(op_stack.pop())
    return postfix_list


def postfix_eval(token_list, dices, judge):
    val_stack = Stack()
    for token in token_list:
        if type(token) is int:
            val_stack.push(token)
        elif token == 'f':
            val_stack.push(token)
        elif token == 'd':
            n1 = val_stack.pop()
            n2 = 1
            if not val_stack.is_empty():
                n2 = val_stack.pop()
            val_stack.push(dice(n2, n1, dices))
        else:
            n1 = val_stack.pop()
            n2 = val_stack.pop()
            if token == '+':
                val_stack.push(n2 + n1)
            elif token == '-':
                val_stack.push(n2 - n1)
            elif token == '*':
                val_stack.push(n2 * n1)
            elif token == '/':
                val_stack.push(int(n2 / n1))
            # .replace('<=', '#')
            elif token == '#':
                result = n2 <= n1
                val_stack.push(result)
                jdg = [' '.join(map(str, [int(n2), '<=', int(n1)])), '성공' if result else '실패']
                judge.append(jdg)
            # .replace('>=', '$')
            elif token == '$':
                result = n2 >= n1
                val_stack.push(result)
                jdg = [' '.join(map(str, [int(n2), '>=', int(n1)])), '성공' if result else '실패']
                judge.append(jdg)
            elif token == '<':
                result = n2 < n1
                val_stack.push(result)
                jdg = [' '.join(map(str, [int(n2), '<', int(n1)])), '성공' if result else '실패']
                judge.append(jdg)
            elif token == '>':
                result = n2 > n1
                val_stack.push(result)
                jdg = [' '.join(map(str, [int(n2), '>', int(n1)])), '성공' if result else '실패']
                judge.append(jdg)
    return val_stack.pop()


def dice(x, y, dices):
    value = 0
    d = []
    if x > 1000:
        raise AssertionError()
    if y == 'f':
        for i in range(x):
            rand = random.randint(0, 2) - 1
            value = value + rand
            if rand == -1:
                d.append('-')
            elif rand == 1:
                d.append('+')
            else:
                d.append(rand)
    elif y == 0:
        raise AssertionError()
    else:
        for i in range(x):
            rand = random.randint(1, y)
            d.append(rand)
            value = value + rand
    s = [x, 'd', y, '=', value]
    d.append(''.join(map(str, s)))
    dices.append(d)
    return value


def calc_expr(expr, dices, judge=None):
    if judge is None:
        judge = []
    tokens = split_tokens(expr)
    postfix = convert_expr(tokens)
    val = postfix_eval(postfix, dices, judge)
    return val


app = commands.Bot(command_prefix='!')


@app.event
async def on_ready():
    print(f'{app.user} has connected to Discord!')
    await app.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.listening, name="!다이스"))
    active_servers = app.guilds
    for guild in active_servers:
        print(guild.name)


async def make_character(ctx):
    dices = []
    embed_message = discord.Embed(title=f":game_die: CoC 7th 캐릭터 메이킹", color=0xff8400)
    embed_message.add_field(name="플레이어", value=ctx.message.author.mention, inline=False)

    embed_message.add_field(name="근력", value=calc_expr('3d6*5', dices), inline=True)
    embed_message.add_field(name="민첩", value=calc_expr('3d6*5', dices), inline=True)
    embed_message.add_field(name="정신", value=calc_expr('3d6*5', dices), inline=True)
    embed_message.add_field(name="건강", value=calc_expr('3d6*5', dices), inline=True)
    embed_message.add_field(name="외모", value=calc_expr('3d6*5', dices), inline=True)

    embed_message.add_field(name="교육", value=calc_expr('(2d6+6)*5', dices), inline=True)
    embed_message.add_field(name="크기", value=calc_expr('(2d6+6)*5', dices), inline=True)
    embed_message.add_field(name="지능", value=calc_expr('(2d6+6)*5', dices), inline=True)

    embed_message.add_field(name="행운", value=calc_expr('3d6*5', dices), inline=True)

    embed_message.add_field(name="주사위 목록",
                            value='\n'.join(map(str, dices)), inline=True)
    await ctx.send(embed=embed_message)


async def roll_dice(ctx, query):
    try:
        dices = []
        judge = []
        result = calc_expr(query
                           .replace('<=', '#')
                           .replace('>=', '$')
                           , dices, judge)
        if len(str(result)) > 240:
            raise AssertionError()
        if type(result) is bool:
            if result:
                embed_message = discord.Embed(title=":game_die: 결과 : 성공!", color=0xff8400)
            else:
                embed_message = discord.Embed(title=":game_die: 결과 : 실패!", color=0xff8400)
        else:
            embed_message = discord.Embed(title=f":game_die: 결과: {result}", color=0xff8400)

        embed_message.add_field(name="플레이어", value=ctx.message.author.mention, inline=False)
        if len(judge) > 0:
            embed_message.add_field(name="판정 목록",
                                    value='\n'.join(map(str, judge)), inline=False)
        if len(dices) > 0:
            embed_message.add_field(name="주사위 목록",
                                    value='\n'.join(map(str, dices)), inline=False)
        if len(embed_message) > 960:
            embed_message = discord.Embed(title=f":game_die: 결과: {result}", color=0xff8400)
            embed_message.add_field(name="플레이어", value=ctx.message.author.mention, inline=False)
            embed_message.add_field(name="주사위 목록",
                                    value='\n'.join([item[-1] for item in dices]), inline=False)
    except AssertionError:
        embed_message = discord.Embed(title=f":warning: 주사위 값이 잘못되었습니다",
                                      description='주사위의 개수나 값을 조절해 주세요.', color=0xff8400)
    except IndexError as ie:
        embed_message = discord.Embed(title=f":warning: 명령어에 문제가 있습니다.",
                                      description='주사위를 여러 개 굴리시는 경우 각 주사위마다 몇개의 주사위를 굴 적어주세요.', color=0xff8400)
    except Exception as e:
        embed_message = discord.Embed(title=f":x: 지원하지 않는 명령어입니다.",
                                      description=str(e), color=0xff8400)
    await ctx.send(embed=embed_message)


@app.command(name='다이스')
async def help_message(ctx):
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
                                  'ex> `!ruse https://docs.google.com/spreadsheets/d/1ZzXjzplwt3lSnNNsrnQfrPtmUsHvEfgxK31XWEa2lWA \"조 종사(Niq)\"`'
                                  '\n'
                                  '`!rr [판정이름]`으로 등록한 탐사자 특성/기능치 판별을 빠르게 할 수 있습니다.'
                                  'ex> `!rr 심리학`'
                                  '\n'
                                  '`!rstat`으로 등록한 탐사자 이름과 시트 링크를 확인 할 수 있습니다.'
                                  '\n'
                                  '`!rreset`으로 등록한 탐사자를 해제할 수 있습니다.'
                                  ,
                                  color=0xff8400)
    await ctx.send(embed=embed_message)


@app.command(name='r', pass_context=True)
async def r(ctx, *args):
    await roll(ctx, *args)


@app.command(name='roll', pass_context=True)
async def roll(ctx, *args):
    query = ''.join(args)
    print(' '.join([ctx.message.author.mention, 'query', query]))
    if args[0] == 'ccc':
        await make_character(ctx)
    else:
        await roll_dice(ctx, query)


# ----


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


def roll_sheet(worksheet: gspread.Worksheet, target):
    value = dice(1, 100, [])
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
async def roll2(ctx, *args):
    if ctx.author in player:
        sheet = player[ctx.author]
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
async def use_sheet(ctx, *args):
    try:
        user = ctx.author
        uri = args[0]
        doc = gc.open_by_url(uri)
        sheet_name = args[1]
        sheet = doc.worksheet(sheet_name)
        docs[user] = doc
        player[user] = sheet
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
async def add_sheet(ctx):
    try:
        if ctx.author in player:
            del player[ctx.author]
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
async def stat_sheet(ctx):
    try:
        if ctx.author in player:
            sheet = player[ctx.author]
            embed_message = discord.Embed(title=f"현재 사용하고 있는 탐사자는 \"{sheet.acell('E7').value}\"입니다.", description=f"플레이어: {ctx.author.mention}",
                                          color=0xff8400)
            embed_message.add_field(name="시트링크", value=docs[ctx.author].url + ' # ' +sheet.title, inline=False)
            await ctx.send(embed=embed_message)
        else:
            embed_message = discord.Embed(title=f"등록된 탐사자가 없습니다.", description=f"플레이어 : {ctx.author.mention}",
                                          color=0xff8400)
            await ctx.send(embed=embed_message)
    except Exception as e:
        embed_message = discord.Embed(title=f":x: 명령을 수행하는데 실패했습니다.", description=str(e), color=0xff8400)
        await ctx.send(embed=embed_message)


app.run(open("./TOKEN").readline())