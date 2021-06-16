from oauth2client.service_account import ServiceAccountCredentials

TOKEN = "DISCORDTOKEN"
credentials = ServiceAccountCredentials.from_json_keyfile_name("dicebot-key.json")