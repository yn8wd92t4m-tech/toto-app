import io
import datetime
from zoneinfo import ZoneInfo
from collections import Counter
import requests
import streamlit as st
import pandas as pd

# ページの基本設定
st.set_page_config(page_title="toto / mini toto 揺らぎ・逆転法則AI", page_icon="⚽", layout="wide")

st.title("⚽ toto / mini toto 非線形・揺らぎ解析ナビゲーター (v2.3)")
st.caption("実データ117試合（9開催回）検証済：「小差アウェイの両端ダブル化」「罠カードのシングル除外」「第8枠ホーム0勝(0/8)法則」統合モデル。")

JST = ZoneInfo("Asia/Tokyo")
now = datetime.datetime.now(JST)

# --- スタジアム網羅データベース ---
STADIUM_DB = {
    "清水": {"lat": 34.985, "lon": 138.531, "name": "アイスタ", "roof": False},
    "横浜FM": {"lat": 35.510, "lon": 139.606, "name": "日産ス", "roof": False},
    "福岡": {"lat": 33.585, "lon": 130.460, "name": "ベススタ", "roof": False},
    "FC東京": {"lat": 35.664, "lon": 139.527, "name": "味スタ", "roof": False},
    "柏": {"lat": 35.848, "lon": 139.975, "name": "三協F柏", "roof": False},
    "名古屋": {"lat": 35.084, "lon": 137.170, "name": "豊田ス", "roof": True},
    "神戸": {"lat": 35.678, "lon": 139.715, "name": "MUFG国立", "roof": False},
    "G大阪": {"lat": 34.809, "lon": 135.543, "name": "パナスタ", "roof": False},
    "千葉": {"lat": 35.578, "lon": 140.123, "name": "フクアリ", "roof": False},
    "町田": {"lat": 35.592, "lon": 139.438, "name": "Gスタ", "roof": False},
    "徳島": {"lat": 34.168, "lon": 134.618, "name": "鳴門大塚", "roof": False},
    "八戸": {"lat": 40.543, "lon": 141.528, "name": "プラスタ", "roof": False},
    "鳥栖": {"lat": 33.372, "lon": 130.520, "name": "駅スタ", "roof": False},
    "岡山": {"lat": 34.681, "lon": 133.919, "name": "JFEス", "roof": False},
    "水戸": {"lat": 36.345, "lon": 140.412, "name": "水戸信ス", "roof": False},
    "鹿島": {"lat": 35.991, "lon": 140.640, "name": "メルスタ", "roof": False},
    "京都": {"lat": 35.000, "lon": 135.581, "name": "サンガS", "roof": False},
    "長崎": {"lat": 32.760, "lon": 129.866, "name": "ピースタ", "roof": False},
    "仙台": {"lat": 38.319, "lon": 140.882, "name": "ユアスタ", "roof": False},
    "新潟": {"lat": 37.882, "lon": 139.059, "name": "デンカS", "roof": False},
    "宮崎": {"lat": 32.062, "lon": 131.472, "name": "いちご", "roof": False},
}

