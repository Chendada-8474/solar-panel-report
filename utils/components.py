from io import BytesIO
import matplotlib.pyplot as plt

# import contextily as cx


class Bottons:
    def __init__(self) -> None:
        self.confirm = {"確認": True, "取消": False}
        self.send = {}


class BotReply:
    def __init__(self) -> None:
        pass

    def permission_deny(self) -> str:
        return "您沒有足夠的權限。"

    def ask_location(self) -> str:
        return "請傳送目前的點位。"

    def ask_pond_index(self) -> str:
        return "請選擇圖中魚塭的編號。"

    def no_pond_selected() -> str:
        return "沒有選取到任何魚塭，請再試一次。"

    def selected_ponds_img(self, ponds, observer=None):
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
    from sql_commander import get_ponds_nearby_as_geopandas, _coord_trans
    from telegram.ext import ExtBot

    bot = ExtBot("5073744772:AAErv1yd8S9F-L-h-e7zRlkEyT5e9LbrPJg")

    bot_reply = BotReply()
    y, x = 23.988668, 120.346779
    ponds = get_ponds_nearby_as_geopandas(x, y)
    ponds.at[0, "solar_panel_type"] = 3
    ponds.at[5, "solar_panel_type"] = 3
    ponds.at[10, "solar_panel_type"] = 2
    ponds.at[11, "solar_panel_type"] = 5
    ponds["solar_panel_type"] = ponds["solar_panel_type"].astype("string")
    x, y = _coord_trans((x, y))
    bot.send_photo("348929573", photo=bot_reply.plot_selected_ponds(ponds, (x, y)))
