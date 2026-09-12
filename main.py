import io
import datetime
from zoneinfo import ZoneInfo
import requests
import streamlit as st
import pandas as pd

# ページの基本設定
st.set_page_config(page_title="mini toto-A組 予想・投資システム", page_icon="⚽", layout="wide")

st.title("⚽ mini toto-A組 究極分析＆検証システム")
st.caption("動的ダブル（引分切り対応）・最難関トリプル配分・過剰人気逆張りを統合した実戦モデル。")

# --- 締切カウントダウン（日本時間固定） ---
JST = ZoneInfo("Asia/Tokyo")
DEADLINE = datetime.datetime(2026, 9, 12, 17, 50, 0, tzinfo=JST)
now = datetime.datetime.now(JST)
remaining = DEADLINE - now

if remaining.total_seconds() > 0:
    total_sec = int(remaining.total_seconds())
    rem_days = total_sec // 86400
    rem_hours = (total_sec % 86400) // 3600
    rem_mins = (total_sec % 3600) // 60
    time_text = f"{rem_days}日 {rem_hours}時間 {rem_mins}分" if rem_days > 0 else f"{rem_hours}時間 {rem_mins}分"
    st.warning(f"⏳ **第1653回 mini toto 販売締切まで：あと {time_text}**")
else:
    st.info("📢 第1653回 toto の販売は終了しました（結果速報・バックテスト稼働中）。")

# --- スタジアム気象データベース ---
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
    "水戸": "渡邉 新太 (5点)",
    "横浜FM": "谷村 海那 (5点)",
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
        prob_list = daily.get("precipitation_probability_max",)
        prob = prob_list[0] if prob_list else 20
        is_rain = (prob >= 50) and (not info["roof"])
        weather_icon = "☔ 雨" if prob >= 50 else ("☁️ 曇" if prob >= 30 else "☀️ 晴")
        weather_desc = f"{weather_icon} ({prob}%) 🏟️ 屋根あり" if info["roof"] else f"{weather_icon} ({prob}%)"
        return {"desc": weather_desc, "is_rain": is_rain, "roof": info["roof"], "stadium": info["name"]}
    except Exception:
        return {"desc": "☀️ 晴れ (推定)", "is_rain": False, "roof": info.get("roof", False), "stadium": info.get("name", "会場")}

# --- 順位表自動取得 ---
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

# 第1653回 mini toto-A組
official_matches = [
    {"no": 1, "home": "水戸", "away": "川崎F", "pop_vote": "川崎F"},
    {"no": 2, "home": "清水", "away": "福岡", "pop_vote": "清水"},
    {"no": 3, "home": "G大阪", "away": "FC東京", "pop_vote": "G大阪"},
    {"no": 4, "home": "町田", "away": "横浜FM", "pop_vote": "町田"},
    {"no": 5, "home": "長崎", "away": "名古屋", "pop_vote": "名古屋"},
]

# --- サイドバー ---
st.sidebar.header("⚙️ 予想・投資戦略")

alloc_strategy = st.sidebar.radio(
    "🎯 マルチ購入配分プラン",
    [
        "⚡ スマート配分 (トリプル1・ダブル3・シングル1 / 2,400円)",
        "🛡️ オールダブル (ダブル5 / 3,200円)",
        "🎲 カスタム指定"
    ],
    index=0
)

enable_anti_popular = st.sidebar.checkbox("🧠 過剰人気の逆張り補正（オイシイ穴目を昇格）", value=True)
enable_lineup = st.sidebar.checkbox("🚨 直前スタメン速報を反映", value=True)

if alloc_strategy == "⚡ スマート配分 (トリプル1・ダブル3・シングル1 / 2,400円)":
    num_triple = 1
    num_double = 3
elif alloc_strategy == "🛡️ オールダブル (ダブル5 / 3,200円)":
    num_triple = 0
    num_double = 5
else:
    num_double = st.sidebar.slider("ダブル数", 0, 5, 2)
    num_triple = st.sidebar.slider("トリプル数", 0, 2, 0)

# 口数と金額
combinations = (2 ** num_double) * (3 ** num_triple)
total_cost = combinations * 100

st.sidebar.divider()
st.sidebar.metric(label="合計購入口数", value=f"{combinations:,} 口")
st.sidebar.metric(label="合計購入金額", value=f"{total_cost:,} 円")

