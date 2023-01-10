from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from utils.sql_commander import get_solar_panel_types
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from geopandas import GeoDataFrame

# import contextily as cx

plt.switch_backend("Agg")


class Bottons:
    def __init__(self) -> None:
        self.continue_report_markup = self._bottonrize_selection_talbe(
            (("confirm", "確認"), ("continue", "繼續"), ("cancel", "取消"))
        )
        self.panel_types_markup = self._bottonrize_selection_talbe(
            get_solar_panel_types(), add_index=True
        )
        self.org_markup = self._bottonrize_selection_talbe(
            (("hab", "棲地組"), ("chiqu", "七股站"), ("parttime", "點工"))
        )
        self.signup_markup = self._bottonrize_selection_talbe(
            (("signup", "確認送出"), ("cancel", "取消申請"))
        )
        self.announce_markup = self._bottonrize_selection_talbe(
            (("send", "確認公告"), ("cancel", "取消公告"))
        )

    def unauth_appliers(self, sql_result):
        return ReplyKeyboardMarkup(
            [["%s (%s) %s" % (name, org, tg_id)] for tg_id, name, org in sql_result],
            resize_keyboard=True,
        )

    def _bottonrize_selection_talbe(self, sql_result, add_index=False) -> dict:
        botton_dict = {}

        for type_id, panel_type in sql_result:
            if not add_index:
                botton_dict[panel_type] = type_id
            else:
                botton_dict["%s.%s" % (type_id, panel_type)] = type_id
        return self._markup_maker(botton_dict)

    def _markup_maker(self, botton_dict: dict):
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(key, callback_data=value)
                    for key, value in botton_dict.items()
                ]
            ]
        )
        return markup


class AdminInfo:
    def __init__(self, title=None, phone_number=None, first_name=None) -> None:
        self.title = title
        self.phone_number = phone_number
        self.first_name = first_name


class BotReply:
    def __init__(self) -> None:
        self.shuyen = AdminInfo(
            title="計畫主持人：黃書彥", phone_number="+886911380312", first_name="shuyen"
        )
        self.hunter = AdminInfo(
            title="計畫助理：林釗輝", phone_number="+886978290319", first_name="釗輝"
        )
        self.chendada = AdminInfo(
            title="系統開發：陳達智", phone_number="+886912957551", first_name="Ta-chih"
        )
        self._COLORS = (
            "lightgray",
            "wheat",
            "lightskyblue",
            "royalblue",
            "limegreen",
            "violet",
        )

        self.question_dict = {
            "location": "請傳送目前的點位。",
            "pond_index": "請選擇圖中魚塭的編號\n(僅需填寫有光電的魚塭編號)",
            "panel_type": "請選擇光電板的類型",
            "end_select": "要結束回報送出了嗎？\n(要按確認或者是取消，本次回報才算結束。)\n確認：送出變更\n繼續：繼續回報\n取消：不送出取消這次回報",
            "orgnization": "請問你的服務單位？",
            "signup": "確認送出申請？",
            "announce_content": "請輸入想公告的內容：",
            "applier": "請選擇你要授權的使用者：",
            "send_announce": "確認要送出公告？\n系統會自動加上署名喔 ^_<",
        }

        self.say_what_dict = {
            "cancel": "已取消。",
            "current_location": "紅點是你目前的位置。",
            "update_done": "已成功回報！",
            "report_cancel": "本次回報已取消。",
            "signup_cancel": "申請已取消。",
            "no_pond_selected": "沒有選取到任何魚塭，請用 /report 再試一次。",
            "no_pond_checked": "沒有選取到任何魚塭。",
            "permission_deny": "您沒有足夠的權限。",
            "signup_sent": "你的申請已送出，請待管理員審核。",
            "no_applier": "沒有待審核的使用者喔。",
            "wrong_id": "請輸入正確的使用者ID，或者是這個使用者已經審核過了。",
            "to_applier_passed": "你的申請已經通過了，可以開始使用回報系統了\n回報前請先詳細閱讀使用說明\n用 /manual 來查看使用說明。",
            "approved_applier": "授權成功！",
            "manual_url": "https://github.com/Chendada-8474/solar-panel-report",
            "panel_type": "1. 無：未設置光電區域，如果填錯了可以用這個選項來返回。\n2. 打樁：地面型光電尚僅只有柱子，未裝置光電板。若只有整地不算在此類，至少需要有一根柱子\n3. 地面型：已裝置光電板之地面型光電(只要有一塊就算)\n4. 水面型：已裝置光電板之水面型光電。",
            "set_name_first": "請先設定 Telegram 帳號的姓名。",
            "approved_applier": "授權成功！",
            "weird_pond_index": "魚塭編號怪怪的喔。",
            "announce_sent": "已公告，公告內容：",
            "announce_cancel": "已取消公告。",
            "auth_cancel": "你可以輸入 'cancel' 來取消授權。",
        }

    def ask(self, question=None) -> str:
        if not question:
            raise Exception("question is needed")
        return self.question_dict[question]

    def say(self, say_what=None) -> str:
        if not say_what:
            raise Exception("say_what is needed")
        return self.say_what_dict[say_what]

    def someone_signup(self, applier, org) -> str:
        return "%s(%s)剛剛送出了申請，請用 /authorize 來授權使用者。" % (applier, org)

    def seleted_applier(self, applier_id) -> str:
        return "你選擇了%s" % applier_id

    def auth_already(self, status="user"):
        text = None
        if status == "admin":
            text = "你已經是管理員了。"
        elif status == "user":
            text = "你已經有使用權限了．。"
        elif status == "applied":
            text = "你的申請已送出，請等待管理員授權。"
        return text

    def selected_org(self, org=None):
        return "選擇了%s" % org

    def selected_ponds_img(self, ponds: GeoDataFrame, observer=None):
        color_list = [
            self._COLORS[int(i) - 1]
            for i in sorted(list(set(ponds["solar_panel_type"])))
        ]
        ponds["solar_panel_type"] = ponds["solar_panel_type"].astype("string")
        ponds.plot(
            figsize=(6, 6),
            column="solar_panel_type",
            legend=True,
            cmap=colors.ListedColormap(color_list),
        )

        if observer:
            plt.plot(observer[0], observer[1], marker="o", markersize=10, color="red")

        for i, row in ponds.iterrows():
            plt.annotate(
                text=str(i),
                size=15,
                xy=(row["centroid_x"], row["centroid_y"]),
                horizontalalignment="center",
            )

        bio = BytesIO()
        bio.name = "ponds.png"
        plt.savefig(bio)
        bio.seek(0)
        plt.close()
        return bio


if __name__ == "__main__":
    from sql_commander import get_ponds_nearby_as_geopandas

    y, x = 23.740711, 120.198713
    ponds = get_ponds_nearby_as_geopandas(x, y)
    ponds.at[3, "solar_panel_type"] = 4
    br = BotReply()
    br.selected_ponds_img(ponds)
