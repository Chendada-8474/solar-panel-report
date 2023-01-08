from utils.sql_commander import connection_info
from telegram.ext import ExtBot

TELEGRAM_TOKEN = connection_info["telegram"]["token"]
bot = ExtBot(TELEGRAM_TOKEN)


class GeoMemory:
    def __init__(self):
        self.memory = {}
        self.updates = {}

    def _no_user_alert(self, user_id):
        if user_id not in self.memory:
            raise Exception("init user first")

    def init_user(self, user_id):
        self.memory[user_id] = {}

    def add(self, user_id: str, content, key="undifined"):
        self._no_user_alert(user_id)
        self.memory[user_id][key] = content

    def get(self, user_id, key="undifined"):
        self._no_user_alert(user_id)
        return self.memory[user_id][key]

    def update_mem_panel_type(self, user_id: str, pond_indexes: list, panel_type):
        self._no_user_alert(user_id)
        for i in pond_indexes:
            self.memory[user_id]["ponds"].at[i, "solar_panel_type"] = panel_type

    def init_updates(self, user_id):
        self._no_user_alert(user_id)
        self.updates[user_id] = {}

    def add_updates(self, user_id: str, pond_indexes: list, panel_type):
        self._no_user_alert(user_id)

        if "ponds" not in self.memory[user_id]:
            raise Exception("key ponds should be init first")

        for i in pond_indexes:
            fishpond_id = self.memory[user_id]["ponds"].iloc[i]["fishpond_id"]
            self.updates[user_id][fishpond_id] = panel_type

    def get_updates(self, user_id: str):
        self._no_user_alert(user_id)
        return self.updates[user_id]


def split_pond_indexes(ponds_indexes: str) -> list:
    indexes, tmp = [], []
    ponds_indexes += "_"
    for i in ponds_indexes:
        if i.isdigit():
            tmp.append(i)
        elif tmp:
            indexes.append(int("".join(tmp)))
            tmp = []
    return indexes


def send_message_skip_no_found_chat(user_id: list, announcement: str):
    for i in user_id:
        try:
            bot.send_message(i, announcement)
        except:
            print("chat %s not found when announcing")


if __name__ == "__main__":
    string = "0,.5.1"
    print(split_pond_indexes(string))