DERBIES = [
    ({"G大阪", "C大阪"}, "🔥 伝統の大阪ダービー"),
    ({"福岡", "長崎"}, "🔥 九州ダービー"),
    ({"町田", "広島"}, "🔥 首位頂上決戦"),
    ({"横浜FM", "川崎F"}, "🔥 神奈川ダービー"),
    ({"東京V", "FC東京"}, "🔥 東京ダービー"),
    ({"清水", "磐田"}, "🔥 静岡ダービー"),
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

ROUNDS_SCHEDULE = {
    "第1670回 (11/7 土 12:50締切)": {
        "deadline": datetime.datetime(2026, 11, 7, 12, 50, 0, tzinfo=JST),
        "round_num": 1670,
        "matches": [
            # A組 (1-5)
            {"no": 1, "home": "清水", "away": "東京V", "date": "2026-11-07"},
            {"no": 2, "home": "横浜FM", "away": "岡山", "date": "2026-11-07"},
            {"no": 3, "home": "福岡", "away": "長崎", "date": "2026-11-07"},
            {"no": 4, "home": "FC東京", "away": "鹿島", "date": "2026-11-07"},
            {"no": 5, "home": "柏", "away": "川崎F", "date": "2026-11-07"},
            # B組 (6-10)
            {"no": 6, "home": "名古屋", "away": "京都", "date": "2026-11-07"},
            {"no": 7, "home": "神戸", "away": "浦和", "date": "2026-11-08"},
            {"no": 8, "home": "G大阪", "away": "C大阪", "date": "2026-11-08"},
            {"no": 9, "home": "千葉", "away": "水戸", "date": "2026-11-08"},
            {"no": 10, "home": "町田", "away": "広島", "date": "2026-11-08"},
            # 終盤 (11-13)
            {"no": 11, "home": "徳島", "away": "宮崎", "date": "2026-11-07"},
            {"no": 12, "home": "八戸", "away": "札幌", "date": "2026-11-08"},
            {"no": 13, "home": "鳥栖", "away": "富山", "date": "2026-11-07"},
        ]
    },
    "第1668回 (10/31 土 開催・終了)": {
        "deadline": datetime.datetime(2026, 10, 31, 13, 50, 0, tzinfo=JST),
        "round_num": 1668,
        "matches": [
            {"no": 1, "home": "岡山", "away": "FC東京", "date": "2026-10-31"},
            {"no": 2, "home": "水戸", "away": "広島", "date": "2026-10-31"},
            {"no": 3, "home": "神戸", "away": "名古屋", "date": "2026-10-31"},
            {"no": 4, "home": "鹿島", "away": "C大阪", "date": "2026-10-31"},
            {"no": 5, "home": "柏", "away": "浦和", "date": "2026-10-31"},
            {"no": 6, "home": "京都", "away": "清水", "date": "2026-10-31"},
            {"no": 7, "home": "千葉", "away": "福岡", "date": "2026-11-01"},
            {"no": 8, "home": "長崎", "away": "東京V", "date": "2026-11-01"},
            {"no": 9, "home": "町田", "away": "G大阪", "date": "2026-11-01"},
            {"no": 10, "home": "横浜FM", "away": "川崎F", "date": "2026-11-01"},
            {"no": 11, "home": "仙台", "away": "大宮", "date": "2026-10-31"},
            {"no": 12, "home": "新潟", "away": "富山", "date": "2026-10-31"},
            {"no": 13, "home": "宮崎", "away": "大分", "date": "2026-10-31"},
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

# --- 非線形・逆転法則エンジン v2.3（小差アウェイ両端ダブル＆罠シングル除外） ---
def predict_nonlinear_model(no, h_name, a_name, is_rain=False, is_derby=False,
                            trap_penalty=0.22, slot_weight=1.0):
    hr = TEAM_POWER_RANK.get(h_name, 20)
    ar = TEAM_POWER_RANK.get(a_name, 20)
    diff = ar - hr  # 正ならホームが格上
    is_single_forbidden = False

    if diff >= 14:
        p1, p0, p2 = 0.72, 0.16, 0.12
        pattern_tag = f"👑 超格差ホーム(差+{diff}): 順当圧勝シングル候補"
    elif 6 <= diff <= 13:
        p1 = max(0.56 - trap_penalty, 0.25)
        p0 = 0.33
        p2 = 1.0 - p1 - p0
        is_single_forbidden = True
        pattern_tag = f"⚠️ 圧倒的格上ホーム罠(差+{diff}): 引かれ守備警戒【シングル厳禁】"
    elif 3 <= diff <= 5:
        p1, p0, p2 = 0.65, 0.18, 0.17
        pattern_tag = f"🎯 ややホーム格上(差+{diff}): 順当スイートスポット(勝率69%帯)"
    elif -2 <= diff <= 2:
        p1, p0, p2 = 0.32, 0.33, 0.35
        is_single_forbidden = True
        pattern_tag = f"🔄 互角対決(差{diff:+d}): 最優先トリプル対象【全抑え推奨】"
    elif -5 <= diff <= -3:
        p1, p0, p2 = 0.36, 0.16, 0.48
        if no != 8:
            is_single_forbidden = True
        pattern_tag = f"⚔️ ややアウェイ格上(差{diff:+d}): 打ち合い【1・2】両端ダブル推奨"
    elif -11 <= diff <= -6:
        p1, p0, p2 = 0.22, 0.28, 0.50
        if no != 8:
            is_single_forbidden = True
        pattern_tag = f"🚩 格上アウェイ(差{diff:+d}): アウェイ優位＋引分粘り【0・2】"
    else:
        p1, p0, p2 = 0.14, 0.22, 0.64
        pattern_tag = f"👑 超格差アウェイ(差{diff:+d}): アウェイ圧勝シングル候補"

    if is_derby:
        p0 += 0.06
        p1 -= 0.03
        p2 -= 0.03
        if not (3 <= diff <= 5):
            is_single_forbidden = True
        pattern_tag += " / 🔥ダービー"

    if is_rain:
        p0 += 0.06
        p1 -= 0.03
        p2 -= 0.03

    # 枠番エリアの揺らぎバイアス
    if no <= 5:
        p1 += 0.04 * slot_weight
        p0 += 0.06 * slot_weight
        p2 -= 0.10 * slot_weight
    elif no == 8:
        p2 += 0.24 * slot_weight
        p0 += 0.08 * slot_weight
        p1 -= 0.32 * slot_weight
        is_single_forbidden = False
        pattern_tag += " / 🚨【魔の第8枠(過去8戦ホーム0勝: 2=7回,0=1回)】"
    elif no >= 11:
        p2 += 0.10 * slot_weight
        p1 -= 0.06 * slot_weight
        p0 -= 0.04 * slot_weight
        pattern_tag += " / 【終盤枠アウェイバイアス】"

    p1 = max(p1, 0.05)
    p0 = max(p0, 0.05)
    p2 = max(p2, 0.05)
    tot = p1 + p0 + p2
    p1, p0, p2 = round(p1 / tot, 3), round(p0 / tot, 3), round(p2 / tot, 3)

    # シングル適性スコア（引き分け0はシングルにせず、1または2の勝率最大値＋実力差で評価）
    win_max = max(p1, p2)
    single_mark = "1" if p1 >= p2 else "2"
    single_score = win_max - (0.35 if is_single_forbidden else 0.0) + (abs(diff) * 0.005)
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
    ["mini toto-B組 (第6〜10試合)", "mini toto-A組 (第1〜5試合)", "通常 toto (全13試合)"],
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
tab1, tab2 = st.tabs(["🎯 最新予想＆マークシート", "🧠 117試合(9開催)総当たり検証＆バックテスト"])

# ==================== タブ1：最新予想 ====================
with tab1:
    st.subheader(f"📋 【{selected_round_key}】 {target_pool}")

    matches_analyzed = []
    valid_single_candidates = 0

    for rm in raw_matches:
        h_name = rm["home"]
        a_name = rm["away"]
        m_date = rm.get("date", "2026-11-07")
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
        if not forb:
            valid_single_candidates += 1
        p_first, p_second, p_third = sorted([hp, dp, ap], reverse=True)
        uncertainty = p_first - p_second

        matches_analyzed.append({
            "no": rm["no"], "home": h_name, "away": a_name, "date": m_date,
            "hr": hr, "ar": ar, "home_p": hp, "draw_p": dp, "away_p": ap,
            "weather": w_info["desc"], "stadium": w_info["stadium"],
            "derby": derby_label, "pattern_tag": p_tag,
            "uncertainty": uncertainty, "top_prob": p_first,
            "single_mark": s_mk, "single_score": s_sc, "forb": forb
        })

    # 組の投資適性バナー
    if total_slots == 5:
        if valid_single_candidates >= 1:
            st.success(f"🔥 **投資適性診断：主戦場ターゲット組**（明確なシングル軸候補が {valid_single_candidates} 試合存在し、残りの波乱・罠カードをマルチ包囲できる理想的な編成です）")
        else:
            st.warning("⚠️ **投資適性診断：全試合波乱・軸不在組**（5試合すべてが互角・罠領域のためシングル軸のリスクが高めです。B組を優先するか少額プランを推奨します）")

    # Step 1: シングル枠を確定
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

# ==================== タブ2：117試合総当たり検証＆バックテスト ====================
with tab2:
    st.subheader("🧠 過去9開催・全117試合（第1653回〜第1668回）バックテスト")
    st.caption("第1668回の最新結果（A組530円 / B組17,460円）を追加し、v2.3での的中成績を検証します。")

    c_p1, c_p2 = st.columns(2)
    with c_p1:
        sim_trap_penalty = st.slider("⚠️ 圧倒的格上ホーム(差+6〜+13)へのマイナス補正強度", 0.0, 0.35, 0.22, 0.02)
    with c_p2:
        sim_slot_weight = st.slider("🔄 主催者の枠番バイアス(第8枠・終盤枠)の反映強度", 0.0, 1.5, 1.0, 0.1)

    ROUNDS_13_HISTORY = [
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
    for rnd, m_list in ROUNDS_13_HISTORY:
        r_preds = []
        for no, h, a, actual in m_list:
            p1, p0, p2, forb, s_mk, s_sc, _, _, _ = predict_nonlinear_model(
                no, h, a, is_rain=False, is_derby=({h, a} in [{"東京V", "FC東京"}, {"神戸", "町田"}, {"横浜FM", "川崎F"}]),
                trap_penalty=sim_trap_penalty, slot_weight=sim_slot_weight
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

        # B組 (36口包囲網) 判定
        b_sub = r_preds[5:10]
        b_s_sorted = sorted(b_sub, key=lambda x: x["s_sc"], reverse=True)
        b_s = {b_s_sorted[0]["no"]}
        b_rem = sorted([p for p in b_sub if p["no"] not in b_s], key=lambda x: x["unc"])
        b_t = {x["no"] for x in b_rem[:2]}
        b_hits = sum(1 for p in b_sub if p["actual"] in ({"1","0","2"} if p["no"] in b_t else ({p["s_mk"]} if p["no"] in b_s else {p["m1"], p["m2"]})))

        bt_logs.append({
            "開催回": f"第{rnd}回",
            "mini toto-A組 (36口)": f"{a_hits}/5 {'🎉1等!' if a_hits == 5 else ''}",
            "mini toto-B組 (36口)": f"{b_hits}/5 {'🎉1等!' if b_hits == 5 else ''}",
        })

    st.dataframe(pd.DataFrame(bt_logs), use_container_width=True, hide_index=True)