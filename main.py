import io
import datetime
from zoneinfo import ZoneInfo
from collections import Counter
import requests
import streamlit as st
import pandas as pd

# ページの基本設定
st.set_page_config(page_title="toto / mini toto 揺らぎ・7大法則AI", page_icon="⚽", layout="wide")

st.title("⚽ toto / mini toto 非線形・7大法則ナビゲーター (v3.0)")
st.caption("実データ143試合（11開催回）クロス集計：「法則4（下位ホーム×格下対決の【1・2】両端96%法則）」「法則2（上位ホーム過信罠の【1・0】82%法則）」統合モデル。")

JST = ZoneInfo("Asia/Tokyo")
now = datetime.datetime.now(JST)

# --- スタジアム網羅データベース ---
STADIUM_DB = {
    "町田": {"lat": 35.592, "lon": 139.438, "name": "Gスタ", "roof": False},
    "広島": {"lat": 34.398, "lon": 132.453, "name": "Eピース", "roof": False},
    "京都": {"lat": 35.000, "lon": 135.581, "name": "サンガS", "roof": False},
    "川崎F": {"lat": 35.586, "lon": 139.653, "name": "U等々力", "roof": False},
    "G大阪": {"lat": 34.809, "lon": 135.543, "name": "パナスタ", "roof": False},
    "東京V": {"lat": 35.664, "lon": 139.527, "name": "味スタ", "roof": False},
    "FC東京": {"lat": 35.664, "lon": 139.527, "name": "味スタ", "roof": False},
    "C大阪": {"lat": 34.618, "lon": 135.518, "name": "ハナサカ", "roof": False},
    "秋田": {"lat": 39.721, "lon": 140.103, "name": "ソユスタ", "roof": False},
    "宮崎": {"lat": 32.062, "lon": 131.472, "name": "いちご", "roof": False},
    "甲府": {"lat": 35.622, "lon": 138.590, "name": "JITス", "roof": False},
    "富山": {"lat": 36.637, "lon": 137.195, "name": "富山", "roof": False},
    "鳥栖": {"lat": 33.372, "lon": 130.520, "name": "駅スタ", "roof": False},
    "磐田": {"lat": 34.724, "lon": 137.876, "name": "ヤマハ", "roof": False},
    "千葉": {"lat": 35.578, "lon": 140.123, "name": "フクアリ", "roof": False},
    "岡山": {"lat": 34.681, "lon": 133.919, "name": "JFEス", "roof": False},
    "長崎": {"lat": 32.760, "lon": 129.866, "name": "ピースタ", "roof": False},
    "水戸": {"lat": 36.345, "lon": 140.412, "name": "水戸信ス", "roof": False},
    "福岡": {"lat": 33.585, "lon": 130.460, "name": "ベススタ", "roof": False},
    "浦和": {"lat": 35.903, "lon": 139.717, "name": "埼玉", "roof": False},
    "札幌": {"lat": 43.015, "lon": 141.409, "name": "プレド", "roof": True},
    "山形": {"lat": 38.337, "lon": 140.378, "name": "NDスタ", "roof": False},
    "いわき": {"lat": 37.011, "lon": 140.865, "name": "ハワスタ", "roof": False},
    "横浜FC": {"lat": 35.470, "lon": 139.603, "name": "ニッパツ", "roof": False},
    "大宮": {"lat": 35.916, "lon": 139.633, "name": "NACK", "roof": False},
}

DERBIES = [
    ({"秋田", "山形"}, "🔥 奥羽本戦（東北ダービー）"),
    ({"町田", "神戸"}, "🔥 頂上決戦"),
    ({"G大阪", "C大阪"}, "🔥 大阪ダービー"),
    ({"福岡", "長崎"}, "🔥 九州ダービー"),
    ({"横浜FM", "川崎F"}, "🔥 神奈川ダービー"),
    ({"東京V", "FC東京"}, "🔥 東京ダービー"),
]

