# 魚塭太陽能板回報系統使用說明

## 指令列表
`/report` - 開始回報光電魚塭

`/check` - 查看魚塭光電回報情形

`/type` - 光電板類型說明

`/manual` - 使用手冊

`/contact` - 聯絡相關人員

`/signup` - 向管理員申請使用權限

## 首次使用
使用前請到 app store 或者是 Google Play 下載 Telegram 應用程式。
下載後請先在 app 中設定你的姓名，再用 `/signup` 指令來向管理員申請使用權限。


## 搜尋 Telegram Bot 帳號
在 Telegram 上搜尋 “TESRI Solar Panel Report” 。

或者是直接透過連結找到機器人帳號：[t.me/tesri_solar_bot](https://t.me/tesri_solar_bot)。

<img src="./img/search_bot.jpeg" width="300">


## 回報方式

註：如果只是想查看回報狀態，可以使用 `/check` 指令就好。

### 1. 輸入指令
請先輸入 `/report` ，或點選左下角的 menu 選單，點選 `/report` 指令。

<img src="./img/report_command.jpeg" width="300">

<img src="./img/ask_location.jpeg" width="300">

### 2. 傳送點位
傳送你目前的點位，你也可以移動地圖，選擇其他點位。

<img src="./img/select_location.PNG" width="300">

### 3. 輸入魚塭編號
機器人會依照你的回傳點位，回傳點為附近的魚塭，請輸入想要回報的魚塭編號。
你可以一次選擇多個魚塭，魚塭編號可以用任何的非數字符號分開。
例如：
`9,5,2,7`
`9 5 2 7`
`9，5，2，7`
`9.5.2.7`

<img src="./img/send_pond_index.PNG" width="300">

溫馨體醒：在這邊請選擇你看到類型一樣的光電類型魚塭，若有其他類型光電請等等按繼續後回報。

### 4. 選擇光電板類型
請依照你觀察到的類別，按光電板按鈕。按下後你可以選擇送出、繼續回報、或者是取消。

<img src="./img/select_type_and_sent.PNG" width="300">

## 光電板類型說明
光電板回報類型分成 4 種，分別為：無、打樁、地面型、水面型 (如果是堤岸型的光電板不用回報。)。

你也可以使用 `/type` 指令來查看說明。

1. 無：未設置光電區域，如果填錯了可以用這個選項來返回。

2. 打樁：地面型光電尚僅只有柱子，未裝置光電板。若只有整地不算在此類，至少需要有一根柱子

![only_pole](./img/only_pole_solar.jpg)

3. 地面型：已裝置光電板之地面型光電(只要有一塊就算)

![gound](./img/gound_solar.jpg)

4. 水面型：已裝置光電板之水面型光電。

![float](./img/float_solar.jpg)


## 常見 Q & A
#### 如果輸入錯誤了怎麼辦？
你可以按繼續，然後輸入剛剛輸錯魚塭的編號，按 1.無 按紐將該魚塭設定回無回報的狀態。
或者是直接按取消按紐，取消這次的回報。

#### 我需要圖中的每一個魚塭都回報嗎？
不用喔！所有魚塭預設是無，你只需要回報有光電板的魚塭就可以了喔。

## 聯絡管理員
你可以使用 `/contact` 指令來獲得管理員的聯絡資訊。

<img src="./img/contact.jpeg" width="300">