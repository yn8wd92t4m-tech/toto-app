import io
import datetime
from zoneinfo import ZoneInfo
import requests
import streamlit as st
import pandas as pd

# ページの基本設定
st.set_page_config(page_title="mini toto高配当特化ナビゲーター", page_icon="⚽", layout="wide")

st.title("⚽ mini toto 高配当特化（36口包囲網）ナビゲーター")
st.caption("「波乱の偶数回」を完全制覇――トリプル2個＋ダブル2個＋厳選シングル1個で数万円の高配当を一撃で掴む実戦モデル。")

# --- 開催回スケジュールマスター ---
JST = ZoneInfo("Asia/Tokyo")
now = datetime.datetime.now(JST)

ROUNDS_SCHEDULE = {
    "第1660回 (10/10 土 開催)": {
        "deadline": datetime.datetime(2026, 10, 10, 13, 50, 0, tzinfo=JST),
        "round_num": 1660,
        "matches": [
            {"no": 1, "home": "C大阪", "away": "横浜FM"},
            {"no": 2, "home": "FC東京", "away": "浦和"},
            {"no": 3, "home": "福岡", "away": "岡山"},
            {"no": 4, "home": "千葉", "away": "長崎"},
            {"no": 5, "home": "水戸", "away": "清水"},
        ]
    },
    "第1659回 (10/7 水 開催・終了)": {
        "deadline": datetime.datetime(2026, 10, 7, 18, 20, 0, tzinfo=JST),
        "round_num": 1659,
        "matches": [
            {"no": 1, "home": "広島", "away": "いわき"},
            {"no": 2, "home": "岡山", "away": "千葉"},
            {"no": 3, "home": "清水", "away": "長崎"},
            {"no": 4, "home": "鳥取", "away": "東京V"},
            {"no": 5, "home": "川崎F", "away": "宮崎"},
        ]
    }
}

# --- サイドバー ---
st.sidebar.header("⚙️ 開催回・戦略設定")

# 更新ボタン
if st.sidebar.button("🔄 最新データを更新・再取得"):
    st.cache_data.clear()
    st.rerun()

round_keys = list(ROUNDS_SCHEDULE.keys())

selected_round_key = st.sidebar.selectbox(
    "🎟️ 対象の開催回",
    round_keys,
    index=0,
    key="round_select_box"
)

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

st.sidebar.divider()
st.sidebar.subheader("🎯 投資配分プラン")

strategy_plan = st.sidebar.radio(
    "マルチ配分方式",
    [
        "🔥 高配当包囲網 (トリプル2・ダブル2・シングル1 / 3,600円)",
        "🛡️ バランス配分 (トリプル1・ダブル2・シングル2 / 1,200円)",
        "🎲 カスタム指定"
    ],
    index=0
)

if "高配当包囲網" in strategy_plan:
    num_triple = 2
    num_double = 2
elif "バランス" in strategy_plan:
    num_triple = 1
    num_double = 2
else:
    num_triple = st.sidebar.slider("トリプル数", 0, 3, 2)
    num_double = st.sidebar.slider("ダブル数", 0, 4, 2)

combinations = (3 ** num_triple) * (2 ** num_double)
total_cost = combinations * 100

st.sidebar.metric(label="合計購入口数", value=f"{combinations:,} 口")
st.sidebar.metric(label="合計投資金額", value=f"{total_cost:,} 円")

# --- スタジアム気象データベース（第1660回 会場対応） ---
STADIUM_DB = {
    "C大阪": {"lat": 34.618, "lon": 135.518, "name": "ヨドコウ", "roof": False},
    "FC東京": {"lat": 35.664, "lon": 139.527, "name": "味スタ", "roof": False},
    "福岡": {"lat": 33.585, "lon": 130.460, "name": "ベススタ", "roof": False},
    "千葉": {"lat": 35.578, "lon": 140.123, "name": "フクアリ", "roof": False},
    "水戸": {"lat": 36.345, "lon": 140.412, "name": "Ksスタ", "roof": False},
    "清水": {"lat": 34.985, "lon": 138.531, "name": "アイスタ", "roof": False},
    "浦和": {"lat": 35.903, "lon": 139.717, "name": "埼玉", "roof": False},
}

# ダービー・注目カード
DERBIES = [
    ({"FC東京", "浦和"}, "🔥 伝統の激突・赤青クラシコ"),
    ({"C大阪", "横浜FM"}, "🔥 伝統の強豪対決"),
    ({"千葉", "長崎"}, "🔥 J2昇格争い頂上決戦"),
]

TOP_SCORERS = {
    "C大阪": "レオ セアラ",
    "横浜FM": "アンデルソン ロペス",
    "清水": "北川 航也",
    "長崎": "マテウス ジェズス",
}

