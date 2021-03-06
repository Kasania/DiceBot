import logging
import datetime

from typing import Dict

import pickle

import global_vars as gv

import discord
import keys
from BasicDice import BasicDice
from CoCDice import CoCDice, CoCKeeperOnly
from HelpCommand import HelpCommand
from discord.ext import commands
import gspread

from discord.ext.commands import CommandNotFound

global app


class SpecificFilter(object):
    def __init__(self, level):
        self.__level = level

    def filter(self, log_record):
        return log_record.levelno <= self.__level

if __name__ == '__main__':

    gv.logger = logging.getLogger(__name__)
    gv.logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s : %(message)s', '%Y-%m-%d %H:%M:%S')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    gv.logger.addHandler(console_handler)

    current_time = str(datetime.datetime.now()).replace(' ', '.').replace(':', '.')

    with open('./logs/'+current_time+'.log', 'w') as fp:
        pass
    file_debug_handler = logging.FileHandler(filename='./logs/'+current_time+'.log', encoding='utf-8')
    file_debug_handler.setLevel(logging.INFO)
    file_debug_handler.setFormatter(formatter)
    file_debug_handler.addFilter(SpecificFilter(logging.INFO))

    with open('./logs/'+current_time+'.error', 'w') as fp:
        pass
    file_error_handler = logging.FileHandler(filename='./logs/'+current_time+'.error', encoding='utf-8')
    file_error_handler.setLevel(logging.ERROR)
    file_error_handler.setFormatter(formatter)
    file_debug_handler.addFilter(SpecificFilter(logging.ERROR))

    gv.logger.addHandler(file_debug_handler)
    gv.logger.addHandler(file_error_handler)

    gv.gc = gspread.authorize(keys.credentials)
    gv.data_docs: Dict[str, str] = pickle.load(open('data/docs.txt', 'rb'))
    gv.data_pre_docs: Dict[str, str] = pickle.load(open('data/docs_alias.txt', 'rb'))
    gv.data_player: Dict[str, str] = pickle.load(open('data/sheet_data.txt', 'rb'))
    gv.data_dice_alias: Dict[str, str] = pickle.load(open('data/dice_alias.txt', 'rb'))

    # ???????????? docs
    gv.docs: Dict[str, gspread.Spreadsheet] = {}

    # ????????? ????????? docs
    gv.pre_docs: Dict[str, gspread.Spreadsheet] = {}
    gv.pre_docs_uri: Dict[str, str] = {}
    for key in gv.data_pre_docs.keys():
        gv.pre_docs[key] = gv.gc.open_by_url(gv.data_pre_docs[key])

    # docs ?????? ???????????? ??????
    gv.player: Dict[str, gspread.Worksheet] = {}
    for key in gv.data_player.keys():
        tokens = gv.data_player[key].split('???')
        gv.docs[key] = gv.gc.open_by_url(tokens[0])
        try:
            gv.player[key] = gv.docs[key].worksheet(tokens[1])
        except Exception as e:
            gv.logger.error("sheet load fail" + key)
    # sheet.url + '???' + sheet_name

    # guild:user:alias , query
    gv.dice_alias: Dict[str, str] = {}
    for key in gv.data_dice_alias.keys():
        gv.dice_alias[key] = gv.data_dice_alias[key]

    gv.logger.info('Data load complete')

    app = commands.Bot(command_prefix='!')
    app.add_cog(BasicDice(app))
    app.add_cog(CoCDice(app))
    app.add_cog(CoCKeeperOnly(app))
    app.help_command = HelpCommand()
    app.description = 'Dice ??? ?????????(????????? ?????????: !)'


@app.event
async def on_command_error(ctx, error):
    gv.logger.error(' '.join([str(ctx.guild), ':', str(ctx.author), ":", str(error)]))
    if isinstance(error, CommandNotFound):
        return
    raise error


@app.event
async def on_ready():
    gv.logger.info(f'{app.user} has connected to Discord!')
    await app.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.listening, name="!?????????"))
    active_servers = app.guilds
    gv.logger.info("---Active Server List---")
    for guild in active_servers:
        gv.logger.info(guild.name)
    gv.logger.info(f"- Active Server count : {len(active_servers)} -")


@app.event
async def on_guild_join(guild):
    gv.logger.info('Bot has been added to a new server')
    gv.logger.info(f'Name of server: {guild}')
    gv.logger.info(f"- Active Server count : {len(app.guilds)} -")


@app.event
async def on_guild_remove(guild):
    gv.logger.info('Bot has been removed to a server')
    gv.logger.info(f'Name of server: {guild}')
    gv.logger.info(f"- Active Server count : {len(app.guilds)} -")

app.run(keys.TOKEN)
