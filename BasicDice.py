import pickle

import discord
import StackDice as sd
import global_vars
from discord.ext import commands


class BasicDice(commands.Cog):
    def __init__(self, app):
        self.app = app

    @commands.command(name='r', pass_context=True,
                      brief='기본 주사위 굴림 명령어',
                      description='!r 명령어 사용법',
                      usage='[주사위 표현식]'
                            '\n!r (1d100+4d20h2)>=150',
                      help='[dice expr]에는 사칙연산 및 다이스 연산으로 표현된 주사위 표현식이 사용됩니다.\n'
                           '사용가능한 표현식은 아래와 같습니다.\n'
                           '\n'
                           ' - 사칙연산자(+,-,*,/), 비교연산자(<,>,<=,>=) 및 괄호\n'
                           ' - NdR : N개의 R면체 주사위 굴리기\n'
                           ' - Ndf : N개의 fudge(fate) 주사위 굴리기\n'
                           ' - NdRhX : N개의 R면체 주사위를 굴리고, 값이 높은 순서대로 X개의 주사위만 사용\n'
                           ' - NdRlX : N개의 R면체 주사위를 굴리고, 값이 낮은 순서대로 X개의 주사위만 사용\n'
                           '\n'
                           '각 연산사이에 사칙, 비교연산자를 사용하여 연결할 수 있으며, 비교 연산 후에는 성공/실패에 따라 값이 1/0으로 처리됩니다.\n'
                           'NdRhX 혹은 NdRlX 연산시에 d와 h 사이에 추가적인 연산을 하는 경우, 올바르지 않은 값이 출력될 수 있습니다.')
    async def r(self, ctx: discord.ext.commands.Context, *args):
        query = ''.join(args)
        global_vars.logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'query', query]))
        await sd.roll_dice(ctx, query)

    @commands.command(name='ra', pass_context=True,
                      brief='주사위 표현식 별명 설정',
                      description='!ra 명령어 사용법',
                      usage='[별명] [주사위 표현식]'
                            '\n!ra crit 3d12+4'
                            '\n!ra atk 1d20+6<=',
                      help='자주 사용하는 주사위 표현식에 별명을 지정할 수 있습니다.\n'
                           '별명이 지정된 표현식은 !rt 명령어를 통해 편리하게 굴릴 수 있습니다.\n'
                           '미완성 표현식에도 별명을 지정할 수 있습니다. 단, !rt 명령어에서 미완성된 표현식을 완성해야 합니다.\n'
                           '별명에 띄어쓰기를 사용하는 경우 큰따옴표("")를 통해 묶어주어야 합니다.\n'
                           '등록한 별명은 서버 및 개인별로 별도로 저장됩니다.\n')
    async def alias_dice(self, ctx: discord.ext.commands.Context, *args):
        name = args[0]
        query = ''.join(args[1:])
        key = str(ctx.guild) + str(ctx.author.mention)
        global_vars.logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'dice alias', ''.join(args)]))

        global_vars.dice_alias[key + ":" + name] = query
        global_vars.data_dice_alias[key + ":" + name] = query
        pickle.dump(global_vars.data_dice_alias, open('data/dice_alias.txt', 'wb'))

        embed_message = discord.Embed(title="주사위 별명이 등록되었습니다.")
        embed_message.add_field(name="플레이어", value=ctx.message.author.mention, inline=False)
        embed_message.add_field(name="주사위 별명", value=name, inline=False)
        embed_message.add_field(name="주사위 명령", value=query, inline=False)
        await ctx.send(embed=embed_message)

    @commands.command(name='rt', pass_context=True,
                      brief='별명이 지정된 주사위 표현식 굴리기',
                      description='!rt 명령어 사용법',
                      usage='[별명] (추가 주사위 표현식)'
                            '\n!rt crit'
                            '\n!rt atk 15',
                      help='!ra 명령어로 별명이 지정된 주사위 표현식을 굴립니다.\n'
                           '별명으로 지정된 표현식에 이어서 추가적인 표현식을 입력할 수 있습니다.\n'
                           '별명에 띄어쓰기를 사용한 경우 큰따옴표("")를 통해 묶어주어야 합니다.\n'
                      )
    async def roll_alias_dice_with_addition(self, ctx: discord.ext.commands.Context, *args):
        name = args[0]
        key = str(ctx.guild) + str(ctx.author.mention)
        global_vars.logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'roll alias', ''.join(args)]))
        if key + ":" + name in global_vars.dice_alias.keys():
            await self.r(ctx, global_vars.dice_alias[key + ":" + name] + ''.join(args[1:]))
        else:
            embed_message = discord.Embed(title="존재하지 않는 주사위 별명입니다.")
            await ctx.send(embed=embed_message)

    @commands.command(name='rl', pass_context=True,
                      brief='별명이 지정된 주사위 표현식 목록 출력',
                      description='!rl 명령어 사용법',
                      usage='',
                      help='!ra 명령어로 별명이 지정된 주사위 표현식의 목록을 출력합니다.\n'
                      )
    async def roll_alias_list(self, ctx: discord.ext.commands.Context):
        key = str(ctx.guild) + str(ctx.author.mention)
        global_vars.logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'roll alias list']))
        result = {}
        for alias in global_vars.dice_alias.keys():
            alias0 = str(alias)
            if alias0.startswith(key):
                result[(alias0.replace(key+":", ""))] = global_vars.dice_alias[alias]
        if len(result) > 0:
            embed_message = discord.Embed(title="주사위 표현식 별명 목록")
            embed_message.add_field(name="플레이어", value=ctx.message.author.mention, inline=False)
            for alias in result.keys():
                embed_message.add_field(name=alias, value=result[alias])

            await ctx.send(embed=embed_message)
        else:
            embed_message = discord.Embed(title="등록한 주사위 별명이 없습니다.")
            embed_message.add_field(name="플레이어", value=ctx.message.author.mention, inline=False)
            await ctx.send(embed=embed_message)
