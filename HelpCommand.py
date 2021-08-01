from discord.ext.commands import DefaultHelpCommand

import global_vars as gv


class HelpCommand(DefaultHelpCommand):
    def __init__(self, **options):
        super().__init__(**options)
        self.command_attrs['name'] = '다이스'
        self.command_attrs['help'] = '도움말을 출력합니다.'
        self.no_category = "기본명령어"

    def get_ending_note(self):
        command_name = self.invoked_with
        return f"{self.context.clean_prefix}{command_name} [명령어]를 입력하여 명령어별 상세 도움말을 확인 하실 수 있습니다."

    async def send_bot_help(self, mapping):
        ctx = self.context
        gv.logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'help']))
        await super().send_bot_help(mapping)

    async def send_command_help(self, command):
        ctx = self.context
        gv.logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'help command', str(command)]))
        await super().send_command_help(command)

    async def send_group_help(self, command):
        ctx = self.context
        gv.logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'help group', str(command)]))
        await super().send_group_help(command)

    async def send_cog_help(self, command):
        ctx = self.context
        gv.logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'help cog', str(command)]))
        await super().send_cog_help(command)

    def command_not_found(self, string):
        ctx = self.context
        gv.logger.info(' '.join([str(ctx.guild), ':', str(ctx.author), 'help not found', str(string)]))
        return f'"{string}" 명령어가 존재하지 않습니다.'

