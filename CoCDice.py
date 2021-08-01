import pickle
from typing import Dict

import gspread

import discord
from discord.ext import commands
import global_vars as gv
import StackDice as sd


class CoCDice(commands.Cog):
    def __init__(self, app):
        self.app = app
        self.fixed_sheet_position: Dict[str, str] = {
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

    def get_sheet_value(self, worksheet: gspread.Worksheet, target):
        if target in self.fixed_sheet_position.keys():
            cell = worksheet.acell(self.fixed_sheet_position[target])
            v = int(cell.value)
        else:
            cell = worksheet.find(target)
            row = cell.row
            col = cell.col
            v = int(worksheet.cell(row, col + 4).value)
        return v

    @commands.command(name='rccc', pass_context=True,
                      brief='CoC 7th 탐사자 특성치 굴리기',
                      description='!rccc 명령어 사용법',
                      usage='',
                      help='CoC 7th 탐사자의 생성에 필요한 특성치 주사위를 굴리는 기능입니다.\n')
    async def make_player_sheet(self, ctx: discord.ext.commands.Context):
        gv.logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'rccc']))
        await sd.make_character(ctx)

    @commands.command(name='rr', pass_context=True,
                      brief='CoC 7th 다이스 굴리기',
                      description='!rr 명령어 사용법',
                      usage='[기능/특성치 이름] (주사위 표현식)'
                            '\n!rr 근력'
                            '\n!rr 근접전(격투) +1d6'
                            '\n!rr 기계수리 b1',
                      help='!ruse로 등록한 CoC 7th 시트의 주사위를 굴릴 수 있습니다.\n'
                           '공개된 CoC 7th 판정 기준을 따라 대성공/어려운성공/성공/실패/대실패를 판별합니다.\n'
                           '추가적인 주사위 표현식을 사용하여 판정에 보정을 적용 할 수 있습니다.\n'
                           'b, p 연산을 사용하여 보너스, 페널티 주사위를 적용 할 수 있습니다.\n')
    async def roll2(self, ctx: discord.ext.commands.Context, *args):
        gv.logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'rr', ' '.join(args)]))
        key = str(ctx.guild) + str(ctx.author)
        try:

            if key in gv.player:
                sheet = gv.player[key]
                sheet_value = self.get_sheet_value(sheet, args[0])
                dice_value = sd.dice(1, 100, [])
                dices = [dice_value]
                if len(args) > 1:
                    if str(args[1]).startswith('b'):
                        expr = sd.calc_expr(''.join(args[1:])[1:], dices, [])
                        dice_value = sd.calc_bonus(dice_value, expr, dices)
                    elif str(args[1]).startswith('p'):
                        expr = sd.calc_expr(''.join(args[1:])[1:], dices, [])
                        dice_value = sd.calc_penalty(dice_value, expr, dices)
                    else:
                        expr = str(dice_value) + ''.join(args[1:])
                        dice_value = sd.calc_expr(expr, dices, [])
                jud = sd.judgement(dice_value, sheet_value)
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
            gv.logger.info(e)
            await ctx.send(embed=embed_message)

    @commands.command(name='ruse', pass_context=True,
                      brief='CoC 7th 다이스 굴리기 시트 등록',
                      description='!ruse 명령어 사용법',
                      usage='[시트링크] [시트이름]'
                            '\n!ruse [시트링크별명] [시트이름]'
                            '\n!ruse https://docs.google.com/spreadsheets/d/'
                                  '1CzAo97L-ioGFHo_d8MC64nxAKiLchd-MkixYL4mxjwE 조 종사(Niq)'
                            '\n!ruse 시트링크별명 조 종사(Niq)',
                      help='!rr 명령에 사용할 CoC 7th 시트를 등록하는 명령어입니다.\n'
                           '구글 스프레드 시트의 링크 또는 !radd 명령을 통해 별명이 지정된 시트의 별명을 사용 할 수 있습니다.\n'
                           '등록에 사용할 수 있는 서식은 https://stone-whale.postype.com/post/4912082의 기본 및 now 시트입니다.\n'
                           '등록한 시트는 서버 및 개인별로 별도로 저장됩니다.\n')
    async def use_player_sheet(self, ctx: discord.ext.commands.Context, *args):
        gv.logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'ruse', ' '.join(args)]))
        try:
            user = ctx.author
            guild: discord.guild.Guild = ctx.guild

            uri = args[0]
            key = str(guild) + str(uri)
            if key in gv.pre_docs:
                doc = gv.pre_docs[key]
                sheet_url = gv.data_pre_docs[key]
            else:
                try:
                    doc = gv.gc.open_by_url(uri)
                    sheet_url = uri
                except gspread.exceptions.NoValidUrlKeyFound:
                    raise Exception

            sheet_name = ' '.join(args[1:])
            sheet = doc.worksheet(sheet_name)
            gv.docs[str(guild) + str(user)] = doc
            gv.player[str(guild) + str(user)] = sheet

            gv.data_player[str(guild) + str(user)] = sheet_url + '→' + sheet_name
            pickle.dump(gv.data_player, open("data/sheet_data.txt", "wb"))

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

    @commands.command(name='rreset', pass_context=True,
                      brief='등록된 CoC 7th 시트 해제',
                      description='!rreset 명령어 사용법',
                      usage='',
                      help='!ruse 명령으로 등록한 시트를 해제하는 기능입니다.\n')
    async def reset_player_sheet(self, ctx: discord.ext.commands.Context):
        gv.logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'rreset']))
        key = str(ctx.guild) + str(ctx.author)
        try:
            if key in gv.player:
                del gv.player[key]
                del gv.data_player[key]
                pickle.dump(gv.data_player, open("data/sheet_data.txt", "wb"))
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
            gv.logger.info(e)
            await ctx.send(embed=embed_message)

    @commands.command(name='rstat', pass_context=True,
                      brief='등록된 CoC 7th 시트 확인',
                      description='!rstat 명령어 사용법',
                      usage='',
                      help='!ruse 명령으로 현재 등록된 시트를 확인하는 기능입니다.\n')
    async def stat_player_sheet(self, ctx: discord.ext.commands.Context):
        gv.logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'rstat']))
        try:
            key = str(ctx.guild) + str(ctx.author)
            if key in gv.player:
                sheet = gv.player[key]
                embed_message = discord.Embed(title=f"현재 사용하고 있는 탐사자는 \"{sheet.acell('E7').value}\"입니다.",
                                              description=f"플레이어: {ctx.author.mention}", color=0xff8400)
                embed_message.add_field(name="시트링크", value=gv.docs[key].url + ' # ' + sheet.title, inline=False)
                await ctx.send(embed=embed_message)
            else:
                embed_message = discord.Embed(title=f"등록된 탐사자가 없습니다.", description=f"플레이어 : {ctx.author.mention}",
                                              color=0xff8400)
                await ctx.send(embed=embed_message)
        except Exception as e:
            embed_message = discord.Embed(title=f":x: 명령을 수행하는데 실패했습니다.",
                                          description=f"플레이어 : {ctx.author.mention}", color=0xff8400)
            gv.logger.info(e)
            await ctx.send(embed=embed_message)


