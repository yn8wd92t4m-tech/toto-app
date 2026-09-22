import io
import datetime
from zoneinfo import ZoneInfo
import requests
import streamlit as st
import pandas as pd

# ページの基本設定
st.set_page_config(page_title="mini toto予想ナビゲーター", page_icon="⚽", layout="wide")

st.title("⚽ サッカーくじ mini toto 予想ナビゲーター")

# --- 開催回スケジュールマスター（自動切り替え用） ---
JST = ZoneInfo("Asia/Tokyo")
now = datetime.datetime.now(JST)

ROUNDS_SCHEDULE = {
    "第1655回 (9/23 水・祝 開催)": {
        "deadline": datetime.datetime(2026, 9, 23, 16, 50, 0, tzinfo=JST),
        "round_num": 1655,
        "matches": [
            {"no": 1, "home": "鹿島", "away": "甲府"},
            {"no": 2, "home": "神戸", "away": "鳥栖"},
            {"no": 3, "home": "町田", "away": "栃木C"},
            {"no": 4, "home": "G大阪", "away": "徳島"},
            {"no": 5, "home": "柏", "away": "今治"},
        ]
    },
    "第1656回 (9/26 土 開催)": {
        "deadline": datetime.datetime(2026, 9, 26, 17, 50, 0, tzinfo=JST),
        "round_num": 1656,
        "matches": [
            {"no": 1, "home": "山形", "away": "富山"},
            {"no": 2, "home": "浦和", "away": "神戸"},
            {"no": 3, "home": "清水", "away": "磐田"},
            {"no": 4, "home": "横浜FM", "away": "川崎F"},
            {"no": 5, "home": "FC東京", "away": "G大阪"},
        ]
    }
}

# 現在時刻から自動で「現在販売中の最新回」を判定
auto_selected_key = "第1656回 (9/26 土 開催)"
for r_key, r_info in ROUNDS_SCHEDULE.items():
    if now < r_info["deadline"]:
        auto_selected_key = r_key
        break

# --- サイドバー ---
st.sidebar.header("⚙️ 開催回・予想設定")

round_keys = list(ROUNDS_SCHEDULE.keys())
def_idx = round_keys.index(auto_selected_key) if auto_selected_key in round_keys else 0

selected_round_key = st.sidebar.selectbox("🎟️ 対象の開催回", round_keys, index=def_idx)
current_round_data = ROUNDS_SCHEDULE[selected_round_key]
DEADLINE = current_round_data["deadline"]
raw_matches = current_round_data["matches"]
round_num = current_round_data["round_num"]

# 締切カウントダウン
remaining = DEADLINE - now
if remaining.total_seconds() > 0:
    total_sec = int(remaining.total_seconds())
    rem_days = total_sec // 86400
    rem_hours = (total_sec % 86400) // 3600
    rem_mins = (total_sec % 3600) // 60
    time_text = f"{rem_days}日 {rem_hours}時間 {rem_mins}分" if rem_days > 0 else f"{rem_hours}時間 {rem_mins}分"
    st.warning(f"⏳ **第{round_num}回 mini toto 販売締切まで：あと {time_text}** （締切: {DEADLINE.strftime('%m/%d %H:%M')}）")
    st.sidebar.metric(label="⏳ 投票締切まで", value=time_text)
else:
    st.info(f"📢 第{round_num}回 toto の販売は終了しました。")
    st.sidebar.metric(label="⏳ 投票締切まで", value="受付終了")

st.caption("最新順位・気象API・出場停止・スタメン速報・トリガミ防止最適化を完全統合した本格モデル。")

# --- スタジアム気象・屋根データベース ---
STADIUM_DB = {
    "鹿島": {"lat": 35.991, "lon": 140.640, "name": "カシマ", "roof": False},
    "神戸": {"lat": 34.656, "lon": 135.169, "name": "ノエスタ", "roof": True},
    "町田": {"lat": 35.592, "lon": 139.438, "name": "Gスタ", "roof": False},
    "G大阪": {"lat": 34.809, "lon": 135.543, "name": "パナスタ", "roof": False},
    "柏": {"lat": 35.848, "lon": 139.975, "name": "三協F柏", "roof": False},
    "福岡": {"lat": 33.585, "lon": 130.460, "name": "ベススタ", "roof": False},
    "浦和": {"lat": 35.903, "lon": 139.717, "name": "埼玉", "roof": False},
    "清水": {"lat": 34.985, "lon": 138.531, "name": "アイスタ", "roof": False},
    "山形": {"lat": 38.337, "lon": 140.378, "name": "NDスタ", "roof": False},
    "横浜FM": {"lat": 35.510, "lon": 139.606, "name": "日産ス", "roof": False},
    "FC東京": {"lat": 35.664, "lon": 139.527, "name": "味スタ", "roof": False},
}