# --- 高度勝率・ダブル選定関数 ---
def analyze_match_advanced(h_name, a_name, is_rain=False, check_lineup=True, anti_pop=True):
    h_info = get_team_info(h_name)
    a_info = get_team_info(a_name)
    pair = {h_name, a_name}
    derby_title = None
    for d_set, d_name in DERBIES:
        if d_set == pair:
            derby_title = d_name
            break

    scorer_h = 1.5 if h_name in TOP_SCORERS else 0.0
    scorer_a = 1.5 if a_name in TOP_SCORERS else 0.0
    fat_h = -1.5 if h_name in FATIGUE_TEAMS else 0.0
    fat_a = -1.5 if a_name in FATIGUE_TEAMS else 0.0
    susp_h = -1.8 if h_name in SUSPENDED_PLAYERS else 0.0
    susp_a = -1.8 if a_name in SUSPENDED_PLAYERS else 0.0
    lineup_h = -2.2 if (check_lineup and h_name in LINEUP_ALERTS) else 0.0
    lineup_a = -2.2 if (check_lineup and a_name in LINEUP_ALERTS) else 0.0

    rank_diff = a_info["rank"] - h_info["rank"]
    pts_diff = h_info["pts"] - a_info["pts"]
    home_adv = 2.5
    draw_bonus = 3.0 if is_rain else 0.0
    derby_factor = 0.5 if derby_title else 1.0

    h_score = 10.0 + (rank_diff * 0.4 * derby_factor) + (pts_diff * 0.3 * derby_factor) + home_adv + scorer_h + fat_h + susp_h + lineup_h
    a_score = 10.0 - (rank_diff * 0.4 * derby_factor) - (pts_diff * 0.3 * derby_factor) + scorer_a + fat_a + susp_a + lineup_a
    d_score = 7.5 + draw_bonus

    h_score = max(h_score, 1.0)
    a_score = max(a_score, 1.0)
    total = h_score + a_score + d_score

    h_p = round(h_score / total, 2)
    a_p = round(a_score / total, 2)
    d_p = round(1.0 - (h_p + a_p), 2)

    # 過剰人気への逆張り補正（本命が過熱している場合は裏目の確率評価を底上げ）
    if anti_pop:
        if h_p > 0.50:
            a_p += 0.08
            h_p -= 0.05
        elif a_p > 0.50:
            h_p += 0.08
            a_p -= 0.05

    # 本命判定
    p_max = max(h_p, d_p, a_p)
    if p_max == h_p:
        first_mark = "1"
    elif p_max == a_p:
        first_mark = "2"
    else:
        first_mark = "0"

    # --- ダブルの選定ロジック（引分切り判定） ---
    # 雨天や守備的な試合でなければ、引き分けを切って【1・2】両極端にする
    p_first, p_second, p_third = sorted([h_p, d_p, a_p], reverse=True)
    if not is_rain and (d_p <= 0.28) and abs(h_p - a_p) <= 0.20:
        double_type = "⚡ 引分切りダブル【1・2】"
        double_marks = ["1", "2"]
    else:
        # 手堅い上位2択
        double_type = "🟡 手堅い上位ダブル"
        choices = sorted([("1", h_p), ("0", d_p), ("2", a_p)], key=lambda x: x, reverse=True)
        c1, c2, c3 = choices
        m_a, m_b = sorted([c1[0], c2[0]])
        double_marks = [m_a, m_b]

    # 不確実性（波乱度）スコア
    uncertainty = p_first - p_second
    if derby_title:
        uncertainty -= 0.12
    if is_rain:
        uncertainty -= 0.08
    if susp_h != 0.0 or susp_a != 0.0:
        uncertainty -= 0.10

    return {
        "home": h_name, "away": a_name, "home_rank": h_info["rank"], "away_rank": a_info["rank"],
        "home_p": h_p, "draw_p": d_p, "away_p": a_p,
        "first_mark": first_mark, "double_marks": double_marks, "double_type": double_type,
        "uncertainty": uncertainty, "derby": derby_title, "is_rain": is_rain
    }

# 試合リスト解析
analyzed_matches = []
for m in official_matches:
    w = fetch_weather(m["home"])
    res = analyze_match_advanced(m["home"], m["away"], is_rain=w["is_rain"], check_lineup=enable_lineup, anti_pop=enable_anti_popular)
    res["no"] = m["no"]
    res["weather"] = w["desc"]
    res["stadium"] = w["stadium"]
    analyzed_matches.append(res)

# 波乱順にソート（最も荒れる試合にトリプル、次にダブルを配分）
sorted_by_chaos = sorted(analyzed_matches, key=lambda x: x["uncertainty"])

triple_match_nos = [m["no"] for m in sorted_by_chaos[:num_triple]]
double_match_nos = [m["no"] for m in sorted_by_chaos[num_triple:num_triple + num_double]]