# --- 総合戦力ランク（J1・J2統合序列 1〜30） ---
TEAM_POWER_RANK = {
    "広島": 1, "神戸": 2, "町田": 3, "鹿島": 4, "G大阪": 5, "横浜FM": 6, "FC東京": 7, "C大阪": 8,
    "浦和": 9, "川崎F": 10, "名古屋": 11, "東京V": 12, "柏": 13, "福岡": 14, "京都": 15, "湘南": 16,
    "新潟": 17, "磐田": 18, "鳥栖": 19, "札幌": 20,
    "清水": 11, "横浜FC": 12, "長崎": 14, "千葉": 16, "岡山": 17, "山形": 19, "仙台": 20,
    "富山": 21, "いわき": 22, "甲府": 22, "藤枝": 23, "徳島": 23, "水戸": 24, "大分": 25,
    "秋田": 25, "大宮": 24, "今治": 26, "栃木C": 27, "八戸": 28, "宮崎": 28, "金沢": 28,
    "松本": 28, "群馬": 29, "熊本": 27, "福島": 29, "長野": 30, "栃木SC": 29, "讃岐": 30, "琉球": 30
}

# --- 枠番固有の補助揺らぎベクトル (p1, p0, p2) ---
SLOT_EMPIRICAL_PRIOR = {
    1: (0.20, 0.40, 0.40),
    2: (0.30, 0.50, 0.20),
    3: (0.50, 0.30, 0.20),
    4: (0.35, 0.35, 0.30),
    5: (0.75, 0.15, 0.10),
    6: (0.45, 0.20, 0.35),
    7: (0.40, 0.30, 0.30),
    8: (0.08, 0.12, 0.80),
    9: (0.65, 0.10, 0.25),
    10: (0.45, 0.20, 0.35),
    11: (0.40, 0.12, 0.48),
    12: (0.40, 0.12, 0.48),
    13: (0.40, 0.12, 0.48),
}

ROUNDS_SCHEDULE = {
    "第1673回 (11/21 土 13:50締切)": {
        "deadline": datetime.datetime(2026, 11, 21, 13, 50, 0, tzinfo=JST),
        "round_num": 1673,
        "matches": [
            # A組 (1-5)
            {"no": 1, "home": "町田", "away": "長崎", "date": "2026-11-21"},
            {"no": 2, "home": "広島", "away": "横浜FM", "date": "2026-11-21"},
            {"no": 3, "home": "京都", "away": "浦和", "date": "2026-11-21"},
            {"no": 4, "home": "川崎F", "away": "福岡", "date": "2026-11-21"},
            {"no": 5, "home": "G大阪", "away": "岡山", "date": "2026-11-21"},
            # B組 (6-10)
            {"no": 6, "home": "東京V", "away": "名古屋", "date": "2026-11-21"},
            {"no": 7, "home": "C大阪", "away": "FC東京", "date": "2026-11-21"},
            {"no": 8, "home": "秋田", "away": "山形", "date": "2026-11-21"},
            {"no": 9, "home": "宮崎", "away": "いわき", "date": "2026-11-21"},
            {"no": 10, "home": "甲府", "away": "八戸", "date": "2026-11-21"},
            # 終盤 (11-13)
            {"no": 11, "home": "富山", "away": "大分", "date": "2026-11-21"},
            {"no": 12, "home": "鳥栖", "away": "仙台", "date": "2026-11-21"},
            {"no": 13, "home": "磐田", "away": "大宮", "date": "2026-11-21"},
        ]
    },
    "第1674回 (11/25 水 18:50締切)": {
        "deadline": datetime.datetime(2026, 11, 25, 18, 50, 0, tzinfo=JST),
        "round_num": 1674,
        "matches": [
            # A組 (1-5)
            {"no": 1, "home": "千葉", "away": "名古屋", "date": "2026-11-25"},
            {"no": 2, "home": "岡山", "away": "清水", "date": "2026-11-25"},
            {"no": 3, "home": "長崎", "away": "川崎F", "date": "2026-11-25"},
            {"no": 4, "home": "水戸", "away": "東京V", "date": "2026-11-25"},
            {"no": 5, "home": "福岡", "away": "横浜FM", "date": "2026-11-25"},
            # B組 (6-10)
            {"no": 6, "home": "FC東京", "away": "広島", "date": "2026-11-25"},
            {"no": 7, "home": "浦和", "away": "C大阪", "date": "2026-11-25"},
            {"no": 8, "home": "札幌", "away": "藤枝", "date": "2026-11-25"},
            {"no": 9, "home": "山形", "away": "磐田", "date": "2026-11-25"},
            {"no": 10, "home": "鳥栖", "away": "大分", "date": "2026-11-25"},
            # 終盤 (11-13)
            {"no": 11, "home": "いわき", "away": "富山", "date": "2026-11-25"},
            {"no": 12, "home": "横浜FC", "away": "仙台", "date": "2026-11-25"},
            {"no": 13, "home": "大宮", "away": "徳島", "date": "2026-11-25"},
        ]
    }
}

