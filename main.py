import io
import datetime
import requests
import streamlit as st
import pandas as pd

# ページの基本設定
st.set_page_config(page_title="mini toto-A組 予想・投資シミュレーター", page_icon="⚽", layout="wide")

st.title("⚽ mini toto-A組 予想・投資ナビゲーター")
st.caption("A組（前半5試合）に特化し、開催回の波乱度診断と『厚張り（複数口買い）』戦略で回収率を最大化する実戦ツール。")

# --- 締切カウントダウン ---
DEADLINE = datetime.datetime(2026, 9, 12, 17, 50, 0)
now = datetime.datetime.now()
remaining = DEADLINE - now

if remaining.total_seconds() > 0:
    total_sec = int(remaining.total_seconds())
    rem_days = total_sec // 86400
    rem_hours = (total_sec % 86400) // 3600
    rem_mins = (total_sec % 3600) // 60
    time_text = f"{rem_days}日 {rem_hours}時間 {rem_mins}分" if rem_days > 0 else f"{rem_hours}時間 {rem_mins}分"
    st.warning(f"⏳ **第1653回 mini toto 販売締切（ネット決済）まで：あと {time_text}** （締切: 9/12 17:50）")
else:
    st.error("⚠️ 第1653回 toto の販売は終了しました。")

# --- スタジアム気象・屋根データベース ---
STADIUM_DB = {
    "水戸": {"lat": 36.345, "lon": 140.412, "name": "水戸信ス", "roof": False},
    "清水": {"lat": 34.985, "lon": 138.531, "name": "アイスタ", "roof": False},
    "G大阪": {"lat": 34.809, "lon": 135.543, "name": "パナスタ", "roof": False},
    "町田": {"lat": 35.678, "lon": 139.715, "name": "MUFG国立", "roof": False},
    "長崎": {"lat": 32.837, "lon": 129.980, "name": "トラスタ", "roof": False},
    "広島": {"lat": 34.398, "lon": 132.453, "name": "Eピース", "roof": False},
    "東京V": {"lat": 35.664, "lon": 139.527, "name": "味スタ", "roof": False},
    "浦和": {"lat": 35.903, "lon": 139.717, "name": "埼玉", "roof": False},
}

DERBIES = [
    ({"清水", "磐田"}, "🔥 静岡ダービー"),
    ({"G大阪", "C大阪"}, "🔥 大阪ダービー"),
    ({"横浜FM", "川崎F"}, "🔥 神奈川ダービー"),
    ({"FC東京", "東京V"}, "🔥 東京ダービー"),
    ({"町田", "横浜FM"}, "🔥 境川決戦"),
]

TOP_SCORERS = {
    "水戸": "渡邉 新太 (5点/得点ランク2位)",
    "横浜FM": "谷村 海那 (5点/得点ランク2位)",
}

FATIGUE_TEAMS = {"川崎F", "町田", "G大阪", "名古屋"}
SUSPENDED_PLAYERS = {
    "清水": "住吉 ジェラニレショーン (主力CB)",
}
LINEUP_ALERTS = {
    "FC東京": "主力MFが急遽ベンチスタート",
    "横浜FM": "主力DFが欠場",
}

# --- 気象API ---
@st.cache_data(ttl=1800)
def fetch_weather(home_team):
    info = STADIUM_DB.get(home_team, {"lat": 35.68, "lon": 139.76, "name": "会場", "roof": False})
    url = f"https://api.open-meteo.com/v1/forecast?latitude={info['lat']}&longitude={info['lon']}&daily=precipitation_probability_max,weather_code&timezone=Asia%2FTokyo"
    try:
        res = requests.get(url, timeout=5).json()
        daily = res.get("daily", {})
        prob_list = daily.get("precipitation_probability_max", [20])
        prob = prob_list[0] if prob_list else 20
        is_rain = (prob >= 50) and (not info["roof"])
        weather_icon = "☔ 雨" if prob >= 50 else ("☁️ 曇" if prob >= 30 else "☀️ 晴")
        weather_desc = f"{weather_icon} ({prob}%) 🏟️ 屋根あり" if info["roof"] else f"{weather_icon} ({prob}%)"
        return {"desc": weather_desc, "is_rain": is_rain, "roof": info["roof"], "stadium": info["name"]}
    except Exception:
        return {"desc": "☀️ 晴れ (推定)", "is_rain": False, "roof": info.get("roof", False), "stadium": info.get("name", "会場")}