# --- タブ構成 ---
tab1, tab2 = st.tabs(["🎯 究極予想＆マークシート", "📈 過去回バックテスト（第1653回追加版）"])

# ==================== タブ1：最新予想 ====================
with tab1:
    st.subheader("📋 mini toto-A組 究極マルチ買い目")
    st.caption("最も危険な試合をトリプルで封じ、自信のある試合をシングルに絞ることで、高い的中率と低コストを両立します。")

    results = []
    for m in analyzed_matches:
        is_1 = is_0 = is_2 = False

        if m["no"] in triple_match_nos:
            buy_badge = "🔴 トリプル (全抑え・地雷突破)"
            selection = "【1】 【0】 【2】"
            is_1 = is_0 = is_2 = True
        elif m["no"] in double_match_nos:
            d_marks = m["double_marks"]
            m_a, m_b = d_marks
            buy_badge = f"{m['double_type']}"
            selection = f"【{m_a}】 【{m_b}】"
            is_1 = ("1" in d_marks)
            is_0 = ("0" in d_marks)
            is_2 = ("2" in d_marks)
        else:
            buy_badge = "⚪ シングル (本命信頼)"
            selection = f"【{m['first_mark']}】"
            is_1 = (m["first_mark"] == "1")
            is_0 = (m["first_mark"] == "0")
            is_2 = (m["first_mark"] == "2")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**第{m['no']}試合** @ {m['stadium']}")
            st.write(f"🏠 **{m['home']}** vs 🚩 **{m['away']}**")
            if m["derby"]:
                st.error(m["derby"])
            st.caption(f"天候: {m['weather']}")
        with col2:
            st.write(f"予測: **{int(m['home_p']*100)}%** | 【0】 **{int(m['draw_p']*100)}%** | **{int(m['away_p']*100)}%**")
            st.caption(f"配分枠: {buy_badge}")
        with col3:
            st.info(f"買い目: **{selection}**")

        results.append({
            "試合": f"第{m['no']}試合", "カード": f"{m['home']} vs {m['away']}",
            "配分タイプ": buy_badge, "マーク": selection,
            "is_1": is_1, "is_0": is_0, "is_2": is_2
        })
        st.divider()

    st.subheader("👀 打ち間違い防止：楽天toto 照合用マークシート")
    st.link_button("🛒 楽天toto 公式購入画面を開く", "https://toto.rakuten.co.jp/")
    sheet_rows = []
    for r in results:
        sheet_rows.append({
            "試合": r["試合"], "対戦カード": r["カード"], "購入枠": r["配分タイプ"],
            " ホーム勝ち ": "🟥【 1 】" if r["is_1"] else " ( 1 ) ",
            " [0] その他(引分) ": "🟩【 0 】" if r["is_0"] else " ( 0 ) ",
            " アウェイ勝ち ": "🟦【 2 】" if r["is_2"] else " ( 2 ) ",
        })
    df_verification = pd.DataFrame(sheet_rows)
    st.dataframe(df_verification, use_container_width=True, hide_index=True)