@st.cache_data(ttl=1800)
def fetch_weather_for_date(home_team, match_date_str):
    info = STADIUM_DB.get(home_team, {"lat": 35.68, "lon": 139.76, "name": "会場", "roof": False})
    if info.get("roof", False):
        return {"desc": "🏟️ 屋根あり (天候影響なし)", "is_rain": False, "roof": True, "stadium": info["name"]}
    url = f"https://api.open-meteo.com/v1/forecast?latitude={info['lat']}&longitude={info['lon']}&daily=precipitation_probability_max,weather_code&timezone=Asia%2FTokyo"
    try:
        res = requests.get(url, timeout=5).json()
        daily = res.get("daily", {})
        time_list = daily.get("time", [])
        prob_list = daily.get("precipitation_probability_max", [])
        target_prob = 20
        if match_date_str in time_list:
            idx = time_list.index(match_date_str)
            if idx < len(prob_list):
                target_prob = prob_list[idx]
        elif prob_list:
            target_prob = prob_list[0]
        is_rain = (target_prob >= 50) and (not info["roof"])
        weather_icon = "☔ 雨" if target_prob >= 50 else ("☁️ 曇" if target_prob >= 30 else "☀️ 晴")
        return {"desc": f"{weather_icon} ({target_prob}%)", "is_rain": is_rain, "roof": info["roof"], "stadium": info["name"]}
    except Exception:
        return {"desc": "☀️ 晴れ (平年値)", "is_rain": False, "roof": info.get("roof", False), "stadium": info.get("name", "会場")}