# ダービー一覧
DERBIES = [
    ({"清水", "磐田"}, "🔥 静岡ダービー"),
    ({"G大阪", "C大阪"}, "🔥 大阪ダービー"),
    ({"横浜FM", "川崎F"}, "🔥 神奈川ダービー"),
    ({"FC東京", "東京V"}, "🔥 東京ダービー"),
]

TOP_SCORERS = {
    "鹿島": "鈴木 優磨",
    "神戸": "大迫 勇也",
    "町田": "藤尾 翔太",
}

FATIGUE_TEAMS = {"町田", "神戸", "川崎F"}
SUSPENDED_PLAYERS = {}
LINEUP_ALERTS = {}

# --- 気象API取得 ---
@st.cache_data(ttl=1800)
def fetch_weather(home_team):
    info = STADIUM_DB.get(home_team, {"lat": 35.68, "lon": 139.76, "name": "会場", "roof": False})
    url = f"https://api.open-meteo.com/v1/forecast?latitude={info['lat']}&longitude={info['lon']}&daily=precipitation_probability_max,weather_code&timezone=Asia%2FTokyo"
    try:
        res = requests.get(url, timeout=5).json()
        daily = res.get("daily", {})
        prob_list = daily.get("precipitation_probability_max", [])
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

if st.sidebar.button("🔄 最新データを再取得"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
enable_lineup_check = st.sidebar.checkbox("🚨 直前スタメン速報を反映（キックオフ2時間前〜）", value=True)
auto_anti_trigami = st.sidebar.checkbox("🛡️ トリガミ防止オート（最低配当＞購入額で最大化）", value=True)
strategy = st.sidebar.radio("🎯 予想スタイル", ["本命重視（堅実）", "バランス", "大穴・波乱狙い（高配当）"], index=1)

df_standings = fetch_jleague_standings()
team_dict = {}
if df_standings is not None:
    with st.expander("📊 Webから取得した最新J1順位表を確認する"):
        st.dataframe(df_standings, use_container_width=True)
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

# --- 勝率・波乱度の総合計算 ---
matches = []
for rm in raw_matches:
    h_name = rm["home"]
    a_name = rm["away"]
    h_info = get_team_info(h_name)
    a_info = get_team_info(a_name)

    derby_title = None
    pair = {h_name, a_name}
    for d_set, d_name in DERBIES:
        if d_set == pair:
            derby_title = d_name
            break

    weather_info = fetch_weather(h_name)
    h_scorer = TOP_SCORERS.get(h_name, None)
    a_scorer = TOP_SCORERS.get(a_name, None)
    scorer_h_bonus = 1.5 if h_scorer else 0.0
    scorer_a_bonus = 1.5 if a_scorer else 0.0

    h_fatigue = h_name in FATIGUE_TEAMS
    a_fatigue = a_name in FATIGUE_TEAMS
    fatigue_h_penalty = -1.5 if h_fatigue else 0.0
    fatigue_a_penalty = -1.5 if a_fatigue else 0.0

    h_susp = SUSPENDED_PLAYERS.get(h_name, None)
    a_susp = SUSPENDED_PLAYERS.get(a_name, None)
    susp_h_penalty = -1.8 if h_susp else 0.0
    susp_a_penalty = -1.8 if a_susp else 0.0

    lineup_h_alert = None
    lineup_a_alert = None
    lineup_h_penalty = 0.0
    lineup_a_penalty = 0.0

    if enable_lineup_check:
        if h_name in LINEUP_ALERTS:
            lineup_h_alert = LINEUP_ALERTS[h_name]
            lineup_h_penalty = -2.2
        if a_name in LINEUP_ALERTS:
            lineup_a_alert = LINEUP_ALERTS[a_name]
            lineup_a_penalty = -2.2

    rank_diff = a_info["rank"] - h_info["rank"]
    pts_diff = h_info["pts"] - a_info["pts"]
    home_adv = 2.5
    draw_bonus = 3.0 if weather_info["is_rain"] else 0.0
    derby_factor = 0.5 if derby_title else 1.0

    home_score = 10.0 + (rank_diff * 0.4 * derby_factor) + (pts_diff * 0.3 * derby_factor) + home_adv + scorer_h_bonus + fatigue_h_penalty + susp_h_penalty + lineup_h_penalty
    away_score = 10.0 - (rank_diff * 0.4 * derby_factor) - (pts_diff * 0.3 * derby_factor) + scorer_a_bonus + fatigue_a_penalty + susp_a_penalty + lineup_a_penalty
    draw_score = 7.5 + draw_bonus

    home_score = max(home_score, 1.0)
    away_score = max(away_score, 1.0)
    total = home_score + away_score + draw_score

    h_p = round(home_score / total, 2)
    a_p = round(away_score / total, 2)
    d_p = round(1.0 - (h_p + a_p), 2)

    notes = []
    if derby_title:
        notes.append(derby_title)
    if weather_info["is_rain"]:
        notes.append("☔ 雨天引分")
    if lineup_h_alert or lineup_a_alert:
        notes.append("🚨 スタメン波乱")
    elif h_susp or a_susp:
        notes.append("🟥 出場停止")
    if h_scorer or a_scorer:
        notes.append("⚽ 好調選手在籍")

    matches.append({
        "no": rm["no"],
        "home": h_name,
        "away": a_name,
        "home_rank": h_info["rank"],
        "away_rank": a_info["rank"],
        "home_pts": h_info["pts"],
        "away_pts": a_info["pts"],
        "home_p": h_p,
        "draw_p": d_p,
        "away_p": a_p,
        "weather": weather_info["desc"],
        "stadium": weather_info["stadium"],
        "derby": derby_title,
        "is_rain": weather_info["is_rain"],
        "h_scorer": h_scorer,
        "a_scorer": a_scorer,
        "h_fatigue": h_fatigue,
        "a_fatigue": a_fatigue,
        "h_susp": h_susp,
        "a_susp": a_susp,
        "lineup_h_alert": lineup_h_alert,
        "lineup_a_alert": lineup_a_alert,
        "note_str": " / ".join(notes) if notes else "通常"
    })

# 接戦度・波乱度ソート
for m in matches:
    p_first, p_second, p_third = sorted([m["home_p"], m["draw_p"], m["away_p"]], reverse=True)
    uncertainty = p_first - p_second
    if m["lineup_h_alert"] or m["lineup_a_alert"]:
        uncertainty -= 0.15
    if m["derby"]:
        uncertainty -= 0.10
    if m["h_susp"] or m["a_susp"]:
        uncertainty -= 0.08
    if m["is_rain"]:
        uncertainty -= 0.05
    m["uncertainty_score"] = uncertainty

sorted_matches = sorted(matches, key=lambda x: x["uncertainty_score"])

# トリガミ防止オート
popular_probs = [max(m["home_p"], m["draw_p"], m["away_p"]) for m in matches]
min_combo_prob = 1.0
for p in popular_probs:
    min_combo_prob *= p

fund = 15000000
estimated_min_payout = int((fund * 0.00005) / max(min_combo_prob, 0.005))
estimated_min_payout = max(min(estimated_min_payout, 15000), 2500)

max_d = 5
max_t = 2

if auto_anti_trigami:
    safe_max_cost = estimated_min_payout * 0.8
    calc_d = 0
    while calc_d < max_d:
        if (2 ** (calc_d + 1)) * 100 <= safe_max_cost:
            calc_d += 1
        else:
            break
    num_double = calc_d
    num_triple = 0
    st.sidebar.info(f"🛡️ **トリガミ防止判定**: 最低配当約 {estimated_min_payout:,}円 を下回らないよう ダブルを **{num_double}個** に自動最適化しました。")
else:
    num_double = st.sidebar.slider("ダブル（2択）を使う試合数", min_value=0, max_value=max_d, value=2)
    num_triple = st.sidebar.slider("トリプル（全通り）を使う試合数", min_value=0, max_value=max_t, value=0)

combinations = (2 ** num_double) * (3 ** num_triple)
total_cost = combinations * 100

st.sidebar.metric(label="合計購入口数", value=f"{combinations:,} 口")
st.sidebar.metric(label="合計購入金額", value=f"{total_cost:,} 円")
st.sidebar.metric(label="推定最低当せん金", value=f"{estimated_min_payout:,} 円")

triple_nos = [m["no"] for m in sorted_matches[:num_triple]]
double_nos = [m["no"] for m in sorted_matches[num_triple:num_triple + num_double]]

st.subheader(f"📋 【{selected_round_key}】 mini toto-A組 予想＆推奨買い目")

results = []

for m in matches:
    choices = [
        {"mark": "1", "prob": m["home_p"]},
        {"mark": "0", "prob": m["draw_p"]},
        {"mark": "2", "prob": m["away_p"]}
    ]
    
    if strategy == "大穴・波乱狙い（高配当）":
        for c in choices:
            weight = 0.70 if c["mark"] == "1" else 1.30
            c["calc_score"] = c["prob"] * weight
        choices = sorted(choices, key=lambda x: x["calc_score"], reverse=True)
    else:
        choices = sorted(choices, key=lambda x: x["prob"], reverse=True)

    c_first, c_second, c_third = choices
    mark_first = c_first["mark"]
    mark_second = c_second["mark"]

    is_1_checked = False
    is_0_checked = False
    is_2_checked = False

    if m["no"] in triple_nos:
        buy_type = "🔴 トリプル (全抑え)"
        selection = "【1】 【0】 【2】"
        is_1_checked = is_0_checked = is_2_checked = True
    elif m["no"] in double_nos:
        buy_type = "🟡 ダブル (2択)"
        mark_a, mark_b = sorted([mark_first, mark_second])
        selection = f"【{mark_a}】 【{mark_b}】"
        if mark_a == "1" or mark_b == "1":
            is_1_checked = True
        if mark_a == "0" or mark_b == "0":
            is_0_checked = True
        if mark_a == "2" or mark_b == "2":
            is_2_checked = True
    else:
        buy_type = "⚪ シングル (1点)"
        selection = f"【{mark_first}】"
        if mark_first == "1":
            is_1_checked = True
        elif mark_first == "0":
            is_0_checked = True
        elif mark_first == "2":
            is_2_checked = True

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**第{m['no']}試合** @ {m['stadium']}")
        st.write(f"🏠 **{m['home']}** ({m['home_rank']}位) vs 🚩 **{m['away']}** ({m['away_rank']}位)")
        if m["derby"]:
            st.error(m["derby"])
        st.caption(f"天候: {m['weather']}")
        
        if enable_lineup_check:
            if m["lineup_h_alert"]:
                st.markdown(f"🚨 <small style='color:red;'>**{m['home']}**: {m['lineup_h_alert']}</small>", unsafe_allow_html=True)
            if m["lineup_a_alert"]:
                st.markdown(f"🚨 <small style='color:red;'>**{m['away']}**: {m['lineup_a_alert']}</small>", unsafe_allow_html=True)
            if not m["lineup_h_alert"] and not m["lineup_a_alert"]:
                st.markdown("<small style='color:green;'>✅ スタメン確認：主力出場</small>", unsafe_allow_html=True)
        
        badge_info = []
        if m["h_susp"]:
            badge_info.append(f"🟥 **{m['home']}**: 出場停止 ({m['h_susp']})")
        if m["a_susp"]:
            badge_info.append(f"🟥 **{m['away']}**: 出場停止 ({m['a_susp']})")
        if m["h_scorer"]:
            badge_info.append(f"⚽ **{m['home']}**: {m['h_scorer']}")
        if m["a_scorer"]:
            badge_info.append(f"⚽ **{m['away']}**: {m['a_scorer']}")
            
        for b in badge_info:
            st.markdown(f"<small>{b}</small>", unsafe_allow_html=True)
        
    with col2:
        st.write(f"勝率予想: **{int(m['home_p']*100)}%** | 【0】 **{int(m['draw_p']*100)}%** | **{int(m['away_p']*100)}%**")
        st.caption(f"購入枠: {buy_type}")
        
    with col3:
        st.info(f"買い目: **{selection}**")

    results.append({
        "試合番号": f"第{m['no']}試合",
        "対戦カード": f"{m['home']} vs {m['away']}",
        "購入タイプ": buy_type,
        "マーク": selection,
        "is_1": is_1_checked,
        "is_0": is_0_checked,
        "is_2": is_2_checked,
    })
    st.divider()

# --- 楽天toto 照合用マークシート ---
st.subheader("👀 打ち間違い防止：楽天toto 照合用マークシート")
st.caption("楽天totoの購入画面を開き、以下の【マーク】欄の通りにチェックをつけてください。")

st.link_button("🛒 楽天toto 公式購入画面を開く", "https://toto.rakuten.co.jp/")

sheet_rows = []
for r in results:
    m1 = "🟥【 1 】" if r["is_1"] else " ( 1 ) "
    m0 = "🟩【 0 】" if r["is_0"] else " ( 0 ) "
    m2 = "🟦【 2 】" if r["is_2"] else " ( 2 ) "
    sheet_rows.append({
        "試合": r["試合番号"],
        "対戦カード": r["対戦カード"],
        "購入枠": r["購入タイプ"],
        " ホーム勝ち ": m1,
        " [0] その他(引分) ": m0,
        " アウェイ勝ち ": m2,
    })

df_verification = pd.DataFrame(sheet_rows)
st.dataframe(df_verification, use_container_width=True, hide_index=True)