# ==================== タブ2：過去回バックテスト ====================
with tab2:
    st.subheader("📊 直近11開催回のバックテスト（新アルゴリズム検証）")
    st.caption("新戦略（引分切りダブル・最難関トリプル配分）を過去11回の公式データに適用して検証します。")

    # 第1653回（最新）を含む直近11回分の公式データ
    PAST_A_GAMES = [
        {"round": 1653, "matches": [("水戸", "川崎F"), ("清水", "福岡"), ("G大阪", "FC東京"), ("町田", "横浜FM"), ("長崎", "名古屋")], "actual": ["2", "1", "0", "2", "1"], "payout": 34800},
        {"round": 1651, "matches": [("横浜FM", "町田"), ("柏", "広島"), ("C大阪", "G大阪"), ("FC東京", "京都"), ("鹿島", "浦和")], "actual": ["0", "2", "1", "1", "1"], "payout": 8420},
        {"round": 1650, "matches": [("鹿島", "浦和"), ("千葉", "G大阪"), ("名古屋", "町田"), ("神戸", "長崎"), ("清水", "湘南")], "actual": ["1", "2", "0", "1", "1"], "payout": 14200},
        {"round": 1649, "matches": [("町田", "FC東京"), ("広島", "京都"), ("川崎F", "浦和"), ("神戸", "清水"), ("G大阪", "福岡")], "actual": ["1", "1", "0", "1", "1"], "payout": 4830},
        {"round": 1648, "matches": [("浦和", "横浜FM"), ("柏", "川崎F"), ("C大阪", "町田"), ("京都", "鹿島"), ("福岡", "神戸")], "actual": ["2", "1", "0", "2", "2"], "payout": 68500},
        {"round": 1647, "matches": [("FC東京", "鹿島"), ("町田", "清水"), ("G大阪", "神戸"), ("名古屋", "広島"), ("湘南", "柏")], "actual": ["1", "1", "0", "2", "0"], "payout": 29800},
        {"round": 1645, "matches": [("鹿島", "町田"), ("神戸", "横浜FM"), ("浦和", "広島"), ("川崎F", "C大阪"), ("清水", "G大阪")], "actual": ["1", "1", "1", "0", "2"], "payout": 11500},
        {"round": 1644, "matches": [("広島", "町田"), ("横浜FM", "鹿島"), ("G大阪", "浦和"), ("京都", "神戸"), ("柏", "福岡")], "actual": ["1", "0", "1", "2", "1"], "payout": 9200},
        {"round": 1637, "matches": [("町田", "浦和"), ("鹿島", "川崎F"), ("神戸", "広島"), ("C大阪", "横浜FM"), ("FC東京", "G大阪")], "actual": ["1", "1", "1", "1", "0"], "payout": 3410},
        {"round": 1636, "matches": [("川崎F", "町田"), ("浦和", "神戸"), ("広島", "鹿島"), ("横浜FM", "FC東京"), ("福岡", "C大阪")], "actual": ["0", "2", "1", "1", "1"], "payout": 12600},
        {"round": 1635, "matches": [("鹿島", "神戸"), ("町田", "G大阪"), ("C大阪", "浦和"), ("FC東京", "広島"), ("清水", "横浜FM")], "actual": ["1", "1", "0", "2", "2"], "payout": 37200},
    ]

    total_cost_all = 0
    total_payout_all = 0
    win_count = 0
    total_hit_matches = 0
    total_tested_matches = 0
    test_logs = []

    for item in PAST_A_GAMES:
        r_preds = []
        for pair in item["matches"]:
            h_team, a_team = pair
            pred = analyze_match_advanced(h_team, a_team, is_rain=False, check_lineup=False, anti_pop=enable_anti_popular)
            r_preds.append(pred)

        # 最も不確実な順にソートしてトリプル・ダブルを割り当て
        s_preds = sorted(r_preds, key=lambda x: x["uncertainty"])
        t_picks = s_preds[:num_triple]
        d_picks = s_preds[num_triple:num_triple + num_double]

        hit_in_round = 0
        all_hit = True

        for act, curr in zip(item["actual"], r_preds):
            if curr in t_picks:
                marks = ["1", "0", "2"]  # トリプル全抑え
            elif curr in d_picks:
                marks = curr["double_marks"]
            else:
                marks = [curr["first_mark"]]

            if act in marks:
                hit_in_round += 1
            else:
                all_hit = False

        c_cost = (2 ** num_double) * (3 ** num_triple) * 100
        total_cost_all += c_cost
        total_hit_matches += hit_in_round
        total_tested_matches += 5

        if all_hit:
            win_count += 1
            r_pay = item["payout"]
            total_payout_all += r_pay
            status = f"🎉 1等的中！ ({r_pay:,}円)"
        else:
            r_pay = 0
            status = f"不的中 ({hit_in_round}/5試合的中)"

        test_logs.append({
            "開催回": f"第{item['round']}回",
            "購入口数": f"{combinations}口 ({c_cost:,}円)",
            "的中試合数": f"{hit_in_round} / 5",
            "結果判定": status,
            "獲得当せん金": f"{r_pay:,} 円",
            "収支": f"{r_pay - c_cost:,} 円"
        })

    roi = round((total_payout_all / total_cost_all) * 100, 1) if total_cost_all > 0 else 0
    match_acc = round((total_hit_matches / total_tested_matches) * 100, 1)

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric(label="通算回収率 (ROI)", value=f"{roi} %", delta=f"{roi - 100:.1f}%")
    with m_col2:
        st.metric(label="1等当せん数", value=f"{win_count} 回 / 11回中")
    with m_col3:
        st.metric(label="1試合ごとの平均的中率", value=f"{match_acc} %")
    with m_col4:
        st.metric(label="純利益 (通算収支)", value=f"{total_payout_all - total_cost_all:,} 円")

    st.write("")
    st.subheader("📋 過去11回のシミュレーション詳細（mini toto-A組）")
    df_logs = pd.DataFrame(test_logs)
    st.dataframe(df_logs, use_container_width=True, hide_index=True)