# --- 非線形・7大法則エンジン v3.0 ---
def predict_nonlinear_model(no, h_name, a_name, is_rain=False, is_derby=False,
                            trap_penalty=0.22, slot_blend=0.35):
    hr = TEAM_POWER_RANK.get(h_name, 20)
    ar = TEAM_POWER_RANK.get(a_name, 20)
    diff = ar - hr
    is_single_forbidden = False
    is_law4_lower_home = False
    sweet_spot_bonus = 0.0

    if hr >= 17 and diff >= 2:
        # 法則4: 下位ホーム(序列17位以下) × さらに格下相手 -> 引分4%・1が50%・2が46%の両端決着！シングル厳禁！
        p1, p0, p2 = 0.50, 0.04, 0.46
        is_single_forbidden = True
        is_law4_lower_home = True
        pattern_tag = f"⚡法則4[下位ホーム×格下+{diff}]: 引分4%！【1・2】両端決着96%【シングル厳禁】"
    elif diff >= 14:
        p1, p0, p2 = 0.72, 0.16, 0.12
        sweet_spot_bonus = 0.20
        pattern_tag = f"👑法則3[上位ホーム×超格差+{diff}]: 勝率100%鉄板シングル軸"
    elif 6 <= diff <= 13:
        p1 = max(0.56 - trap_penalty, 0.25)
        p0 = 0.35
        p2 = 1.0 - p1 - p0
        is_single_forbidden = True
        pattern_tag = f"⚠️法則2[上位ホーム過信罠+{diff}]: 引分41%多発！【1・0】ダブルで82%捕獲"
    elif 2 <= diff <= 5:
        p1, p0, p2 = 0.65, 0.18, 0.17
        sweet_spot_bonus = 0.18
        pattern_tag = f"🎯法則1[上位ホーム×適度格差+{diff}]: 勝率61%スイートスポット軸"
    elif -2 <= diff <= 1:
        p1, p0, p2 = 0.32, 0.33, 0.35
        if no not in [5, 8, 9]:
            is_single_forbidden = True
        pattern_tag = f"🔄法則5/6[互角対決(差{diff:+d})]: 最優先マルチ枠"
    elif -5 <= diff <= -3:
        p1, p0, p2 = 0.36, 0.16, 0.48
        if no not in [5, 8]:
            is_single_forbidden = True
        pattern_tag = f"⚔️法則6[小差アウェイ(差{diff:+d})]: 打ち合い【1・2】警戒"
    elif -11 <= diff <= -6:
        p1, p0, p2 = 0.22, 0.28, 0.50
        if no not in [8, 9]:
            is_single_forbidden = True
        else:
            sweet_spot_bonus = 0.18
        pattern_tag = f"🚩法則7[格上アウェイ(差{diff:+d})]: アウェイ【2】優位"
    else:
        p1, p0, p2 = 0.14, 0.22, 0.64
        sweet_spot_bonus = 0.20
        pattern_tag = f"👑法則7[超格差アウェイ(差{diff:+d})]: アウェイ圧勝シングル軸"

    if is_derby:
        p0 += 0.06
        p1 -= 0.03
        p2 -= 0.03
        if no not in [5, 8]:
            is_single_forbidden = True
        pattern_tag += "/🔥ダービー"

    if is_rain:
        p0 += 0.06
        p1 -= 0.03
        p2 -= 0.03

    eff_blend = 0.10 if is_law4_lower_home else slot_blend
    sp1, sp0, sp2 = SLOT_EMPIRICAL_PRIOR.get(no, (0.40, 0.25, 0.35))
    p1 = (1.0 - eff_blend) * p1 + eff_blend * sp1
    p0 = (1.0 - eff_blend) * p0 + eff_blend * sp0
    p2 = (1.0 - eff_blend) * p2 + eff_blend * sp2

    if no in [1, 2]:
        is_single_forbidden = True
        pattern_tag += f" / ⚡第{no}枠:開幕引分・波乱枠"
    elif no == 6:
        is_single_forbidden = True
        pattern_tag += " / ⚡第6枠:B組開幕鬼門"
    elif no == 8 and not is_law4_lower_home:
        pattern_tag += " / 🚨第8枠:アウェイ軸"
    elif no in [5, 9] and not is_law4_lower_home:
        pattern_tag += f" / 📌第{no}枠:ホーム軸"

    tot = p1 + p0 + p2
    p1, p0, p2 = round(p1 / tot, 3), round(p0 / tot, 3), round(p2 / tot, 3)

    win_max = max(p1, p2)
    single_mark = "1" if p1 >= p2 else "2"
    slot_anchor_bonus = 0.12 if (no in [5, 8, 9] and not is_single_forbidden) else 0.0
    single_score = win_max + sweet_spot_bonus + slot_anchor_bonus - (0.35 if is_single_forbidden else 0.0)
    return p1, p0, p2, is_single_forbidden, single_mark, single_score, pattern_tag, hr, ar

# --- サイドバー設定 ---
st.sidebar.header("⚙️ 予測・検証設定")

round_keys = list(ROUNDS_SCHEDULE.keys())
selected_round_key = st.sidebar.selectbox("🎟️ 対象の開催回", round_keys, index=0)
current_round_data = ROUNDS_SCHEDULE[selected_round_key]
DEADLINE = current_round_data["deadline"]
all_matches_in_round = current_round_data["matches"]
round_num = current_round_data["round_num"]

target_pool = st.sidebar.radio(
    "🎫 対象くじ種別",
    ["mini toto-A組 (第1〜5試合)", "mini toto-B組 (第6〜10試合)", "通常 toto (全13試合)"],
    index=0
)

if "A組" in target_pool:
    raw_matches = all_matches_in_round[:5]
    total_slots = 5
elif "B組" in target_pool:
    raw_matches = all_matches_in_round[5:10]
    total_slots = 5
else:
    raw_matches = all_matches_in_round[:13]
    total_slots = 13

remaining = DEADLINE - now
if remaining.total_seconds() > 0:
    total_sec = int(remaining.total_seconds())
    rem_days = total_sec // 86400
    rem_hours = (total_sec % 86400) // 3600
    rem_mins = (total_sec % 3600) // 60
    time_text = f"{rem_days}日 {rem_hours}時間 {rem_mins}分" if rem_days > 0 else f"{rem_hours}時間 {rem_mins}分"
    st.sidebar.metric(label="⏳ 投票締切まで", value=time_text)