FATIGUE_TEAMS = {"横浜FM", "浦和", "清水", "長崎"}
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
    # J2等の目安順位
    defaults = {
        "C大阪": {"rank": 8, "pts": 45}, "横浜FM": {"rank": 6, "pts": 48}, "FC東京": {"rank": 7, "pts": 46},
        "浦和": {"rank": 9, "pts": 43}, "福岡": {"rank": 10, "pts": 40},
        "清水": {"rank": 1, "pts": 65}, "長崎": {"rank": 3, "pts": 58}, "千葉": {"rank": 5, "pts": 52},
        "岡山": {"rank": 6, "pts": 50}, "水戸": {"rank": 15, "pts": 32}
    }
    return defaults.get(name, {"rank": 10, "pts": 40})

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

    rank_diff = a_info["rank"] - h_info["rank"]
    pts_diff = h_info["pts"] - a_info["pts"]
    home_adv = 2.2
    draw_bonus = 3.0 if weather_info["is_rain"] else 0.0
    derby_factor = 0.5 if derby_title else 1.0

    home_score = 10.0 + (rank_diff * 0.4 * derby_factor) + (pts_diff * 0.3 * derby_factor) + home_adv + scorer_h_bonus + fatigue_h_penalty
    away_score = 10.0 - (rank_diff * 0.4 * derby_factor) - (pts_diff * 0.3 * derby_factor) + scorer_a_bonus + fatigue_a_penalty
    draw_score = 7.5 + draw_bonus

    home_score = max(home_score, 1.0)
    away_score = max(away_score, 1.0)
    total = home_score + away_score + draw_score

    h_p = round(home_score / total, 2)
    a_p = round(away_score / total, 2)
    d_p = round(1.0 - (h_p + a_p), 2)

    # 不確実性スコア（小さいほど大荒れの危険試合）
    p_first, p_second, p_third = sorted([h_p, d_p, a_p], reverse=True)
    uncertainty = p_first - p_second
    if derby_title:
        uncertainty -= 0.15
    if weather_info["is_rain"]:
        uncertainty -= 0.08
    if h_name in FATIGUE_TEAMS or a_name in FATIGUE_TEAMS:
        uncertainty -= 0.05

    matches.append({
        "no": rm["no"],
        "home": h_name,
        "away": a_name,
        "home_rank": h_info["rank"],
        "away_rank": a_info["rank"],
        "home_p": h_p,
        "draw_p": d_p,
        "away_p": a_p,
        "weather": weather_info["desc"],
        "stadium": weather_info["stadium"],
        "derby": derby_title,
        "uncertainty": uncertainty,
        "reliability": p_first
    })

# 波乱順（不確実性が高い順）にソートしてトリプルを割り当て
sorted_by_chaos = sorted(matches, key=lambda x: x["uncertainty"])
triple_nos = [m["no"] for m in sorted_by_chaos[:num_triple]]

# 残り試合の中で、本命信頼度が最も高い試合をシングルに指定し、残りをダブルに
remaining_matches = [m for m in sorted_by_chaos[num_triple:]]
sorted_by_reliability = sorted(remaining_matches, key=lambda x: x["reliability"], reverse=True)

num_single = max(5 - num_triple - num_double, 0)
single_nos = [m["no"] for m in sorted_by_reliability[:num_single]]
double_nos = [m["no"] for m in sorted_by_reliability[num_single:]]

# --- 画面上部：波乱警報バナー ---
st.error(f"### 🔥 第{round_num}回：大波乱警報発令中（36口包囲網で高配当直撃を狙う）\n**💡 作戦**: 交互にやってくる『波乱の偶数回』です！実力伯仲の激戦2試合を【トリプル全抑え】で完全封殺し、自信のある1試合だけを【シングル】に厳選。今度こそ数万円の高配当を全勝で仕留めます！")

st.subheader(f"📋 【{selected_round_key}】 mini toto-A組 推奨買い目")

results = []

for m in matches:
    choices = [
        {"mark": "1", "prob": m["home_p"]},
        {"mark": "0", "prob": m["draw_p"]},
        {"mark": "2", "prob": m["away_p"]}
    ]
    choices = sorted(choices, key=lambda x: x["prob"], reverse=True)
    c1, c2, c3 = choices

    is_1_checked = False
    is_0_checked = False
    is_2_checked = False

    if m["no"] in triple_nos:
        buy_type = "🔴 トリプル (全抑え・波乱封殺)"
        selection = "【1】 【0】 【2】"
        is_1_checked = is_0_checked = is_2_checked = True
    elif m["no"] in double_nos:
        buy_type = "🟡 ダブル (2択カバー)"
        m_a, m_b = sorted([c1["mark"], c2["mark"]])
        selection = f"【{m_a}】 【{m_b}】"
        if "1" in [m_a, m_b]:
            is_1_checked = True
        if "0" in [m_a, m_b]:
            is_0_checked = True
        if "2" in [m_a, m_b]:
            is_2_checked = True
    else:
        buy_type = "⚪ 厳選シングル (鉄板1点)"
        selection = f"【{c1['mark']}】"
        if c1["mark"] == "1":
            is_1_checked = True
        elif c1["mark"] == "0":
            is_0_checked = True
        elif c1["mark"] == "2":
            is_2_checked = True

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**第{m['no']}試合** @ {m['stadium']}")
        st.write(f"🏠 **{m['home']}** vs 🚩 **{m['away']}**")
        if m["derby"]:
            st.error(m["derby"])
        st.caption(f"天候: {m['weather']}")
        
    with col2:
        st.write(f"勝率予想: **{int(m['home_p']*100)}%** | 【0】 **{int(m['draw_p']*100)}%** | **{int(m['away_p']*100)}%**")
        st.caption(f"配分枠: {buy_type}")
        
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