from io import BytesIO
import matplotlib.pyplot as plt
from utils.sql_commander import get_solar_panel_types
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from geopandas import GeoDataFrame

# import contextily as cx

plt.switch_backend("Agg")


class Bottons:
    def __init__(self) -> None:
        self.confirm = {"確認": True, "取消": False}
        self.continue_report_markup = self._bottonrize_selection_talbe(
            (("confirm", "確認"), ("continue", "繼續"), ("cancel", "取消"))
        )
        self.panel_types_markup = self._bottonrize_selection_talbe(
            get_solar_panel_types(), add_index=True
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

    def ask(self, question=None) -> str:
        if not question:
            raise "question is needed"
        if question == "location":
            text = "請傳送目前的點位"
        elif question == "pond_index":
            text = "請選擇圖中魚塭的編號"
        elif question == "panel_type":
            text = "請選擇光電板的類型"
        elif question == "end_select":
            text = "要結束回報送出了嗎？\n確認：送出變更\n繼續：繼續回報\n取消：不送出取消這次回報"
        return text

    def update_done(self) -> str:
        return "已成功回報！"

    def report_cancel(self) -> str:
        return "本次回報已取消"

    def no_pond_selected(self) -> str:
        return "沒有選取到任何魚塭，請用 /report 再試一次。"

    def no_pond_checked(self) -> str:
        return "沒有選取到任何魚塭"

    def permission_deny(self) -> str:
        return "您沒有足夠的權限。"

    def selected_ponds_img(self, ponds: GeoDataFrame, observer=None):
        ponds["solar_panel_type"] = ponds["solar_panel_type"].astype("string")
        ponds.plot(figsize=(6, 6), column="solar_panel_type", legend=True)

        if observer:
            plt.plot(
                [observer[0]], [observer[1]], marker="o", markersize=10, color="red"
            )

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
    from utils.sql_commander import get_ponds_nearby_as_geopandas, _coord_trans
    from telegram.ext import ExtBot

    # bot = ExtBot("5073744772:AAErv1yd8S9F-L-h-e7zRlkEyT5e9LbrPJg")
    bt = Bottons()
    print(bt.panel_types_markup)
    print(bt.continue_report)

    # y, x = 23.988668, 120.346779
    # ponds = get_ponds_nearby_as_geopandas(x, y)
    # ponds.at[0, "solar_panel_type"] = 3
    # ponds.at[5, "solar_panel_type"] = 3
    # ponds.at[10, "solar_panel_type"] = 2
    # ponds.at[11, "solar_panel_type"] = 5
    # ponds["solar_panel_type"] = ponds["solar_panel_type"].astype("string")
    # x, y = _coord_trans((x, y))
    # bot.send_photo("348929573", photo=bot_reply.plot_selected_ponds(ponds, (x, y)))