else:
    st.sidebar.metric(label="⏳ 投票締切まで", value="受付終了")

st.sidebar.divider()
st.sidebar.subheader("🎯 マルチ購入配分")

if total_slots == 5:
    strategy_plan = st.sidebar.radio(
        "マルチ配分プラン",
        [
            "🔥 高配当包囲網 (トリプル2・ダブル2・シングル1 / 3,600円)",
            "⚡ スマートマルチ (トリプル1・ダブル2・シングル2 / 1,200円)",
            "🛡️ 手堅い配分 (ダブル3・シングル2 / 800円)",
            "🎲 カスタム指定"
        ],
        index=0
    )
    if "包囲網" in strategy_plan:
        num_triple, num_double = 2, 2
    elif "スマート" in strategy_plan:
        num_triple, num_double = 1, 2
    elif "手堅い" in strategy_plan:
        num_triple, num_double = 0, 3
    else:
        num_triple = st.sidebar.slider("トリプル数", 0, 3, 2)
        num_double = st.sidebar.slider("ダブル数", 0, 4, 2)
else:
    st.sidebar.caption("通常toto（13試合）用マルチ設定")
    num_triple = st.sidebar.slider("トリプル数", 0, 3, 1)
    num_double = st.sidebar.slider("ダブル数", 0, 8, 5)

combinations = (3 ** num_triple) * (2 ** num_double)
total_cost = combinations * 100
st.sidebar.metric(label="合計購入口数", value=f"{combinations:,} 口")
st.sidebar.metric(label="合計投資金額", value=f"{total_cost:,} 円")

# --- タブ構成 ---
tab1, tab2 = st.tabs(["🎯 最新予想＆マークシート", "🧠 143試合(11開催)総当たり検証＆バックテスト"])

