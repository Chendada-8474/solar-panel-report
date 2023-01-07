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
        self.color_dict = {}
        # self.color_dict_from(get_solar_panel_types())

    # def color_dict_from(self, sql_result):
    #     color_dict = {}
    #     for i, p in enumerate(sql_result):
    #         color_dict[str(p[0])] = self._COLORS[i]
    #     self.color_dict = color_dict

    def ask(self, question=None) -> str:
        if not question:
            raise "question is needed"
        if question == "location":
            text = "請傳送目前的點位"
        elif question == "pond_index":
            text = "請選擇圖中魚塭的編號\n(僅需填寫有光電的魚塭編號)"
        elif question == "panel_type":
            text = "請選擇光電板的類型"
        elif question == "end_select":
            text = "要結束回報送出了嗎？\n(要按確認或者是取消，本次回報才算結束。)\n確認：送出變更\n繼續：繼續回報\n取消：不送出取消這次回報"
        elif question == "orgnization":
            text = "請問你的服務單位？"
        elif question == "signup":
            text = "確認送出申請？"
        elif question == "applier":
            text = "請選擇你要授權的使用者。"
        return text

    def current_location(self) -> str:
        return "紅點是你目前的位置。"

    def update_done(self) -> str:
        return "已成功回報！"

    def report_cancel(self) -> str:
        return "本次回報已取消。"

    def signup_cancel(self) -> str:
        return "申請已取消。"

    def no_pond_selected(self) -> str:
        return "沒有選取到任何魚塭，請用 /report 再試一次。"

    def no_pond_checked(self) -> str:
        return "沒有選取到任何魚塭。"

    def permission_deny(self) -> str:
        return "您沒有足夠的權限。"

    def signup_sent(self) -> str:
        return "你的申請已送出，請待管理員審核。"

    def no_applier(self) -> str:
        return "沒有待審核的使用者喔。"

    def seleted_applier(self, applier_id) -> str:
        return "你選擇了%s" % applier_id

    def wrong_id(self) -> str:
        return "請輸入正確的使用者ID，或者是這個使用者已經審核過了。"

    def someone_signup(self, applier, org) -> str:
        return "%s(%s)剛剛送出了申請，請用 /authorize 來授權使用者。" % (applier, org)

    def to_applier_passed(self):
        return "你的申請已經通過了，可以開始使用回報系統了\n回報前請先詳細閱讀使用說明\n用 /manual 來查看使用說明。"

    def approved_applier(self):
        return "授權成功"

    def manual_url(self) -> str:
        return "https://github.com/Chendada-8474/solar-panel-report"

    def panel_type(self) -> str:
        text = """
        1. 無：未設置光電區域，如果填錯了可以用這個選項來返回。\n2. 打樁：地面型光電尚僅只有柱子，未裝置光電板。若只有整地不算在此類，至少需要有一根柱子\n3. 地面型：已裝置光電板之地面型光電(只要有一塊就算)\n4. 水面型：已裝置光電板之水面型光電。
        """
        return text

    def set_name_first(self):
        return "請先設定 Telegram 帳號的姓名。"

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
        return bio


if __name__ == "__main__":
    from sql_commander import get_ponds_nearby_as_geopandas

    y, x = 23.740711, 120.198713
    ponds = get_ponds_nearby_as_geopandas(x, y)
    ponds.at[3, "solar_panel_type"] = 4
    br = BotReply()
    br.selected_ponds_img(ponds)