# --- J1順位表自動取得 ---
@st.cache_data(ttl=3600)
def fetch_jleague_standings():
    url = "https://soccer.yahoo.co.jp/jleague/category/j1/standings"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        tables = pd.read_html(io.StringIO(res.text))
        if tables:
            return tables[0]
    except Exception:
        pass
    return None

df_standings = fetch_jleague_standings()
team_dict = {}
if df_standings is not None:
    for _, row in df_standings.iterrows():
        t_name = str(row.get("チーム名", "")).strip()
        r_val = row.get("順位", 10)
        p_val = row.get("勝点", 10)
        try:
            r_int = int(r_val)
        except:
            r_int = 10
        try:
            p_int = int(p_val)
        except:
            p_int = 10
        if t_name:
            team_dict[t_name] = {"rank": r_int, "pts": p_int}

def get_team_info(name):
    for k, v in team_dict.items():
        if name in k or k in name:
            return v
    return {"rank": 14, "pts": 7}

# 第1653回 mini toto-A組（第1〜5試合）
raw_matches = [
    {"no": 1, "home": "水戸", "away": "川崎F"},
    {"no": 2, "home": "清水", "away": "福岡"},
    {"no": 3, "home": "G大阪", "away": "FC東京"},
    {"no": 4, "home": "町田", "away": "横浜FM"},
    {"no": 5, "home": "長崎", "away": "名古屋"},
]

# --- 勝率計算関数 ---
def calculate_match_prediction(h_name, a_name, is_rain=False, check_lineup=True, style="バランス"):
    h_info = get_team_info(h_name)
    a_info = get_team_info(a_name)
    pair = {h_name, a_name}
    derby_title = None
    for d_set, d_name in DERBIES:
        if d_set == pair:
            derby_title = d_name
            break

    h_scorer = TOP_SCORERS.get(h_name, None)
    a_scorer = TOP_SCORERS.get(a_name, None)
    scorer_h = 1.5 if h_scorer else 0.0
    scorer_a = 1.5 if a_scorer else 0.0

    h_fat = -1.5 if h_name in FATIGUE_TEAMS else 0.0
    a_fat = -1.5 if a_name in FATIGUE_TEAMS else 0.0

    h_susp = -1.8 if h_name in SUSPENDED_PLAYERS else 0.0
    a_susp = -1.8 if a_name in SUSPENDED_PLAYERS else 0.0

    lineup_h = -2.2 if (check_lineup and h_name in LINEUP_ALERTS) else 0.0
    lineup_a = -2.2 if (check_lineup and a_name in LINEUP_ALERTS) else 0.0

    rank_diff = a_info["rank"] - h_info["rank"]
    pts_diff = h_info["pts"] - a_info["pts"]
    home_adv = 2.5
    draw_bonus = 3.0 if is_rain else 0.0
    derby_factor = 0.5 if derby_title else 1.0

    h_score = 10.0 + (rank_diff * 0.4 * derby_factor) + (pts_diff * 0.3 * derby_factor) + home_adv + scorer_h + h_fat + h_susp + lineup_h
    a_score = 10.0 - (rank_diff * 0.4 * derby_factor) - (pts_diff * 0.3 * derby_factor) + scorer_a + a_fat + a_susp + lineup_a
    d_score = 7.5 + draw_bonus

    h_score = max(h_score, 1.0)
    a_score = max(a_score, 1.0)
    total = h_score + a_score + d_score

    h_p = round(h_score / total, 2)
    a_p = round(a_score / total, 2)
    d_p = round(1.0 - (h_p + a_p), 2)

    choices = [
        {"mark": "1", "prob": h_p},
        {"mark": "0", "prob": d_p},
        {"mark": "2", "prob": a_p}
    ]
    if style == "大穴・波乱狙い（高配当）":
        for c in choices:
            c["calc_score"] = c["prob"] * (0.70 if c["mark"] == "1" else 1.30)
        choices = sorted(choices, key=lambda x: x["calc_score"], reverse=True)
    else:
        choices = sorted(choices, key=lambda x: x["prob"], reverse=True)

    c1, c2, c3 = choices
    p1, p2, p3 = sorted([h_p, d_p, a_p], reverse=True)
    uncertainty = p1 - p2
    if derby_title:
        uncertainty -= 0.10
    if is_rain:
        uncertainty -= 0.05

    return {
        "home": h_name, "away": a_name, "home_rank": h_info["rank"], "away_rank": a_info["rank"],
        "home_p": h_p, "draw_p": d_p, "away_p": a_p,
        "first_mark": c1["mark"], "second_mark": c2["mark"],
        "uncertainty": uncertainty, "derby": derby_title,
        "is_rain": is_rain, "h_susp": h_susp, "a_susp": a_susp,
        "lineup_alert": (lineup_h != 0.0 or lineup_a != 0.0)
    }