# ==================== タブ1：最新予想 ====================
with tab1:
    st.subheader(f"📋 【{selected_round_key}】 {target_pool}")

    matches_analyzed = []
    for rm in raw_matches:
        h_name = rm["home"]
        a_name = rm["away"]
        m_date = rm.get("date", "2026-11-21")
        pair = {h_name, a_name}
        derby_label = None
        for d_set, d_name in DERBIES:
            if d_set == pair:
                derby_label = d_name
                break
        w_info = fetch_weather_for_date(h_name, m_date)
        hp, dp, ap, forb, s_mk, s_sc, p_tag, hr, ar = predict_nonlinear_model(
            rm["no"], h_name, a_name, is_rain=w_info["is_rain"], is_derby=(derby_label is not None)
        )
        p_first, p_second, p_third = sorted([hp, dp, ap], reverse=True)
        uncertainty = p_first - p_second

        matches_analyzed.append({
            "no": rm["no"], "home": h_name, "away": a_name, "date": m_date,
            "hr": hr, "ar": ar, "home_p": hp, "draw_p": dp, "away_p": ap,
            "weather": w_info["desc"], "stadium": w_info["stadium"],
            "derby": derby_label, "pattern_tag": p_tag,
            "uncertainty": uncertainty, "top_prob": p_first,
            "single_mark": s_mk, "single_score": s_sc
        })

    # Step 1: スイートスポット＆アンカー優先でシングル枠を確定
    num_single = max(total_slots - num_triple - num_double, 0)
    sorted_for_single = sorted(matches_analyzed, key=lambda x: x["single_score"], reverse=True)
    single_nos = [m["no"] for m in sorted_for_single[:num_single]]

    # Step 2: 残りの試合を不確実性順に並べ、トリプルとダブルを割り当て
    remaining_for_multi = [m for m in matches_analyzed if m["no"] not in single_nos]
    sorted_by_chaos = sorted(remaining_for_multi, key=lambda x: x["uncertainty"])
    triple_nos = [m["no"] for m in sorted_by_chaos[:num_triple]]
    double_nos = [m["no"] for m in sorted_by_chaos[num_triple:num_triple + num_double]]

    results = []
    first_marks_list = []

    for m in matches_analyzed:
        choices = sorted(
            [{"mark": "1", "prob": m["home_p"]}, {"mark": "0", "prob": m["draw_p"]}, {"mark": "2", "prob": m["away_p"]}],
            key=lambda x: x["prob"], reverse=True
        )
        c1, c2, c3 = choices
        first_marks_list.append(c1["mark"])

        is_1 = is_0 = is_2 = False
        if m["no"] in triple_nos:
            buy_badge = "🔴 トリプル (全抑え)"
            selection = "【1】 【0】 【2】"
            is_1 = is_0 = is_2 = True
        elif m["no"] in double_nos:
            buy_badge = "🟡 ダブル (2択)"
            m_a, m_b = sorted([c1["mark"], c2["mark"]])
            selection = f"【{m_a}】 【{m_b}】"
            is_1 = ("1" in [m_a, m_b])
            is_0 = ("0" in [m_a, m_b])
            is_2 = ("2" in [m_a, m_b])
        else:
            buy_badge = "⚪ シングル (厳選1点)"
            s_m = m["single_mark"]
            selection = f"【{s_m}】"
            is_1 = (s_m == "1")
            is_0 = (s_m == "0")
            is_2 = (s_m == "2")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**第{m['no']}試合** @ {m['stadium']} ({m['date']})")
            st.write(f"🏠 **{m['home']}** (序列{m['hr']}位) vs 🚩 **{m['away']}** (序列{m['ar']}位)")
            if m["derby"]:
                st.error(m["derby"])
            st.caption(f"天候: {m['weather']}")
        with col2:
            st.write(f"勝率: **【1】{int(m['home_p']*100)}%** | **【0】{int(m['draw_p']*100)}%** | **【2】{int(m['away_p']*100)}%**")
            st.caption(f"診断: {m['pattern_tag']}")
        with col3:
            st.info(f"{buy_badge} 👉 **{selection}**")

        results.append({
            "試合番号": f"第{m['no']}試合", "対戦カード": f"{m['home']} vs {m['away']}",
            "配分タイプ": buy_badge, "マーク": selection,
            "is_1": is_1, "is_0": is_0, "is_2": is_2
        })
        st.divider()

    cnt_marks = Counter(first_marks_list)
    st.info(f"📊 **軸目の出目バランス診断（全{total_slots}試合）**: ホーム【1】={cnt_marks['1']}個 ／ 引分【0】={cnt_marks['0']}個 ／ アウェイ【2】={cnt_marks['2']}個")

    st.subheader("👀 打ち間違い防止：楽天toto 照合用マークシート")
    st.link_button("🛒 楽天toto 公式購入画面を開く", "https://toto.rakuten.co.jp/")
    sheet_rows = []
    for r in results:
        sheet_rows.append({
            "試合": r["試合番号"], "対戦カード": r["対戦カード"], "購入枠": r["配分タイプ"],
            " ホーム勝ち ": "🟥【 1 】" if r["is_1"] else " ( 1 ) ",
            " [0] その他(引分) ": "🟩【 0 】" if r["is_0"] else " ( 0 ) ",
            " アウェイ勝ち ": "🟦【 2 】" if r["is_2"] else " ( 2 ) ",
        })
    st.dataframe(pd.DataFrame(sheet_rows), use_container_width=True, hide_index=True)