class CoCKeeperOnly(commands.Cog):
    def __init__(self, app):
        self.app = app

    @commands.command(name='radd', pass_context=True,
                      brief='CoC 7th 시트링크 별명 설정',
                      description='!radd 명령어 사용법',
                      usage='[시트링크별명] [시트링크]'
                            '\n!radd 테스트용별명 https://docs.google.com/spreadsheets/d/'
                                  '1CzAo97L-ioGFHo_d8MC64nxAKiLchd-MkixYL4mxjwE',
                      help='* 이 기능은 `TRPG 마스터` 역할이 있어야만 사용 가능합니다. *\n'
                           '!ruse 명령어에서 사용가능한 시트링크 별명을 설정 할 수 있습니다.\n'
                           '!radd 명령어로 등록한 시트링크 별명은 !ruse 명령어에서 시트링크와 동일하게 동작합니다.\n')
    async def alias_sheet(self, ctx: discord.ext.commands.Context, *args):
        gv.logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'radd', ' '.join(args)]))
        roles = [role for role in ctx.author.roles if role.name == "TRPG 마스터"]

        name = args[0]
        uri = args[1]

        if len(roles) > 0:
            try:
                guild: discord.guild.Guild = ctx.guild
                doc = gv.gc.open_by_url(uri)
                key = str(guild) + str(name)
                if key in gv.pre_docs.keys():
                    embed_message = discord.Embed(title=f"{name} 이름의 시트 별명은 이미 존재합니다.",
                                                  description=f"마스터 : {ctx.author.mention}", color=0xff8400)
                    embed_message.add_field(name="시트링크", value=gv.pre_docs[key].url, inline=False)
                    await ctx.send(embed=embed_message)
                else:
                    gv.pre_docs[key] = doc
                    gv.data_pre_docs[key] = uri
                    pickle.dump(gv.data_pre_docs, open("data/docs_alias.txt", "wb"))
                    embed_message = discord.Embed(title=f"{name} 시트 별명을 등록했습니다.",
                                                  description=f"마스터 : {ctx.author.mention}", color=0xff8400)
                    embed_message.add_field(name="시트링크", value=gv.pre_docs[key].url, inline=False)
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

    @commands.command(name='rremove', pass_context=True,
                      brief='CoC 7th 시트링크 별명 제거',
                      description='!rremove 명령어 사용법',
                      usage='[시트링크별명]'
                            '\n!rremove 테스트용별명',
                      help='* 이 기능은 `TRPG 마스터` 역할이 있어야만 사용 가능합니다. *\n'
                           '!radd 명령어로 등록한 시트링크 별명을 제거하는 기능입니다.\n')
    async def remove_sheet(self, ctx: discord.ext.commands.Context, *args):
        gv.logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'rremove', ' '.join(args)]))
        roles = [role for role in ctx.author.roles if role.name == "TRPG 마스터"]

        name = args[0]
        if len(roles) > 0:
            guild: discord.guild.Guild = ctx.guild
            key = str(guild) + str(name)
            if key in gv.pre_docs.keys():
                del gv.pre_docs[key]
                del gv.data_pre_docs[key]
                pickle.dump(gv.data_pre_docs, open("data/docs_alias.txt", "wb"))
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

    @commands.command(name='rclear', pass_context=True,
                      brief='등록된 CoC 7th 시트 전체 해제',
                      description='!rclear 명령어 사용법',
                      usage=''
                            '\n!rclear 테스트용별명',
                      help='* 이 기능은 `TRPG 마스터` 역할이 있어야만 사용 가능합니다. *\n'
                           '!ruse 명령어로 등록된 시트를 전부 등록 해제하는 기능입니다.\n'
                           '* 현재 서버에서 !ruse 명령어로 등록된 모든 시트를 해제하므로 주의하시기 바랍니다. *\n')
    async def clear_player_sheet(self, ctx: discord.ext.commands.Context):
        gv.logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'rclear']))
        roles = [role for role in ctx.author.roles if role.name == "TRPG 마스터"]

        if len(roles) > 0:

            deleted_user = []
            for pl in gv.player:
                if pl.startswith(str(ctx.guild)):
                    deleted_user.append(pl)
            message = []
            for du in deleted_user:
                message.append(gv.player[du].title)
                del gv.player[du]
                del gv.data_player[du]

            if len(message) > 0:
                pickle.dump(gv.data_player, open("data/sheet_data.txt", "wb"))
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