# --- サイドバー ---
st.sidebar.header("⚙️ 予想・投資設定")
st.sidebar.metric(label="⏳ 投票締切まで", value=time_text if remaining.total_seconds() > 0 else "受付終了")

if st.sidebar.button("🔄 最新データを再取得"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
enable_lineup_check = st.sidebar.checkbox("🚨 直前スタメン速報を反映", value=True)
strategy = st.sidebar.radio("🎯 予想スタイル", ["本命重視（堅実）", "バランス", "大穴・波乱狙い（高配当）"], index=0)

# --- 試合データ構築と波乱度総合診断 ---
matches = []
chaos_score = 0  # 波乱度スコア加算用

for rm in raw_matches:
    w_info = fetch_weather(rm["home"])
    pred = calculate_match_prediction(rm["home"], rm["away"], is_rain=w_info["is_rain"], check_lineup=enable_lineup_check, style=strategy)
    pred["no"] = rm["no"]
    pred["weather"] = w_info["desc"]
    pred["stadium"] = w_info["stadium"]
    matches.append(pred)

    # 波乱要因の加点
    if pred["derby"]:
        chaos_score += 20
    if pred["is_rain"]:
        chaos_score += 15
    if pred["h_susp"] != 0.0 or pred["a_susp"] != 0.0:
        chaos_score += 15
    if pred["lineup_alert"]:
        chaos_score += 15
    if pred["uncertainty"] < 0.10:
        chaos_score += 10  # 実力伯仲カード

chaos_score = min(chaos_score, 100)

# 診断結果の判定
if chaos_score <= 35:
    chaos_level = "🟢 順当・手堅い傾向（低配当濃厚）"
    advice_text = "本命が強く、1等配当は3,000円〜6,000円程度になりやすい回です。買い目を広げずダブル1〜2個に絞り、**同じ組み合わせを【2口〜3口 厚張り】**して受取金額を1万円以上に引き上げるのが最も効果的です！"
    default_multiplier = 2
elif chaos_score <= 65:
    chaos_level = "🟡 バランス傾向（標準配当）"
    advice_text = "1〜2試合に波乱要因がある標準的な回です。無理な厚張りは避け、**【1口買い】**で接戦カードをダブルで手堅くカバーしましょう。"
    default_multiplier = 1
else:
    chaos_level = "🔴 大荒れ警戒（高配当チャンス）"
    advice_text = "ダービーや悪天候・主力不在が重なる大荒れ警戒回です！**厚張り（複数口買い）は厳禁**です。ダブルを多め（3〜4個）に使って高配当（数万円超）の一撃を狙いましょう。"
    default_multiplier = 1

# サイドバー：厚張り口数の設定
st.sidebar.divider()
st.sidebar.subheader("💰 厚張り（複数口購入）設定")
purchase_multiplier = st.sidebar.slider("同じ目を買う口数（厚張り倍率）", min_value=1, max_value=5, value=default_multiplier)

num_double = st.sidebar.slider("ダブル（2択）を使う試合数", min_value=0, max_value=5, value=2)

combinations = (2 ** num_double)
total_cost = combinations * 100 * purchase_multiplier

st.sidebar.metric(label="1パターンあたりの口数", value=f"{purchase_multiplier} 口")
st.sidebar.metric(label="合計購入口数", value=f"{combinations * purchase_multiplier:,} 口")
st.sidebar.metric(label="合計購入金額", value=f"{total_cost:,} 円")

# --- 画面上部：波乱度診断＆投資ナビゲーションバナー ---
st.info(f"### 🎯 今節のA組 総合診断：{chaos_level} （波乱度: {chaos_score}%）\n**💡 戦略ナビ**: {advice_text}")

# ソートとダブル割り当て
sorted_matches = sorted(matches, key=lambda x: x["uncertainty"])
double_nos = [m["no"] for m in sorted_matches[:num_double]]

# --- 予想結果と照合シート ---
st.subheader("📋 第1653回 mini toto-A組 推奨買い目")

results = []

for m in matches:
    is_1_checked = False
    is_0_checked = False
    is_2_checked = False

    if m["no"] in double_nos:
        buy_type = "🟡 ダブル (2択)"
        mark_a, mark_b = sorted([m["first_mark"], m["second_mark"]])
        selection = f"【{mark_a}】 【{mark_b}】"
        if mark_a == "1" or mark_b == "1":
            is_1_checked = True
        if mark_a == "0" or mark_b == "0":
            is_0_checked = True
        if mark_a == "2" or mark_b == "2":
            is_2_checked = True
    else:
        buy_type = "⚪ シングル (1点)"
        selection = f"【{m['first_mark']}】"
        is_1_checked = (m["first_mark"] == "1")
        is_0_checked = (m["first_mark"] == "0")
        is_2_checked = (m["first_mark"] == "2")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**第{m['no']}試合** @ {m['stadium']}")
        st.write(f"🏠 **{m['home']}** ({m['home_rank']}位) vs 🚩 **{m['away']}** ({m['away_rank']}位)")
        if m["derby"]:
            st.error(m["derby"])
        st.caption(f"天候: {m['weather']}")
    with col2:
        st.write(f"勝率予想: **{int(m['home_p']*100)}%** | 【0】 **{int(m['draw_p']*100)}%** | **{int(m['away_p']*100)}%**")
        st.caption(f"購入枠: {buy_type}")
    with col3:
        st.info(f"買い目: **{selection}**")

    results.append({
        "試合番号": f"第{m['no']}試合", "対戦カード": f"{m['home']} vs {m['away']}",
        "購入タイプ": buy_type, "マーク": selection,
        "is_1": is_1_checked, "is_0": is_0_checked, "is_2": is_2_checked
    })
    st.divider()

# --- 打ち間違い防止・楽天toto照合シート ---
st.subheader("👀 打ち間違い防止：楽天toto 照合用マークシート")
st.markdown(f"楽天totoの購入画面で、以下のマークにチェックを入れ、口数欄に **【 各 {purchase_multiplier} 口 】** と入力してください。")

st.link_button("🛒 楽天toto 公式購入画面を開く", "https://toto.rakuten.co.jp/")

sheet_rows = []
for r in results:
    sheet_rows.append({
        "試合": r["試合番号"], "対戦カード": r["対戦カード"], "購入枠": r["購入タイプ"],
        " ホーム勝ち ": "🟥【 1 】" if r["is_1"] else " ( 1 ) ",
        " [0] その他(引分) ": "🟩【 0 】" if r["is_0"] else " ( 0 ) ",
        " アウェイ勝ち ": "🟦【 2 】" if r["is_2"] else " ( 2 ) ",
    })
df_verification = pd.DataFrame(sheet_rows)
st.dataframe(df_verification, use_container_width=True, hide_index=True)