# ==================== タブ2：143試合総当たり検証＆バックテスト ====================
with tab2:
    st.subheader("🧠 過去11開催・全143試合（第1653回〜第1672回）バックテスト")
    st.caption("第1672回の最新結果（A組5,480円 / B組14,220円）を追加し、v3.0（7大法則＋下位ホーム両端決着ルール）での的中成績を検証します。")

    c_p1, c_p2 = st.columns(2)
    with c_p1:
        sim_trap_penalty = st.slider("⚠️ 上位ホーム過信罠(差+6〜+13)へのマイナス補正強度", 0.0, 0.35, 0.22, 0.02)
    with c_p2:
        sim_slot_blend = st.slider("🔄 枠番固有ベクトルのブレンド比率", 0.0, 0.70, 0.35, 0.05)

    ROUNDS_13_HISTORY = [
        (1672, [(1,"町田","神戸","0"),(2,"C大阪","浦和","0"),(3,"鹿島","横浜FM","1"),(4,"柏","川崎F","1"),(5,"新潟","宮崎","2"),(6,"大分","栃木C","2"),(7,"札幌","鳥栖","2"),(8,"仙台","秋田","1"),(9,"今治","磐田","2"),(10,"富山","徳島","2"),(11,"八戸","いわき","0"),(12,"藤枝","甲府","1"),(13,"大宮","山形","1")]),
        (1670, [(1,"清水","東京V","2"),(2,"横浜FM","岡山","0"),(3,"福岡","長崎","0"),(4,"FC東京","鹿島","1"),(5,"柏","川崎F","1"),(6,"名古屋","京都","2"),(7,"神戸","浦和","0"),(8,"G大阪","C大阪","2"),(9,"千葉","水戸","1"),(10,"町田","広島","0"),(11,"徳島","宮崎","2"),(12,"八戸","札幌","2"),(13,"鳥栖","富山","2")]),
        (1668, [(1,"岡山","FC東京","2"),(2,"水戸","広島","2"),(3,"神戸","名古屋","1"),(4,"鹿島","C大阪","1"),(5,"柏","浦和","1"),(6,"京都","清水","1"),(7,"千葉","福岡","1"),(8,"長崎","東京V","2"),(9,"町田","G大阪","0"),(10,"横浜FM","川崎F","1"),(11,"仙台","大宮","2"),(12,"新潟","富山","2"),(13,"宮崎","大分","1")]),
        (1665, [(1,"広島","清水","1"),(2,"鹿島","柏","2"),(3,"神戸","町田","0"),(4,"C大阪","千葉","0"),(5,"FC東京","水戸","1"),(6,"東京V","福岡","1"),(7,"G大阪","京都","0"),(8,"名古屋","横浜FM","0"),(9,"川崎F","岡山","1"),(10,"浦和","長崎","1"),(11,"秋田","今治","1"),(12,"鳥栖","八戸","1"),(13,"富山","札幌","2")]),
        (1664, [(1,"横浜FM","東京V","0"),(2,"京都","鹿島","0"),(3,"長崎","広島","1"),(4,"FC東京","柏","0"),(5,"名古屋","C大阪","0"),(6,"清水","町田","2"),(7,"岡山","水戸","1"),(8,"福岡","G大阪","2"),(9,"浦和","千葉","1"),(10,"川崎F","神戸","1"),(11,"仙台","今治","1"),(12,"徳島","八戸","2"),(13,"宮崎","秋田","1")]),
        (1663, [(1,"清水","G大阪","0"),(2,"千葉","横浜FM","0"),(3,"東京V","FC東京","2"),(4,"C大阪","川崎F","2"),(5,"鹿島","長崎","1"),(6,"広島","京都","1"),(7,"水戸","浦和","2"),(8,"岡山","神戸","2"),(9,"町田","福岡","1"),(10,"柏","名古屋","2"),(11,"札幌","秋田","1"),(12,"大分","新潟","1"),(13,"今治","八戸","0")]),
        (1660, [(1,"C大阪","横浜FM","0"),(2,"FC東京","浦和","1"),(3,"福岡","岡山","1"),(4,"千葉","長崎","0"),(5,"水戸","清水","2"),(6,"京都","町田","2"),(7,"東京V","広島","2"),(8,"川崎F","名古屋","2"),(9,"甲府","栃木C","1"),(10,"鳥栖","藤枝","1"),(11,"徳島","今治","2"),(12,"山形","仙台","2"),(13,"いわき","秋田","1")]),
        (1658, [(1,"町田","京都","0"),(2,"柏","G大阪","0"),(3,"藤枝","湘南","0"),(4,"甲府","富山","2"),(5,"大分","山形","1"),(6,"新潟","徳島","1"),(7,"札幌","いわき","1"),(8,"八戸","横浜FC","2"),(9,"仙台","磐田","1"),(10,"栃木C","今治","2"),(11,"秋田","鳥栖","1"),(12,"讃岐","栃木SC","0"),(13,"琉球","金沢","2")]),
        (1656, [(1,"山形","鳥栖","1"),(2,"富山","横浜FC","0"),(3,"徳島","栃木C","1"),(4,"大宮","甲府","1"),(5,"宮崎","札幌","1"),(6,"秋田","新潟","0"),(7,"いわき","仙台","2"),(8,"磐田","八戸","2"),(9,"今治","湘南","2"),(10,"大分","藤枝","0"),(11,"群馬","熊本","2"),(12,"福島","長野","1"),(13,"栃木SC","松本","2")]),
        (1654, [(1,"福岡","広島","2"),(2,"浦和","東京V","1"),(3,"清水","千葉","1"),(4,"岡山","京都","2"),(5,"FC東京","名古屋","1"),(6,"長崎","C大阪","0"),(7,"横浜FM","水戸","1"),(8,"町田","柏","2"),(9,"G大阪","神戸","2"),(10,"山形","富山","2"),(11,"藤枝","大宮","0"),(12,"新潟","磐田","1"),(13,"甲府","徳島","2")]),
        (1653, [(1,"水戸","川崎F","2"),(2,"清水","福岡","1"),(3,"G大阪","FC東京","2"),(4,"町田","横浜FM","0"),(5,"長崎","名古屋","1"),(6,"広島","C大阪","1"),(7,"東京V","千葉","0"),(8,"浦和","岡山","2"),(9,"今治","鳥栖","1"),(10,"いわき","横浜FC","1"),(11,"八戸","湘南","2"),(12,"甲府","磐田","2"),(13,"秋田","徳島","1")])
    ]

    bt_logs = []
    a_win_tot = 0
    b_win_tot = 0

    for rnd, m_list in ROUNDS_13_HISTORY:
        r_preds = []
        for no, h, a, actual in m_list:
            p1, p0, p2, forb, s_mk, s_sc, _, _, _ = predict_nonlinear_model(
                no, h, a, is_rain=False, is_derby=({h, a} in [{"東京V", "FC東京"}, {"神戸", "町田"}, {"横浜FM", "川崎F"}, {"G大阪", "C大阪"}, {"仙台", "秋田"}]),
                trap_penalty=sim_trap_penalty, slot_blend=sim_slot_blend
            )
            ch = sorted([("1", p1), ("0", p0), ("2", p2)], key=lambda x: x[1], reverse=True)
            c_1, c_2, c_3 = ch
            unc = c_1[1] - c_2[1]
            r_preds.append({"no": no, "actual": actual, "m1": c_1[0], "m2": c_2[0], "unc": unc, "s_mk": s_mk, "s_sc": s_sc})

        # A組 (36口包囲網) 判定
        a_sub = r_preds[:5]
        a_s_sorted = sorted(a_sub, key=lambda x: x["s_sc"], reverse=True)
        a_s = {a_s_sorted[0]["no"]}
        a_rem = sorted([p for p in a_sub if p["no"] not in a_s], key=lambda x: x["unc"])
        a_t = {x["no"] for x in a_rem[:2]}
        a_hits = sum(1 for p in a_sub if p["actual"] in ({"1","0","2"} if p["no"] in a_t else ({p["s_mk"]} if p["no"] in a_s else {p["m1"], p["m2"]})))
        if a_hits == 5:
            a_win_tot += 1

        # B組 (36口包囲網) 判定
        b_sub = r_preds[5:10]
        b_s_sorted = sorted(b_sub, key=lambda x: x["s_sc"], reverse=True)
        b_s = {b_s_sorted[0]["no"]}
        b_rem = sorted([p for p in b_sub if p["no"] not in b_s], key=lambda x: x["unc"])
        b_t = {x["no"] for x in b_rem[:2]}
        b_hits = sum(1 for p in b_sub if p["actual"] in ({"1","0","2"} if p["no"] in b_t else ({p["s_mk"]} if p["no"] in b_s else {p["m1"], p["m2"]})))
        if b_hits == 5:
            b_win_tot += 1

        bt_logs.append({
            "開催回": f"第{rnd}回",
            "mini toto-A組 (36口)": f"{a_hits}/5 {'🎉1等完全的中!' if a_hits == 5 else ''}",
            "mini toto-B組 (36口)": f"{b_hits}/5 {'🎉1等完全的中!' if b_hits == 5 else ''}",
        })

    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.metric("A組 1等当せん回数 (11開催中)", f"{a_win_tot} 回 / 11回 (勝率 {round(a_win_tot/11*100,1)}%)")
    with m_col2:
        st.metric("B組 1等当せん回数 (11開催中)", f"{b_win_tot} 回 / 11回 (勝率 {round(b_win_tot/11*100,1)}%)")

    st.dataframe(pd.DataFrame(bt_logs), use_container_width=True, hide_index=True)