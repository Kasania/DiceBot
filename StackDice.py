import random
import discord
from discord.ext import commands


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
        'f': 7,
        'd': 6,
        'h': 5,
        'l': 5,
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


# TODO: hx -> peek highest x dice
# TODO: lx -> peek lowest x dice
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
        elif token == 'h':
            n1 = val_stack.pop()
            val_stack.pop()
            val_stack.push(peek_high(n1, dices))
        elif token == 'l':
            n1 = val_stack.pop()
            val_stack.pop()
            val_stack.push(peek_low(n1, dices))
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


def peek_high(x, dices: list):
    ddice = dices[-1].copy()
    txt: str = ddice[-1]
    ddice = ddice[:-1]
    ddice.sort(reverse=True)
    sdice = ddice[:x]
    s = [txt.split('=')[0], 'h', str(x), '=', str(sum(sdice))]
    sdice.append(''.join(map(str, s)))
    dices[-1] = sdice
    return sum(sdice[:-1])


def peek_low(x, dices: list):
    ddice = dices[-1].copy()
    txt: str = ddice[-1]
    ddice = ddice[:-1]
    ddice.sort()
    sdice = ddice[:x]
    s = [txt.split('=')[0], 'l', str(x), '=', str(sum(sdice))]
    sdice.append(''.join(map(str, s)))
    dices[-1] = sdice
    return sum(sdice[:-1])


def calc_expr(expr, dices, judge=None):
    if judge is None:
        judge = []
    tokens = split_tokens(expr)
    postfix = convert_expr(tokens)
    val = postfix_eval(postfix, dices, judge)
    return val


async def make_character(ctx: discord.ext.commands.Context):
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


async def roll_dice(ctx: discord.ext.commands.Context, query):
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