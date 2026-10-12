import io
import datetime
from zoneinfo import ZoneInfo
import math
import requests
import streamlit as st
import pandas as pd

# ページの基本設定
st.set_page_config(page_title="toto / mini toto 総合分析ナビゲーター", page_icon="⚽", layout="wide")

st.title("⚽ サッカーくじ toto / mini toto 統計分析ナビゲーター")
st.caption("J1・J2リーグ統計ベースライン、動的引き分けモデリング、およびバックテスト検証を統合した実戦分析システム。")

# --- 日本時間タイムゾーン ---
JST = ZoneInfo("Asia/Tokyo")
now = datetime.datetime.now(JST)

# --- J1・J2全スタジアム網羅データベース ---
STADIUM_DB = {
    # J1 & カップ戦会場
    "横浜FC": {"lat": 35.470, "lon": 139.603, "name": "ニッパツ", "roof": False},
    "横浜FM": {"lat": 35.510, "lon": 139.606, "name": "日産ス", "roof": False},
    "名古屋": {"lat": 35.122, "lon": 136.945, "name": "ヒマスタ", "roof": False},
    "鳥栖": {"lat": 33.372, "lon": 130.520, "name": "駅スタ", "roof": False},
    "磐田": {"lat": 34.724, "lon": 137.876, "name": "ヤマハ", "roof": False},
    "清水": {"lat": 34.985, "lon": 138.531, "name": "アイスタ", "roof": False},
    "浦和": {"lat": 35.903, "lon": 139.717, "name": "埼玉", "roof": False},
    "鹿島": {"lat": 35.991, "lon": 140.640, "name": "カシマ", "roof": False},
    "柏": {"lat": 35.848, "lon": 139.975, "name": "三協F柏", "roof": False},
    "FC東京": {"lat": 35.664, "lon": 139.527, "name": "味スタ", "roof": False},
    "町田": {"lat": 35.592, "lon": 139.438, "name": "Gスタ", "roof": False},
    "川崎F": {"lat": 35.586, "lon": 139.653, "name": "U等々力", "roof": False},
    "湘南": {"lat": 35.344, "lon": 139.349, "name": "レモンS", "roof": False},
    "新潟": {"lat": 37.882, "lon": 139.059, "name": "デンカS", "roof": False},
    "京都": {"lat": 35.000, "lon": 135.581, "name": "サンガS", "roof": False},
    "G大阪": {"lat": 34.809, "lon": 135.543, "name": "パナスタ", "roof": False},
    "C大阪": {"lat": 34.618, "lon": 135.518, "name": "ヨドコウ", "roof": False},
    "神戸": {"lat": 34.656, "lon": 135.169, "name": "ノエスタ", "roof": True},
    "広島": {"lat": 34.398, "lon": 132.453, "name": "Eピース", "roof": False},
    "福岡": {"lat": 33.585, "lon": 130.460, "name": "ベススタ", "roof": False},
    "岡山": {"lat": 34.681, "lon": 133.919, "name": "Cスタ", "roof": False},
}

# ダービーマッチ（接戦化ファクター）
DERBIES = [
    ({"鳥栖", "福岡"}, "🔥 九州ダービー"),
    ({"清水", "磐田"}, "🔥 静岡ダービー"),
    ({"横浜FM", "横浜FC"}, "🔥 横浜ダービー"),
    ({"G大阪", "C大阪"}, "🔥 大阪ダービー"),
    ({"横浜FM", "川崎F"}, "🔥 神奈川ダービー"),
    ({"FC東京", "東京V"}, "🔥 東京ダービー"),
]

# --- 開催回スケジュールマスター（全13試合完備） ---
ROUNDS_SCHEDULE = {
    "第1661回 (10/14 水 開催)": {
        "deadline": datetime.datetime(2026, 10, 14, 18, 20, 0, tzinfo=JST),
        "round_num": 1661,
        "matches": [
            # A組 (1-5)
            {"no": 1, "home": "横浜FC", "away": "浦和", "date": "2026-10-14"},
            {"no": 2, "home": "横浜FM", "away": "清水", "date": "2026-10-14"},
            {"no": 3, "home": "名古屋", "away": "岡山", "date": "2026-10-14"},
            {"no": 4, "home": "鳥栖", "away": "福岡", "date": "2026-10-14"},
            {"no": 5, "home": "磐田", "away": "川崎F", "date": "2026-10-14"},
            # B組 (6-10)
            {"no": 6, "home": "鹿島", "away": "G大阪", "date": "2026-10-14"},
            {"no": 7, "home": "町田", "away": "広島", "date": "2026-10-14"},
            {"no": 8, "home": "C大阪", "away": "神戸", "date": "2026-10-14"},
            {"no": 9, "home": "FC東京", "away": "柏", "date": "2026-10-14"},
            {"no": 10, "home": "湘南", "away": "新潟", "date": "2026-10-14"},
            # 通常toto (11-13)
            {"no": 11, "home": "京都", "away": "東京V", "date": "2026-10-14"},
            {"no": 12, "home": "千葉", "away": "甲府", "date": "2026-10-14"},
            {"no": 13, "home": "山形", "away": "長崎", "date": "2026-10-14"},
        ]
    },
    "第1662回 (10/17 土 開催)": {
        "deadline": datetime.datetime(2026, 10, 17, 13, 50, 0, tzinfo=JST),
        "round_num": 1662,
        "matches": [
            {"no": 1, "home": "浦和", "away": "鹿島", "date": "2026-10-17"},
            {"no": 2, "home": "町田", "away": "神戸", "date": "2026-10-17"},
            {"no": 3, "home": "G大阪", "away": "名古屋", "date": "2026-10-17"},
            {"no": 4, "home": "横浜FM", "away": "柏", "date": "2026-10-17"},
            {"no": 5, "home": "FC東京", "away": "清水", "date": "2026-10-17"},
        ]
    }
}

# --- 開催日連動のOpen-Meteo気象API ---
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
        weather_desc = f"{weather_icon} ({target_prob}%)"
        return {"desc": weather_desc, "is_rain": is_rain, "roof": info["roof"], "stadium": info["name"]}
    except Exception:
        return {"desc": "☀️ 晴れ (平年値)", "is_rain": False, "roof": info.get("roof", False), "stadium": info.get("name", "会場")}

# --- J1・J2順位表の自動取得 ---
@st.cache_data(ttl=3600)
def fetch_all_standings():
    headers = {"User-Agent": "Mozilla/5.0"}
    res_dict = {}
    
    try:
        u1 = "https://soccer.yahoo.co.jp/jleague/category/j1/standings"
        r1 = requests.get(u1, headers=headers, timeout=8)
        t1 = pd.read_html(io.StringIO(r1.text))
        if t1:
            df1 = t1[0]
            for _, row in df1.iterrows():
                name = str(row.get("チーム名", "")).strip()
                if name:
                    res_dict[name] = {
                        "category": "J1",
                        "rank": int(row.get("順位", 10)),
                        "pts": int(row.get("勝点", 10)),
                        "matches": int(row.get("試合", 25)),
                        "diff": int(row.get("得失点差", 0))
                    }
    except Exception:
        pass
        
    try:
        u2 = "https://soccer.yahoo.co.jp/jleague/category/j2/standings"
        r2 = requests.get(u2, headers=headers, timeout=8)
        t2 = pd.read_html(io.StringIO(r2.text))
        if t2:
            df2 = t2[0]
            for _, row in df2.iterrows():
                name = str(row.get("チーム名", "")).strip()
                if name:
                    res_dict[name] = {
                        "category": "J2",
                        "rank": int(row.get("順位", 10)),
                        "pts": int(row.get("勝点", 10)),
                        "matches": int(row.get("試合", 25)),
                        "diff": int(row.get("得失点差", 0))
                    }
    except Exception:
        pass
        
    return res_dict

standings_data = fetch_all_standings()

# チーム名エイリアス辞書
TEAM_ALIASES = {
    "C大阪": ["セレッソ大阪", "C大阪"], "G大阪": ["ガンバ大阪", "G大阪"],
    "横浜FM": ["横浜F・マリノス", "横浜FM"], "横浜FC": ["横浜FC"],
    "FC東京": ["FC東京"], "東京V": ["東京ヴェルディ", "東京V"],
    "川崎F": ["川崎フロンターレ", "川崎F"], "浦和": ["浦和レッズ", "浦和"],
    "鹿島": ["鹿島アントラーズ", "鹿島"], "柏": ["柏レイソル", "柏"],
    "町田": ["FC町田ゼルビア", "町田"], "湘南": ["湘南ベルマーレ", "湘南"],
    "新潟": ["アルビレックス新潟", "新潟"], "磐田": ["ジュビロ磐田", "磐田"],
    "名古屋": ["名古屋グランパス", "名古屋"], "京都": ["京都サンガF.C.", "京都"],
    "神戸": ["ヴィッセル神戸", "神戸"], "広島": ["サンフレッチェ広島", "広島"],
    "福岡": ["アビスパ福岡", "福岡"], "鳥栖": ["サガン鳥栖", "鳥栖"],
    "清水": ["清水エスパルス", "清水"], "千葉": ["ジェフユナイテッド千葉", "千葉"],
    "長崎": ["V・ファーレン長崎", "長崎"], "水戸": ["水戸ホーリーホック", "水戸"],
    "岡山": ["ファジアーノ岡山", "岡山"], "山形": ["モンテディオ山形", "山形"],
    "甲府": ["ヴァンフォーレ甲府", "甲府"],
}

def get_team_metrics(short_name):
    aliases = TEAM_ALIASES.get(short_name, [short_name])
    for cand in aliases:
        for scraped_name, metrics in standings_data.items():
            if cand == scraped_name or cand in scraped_name:
                return metrics
                
    FALLBACK_DB = {
        "広島": {"category": "J1", "rank": 1, "pts": 62, "matches": 32, "diff": 28},
        "神戸": {"category": "J1", "rank": 2, "pts": 61, "matches": 32, "diff": 24},
        "町田": {"category": "J1", "rank": 3, "pts": 59, "matches": 32, "diff": 21},
        "G大阪": {"category": "J1", "rank": 5, "pts": 53, "matches": 32, "diff": 12},
        "横浜FM": {"category": "J1", "rank": 6, "pts": 50, "matches": 32, "diff": 8},
        "FC東京": {"category": "J1", "rank": 7, "pts": 48, "matches": 32, "diff": 4},
        "C大阪": {"category": "J1", "rank": 8, "pts": 47, "matches": 32, "diff": 3},
        "浦和": {"category": "J1", "rank": 9, "pts": 45, "matches": 32, "diff": 2},
        "福岡": {"category": "J1", "rank": 10, "pts": 43, "matches": 32, "diff": -1},
        "川崎F": {"category": "J1", "rank": 11, "pts": 42, "matches": 32, "diff": 0},
        "名古屋": {"category": "J1", "rank": 12, "pts": 41, "matches": 32, "diff": -2},
        "磐田": {"category": "J1", "rank": 18, "pts": 32, "matches": 32, "diff": -15},
        "鳥栖": {"category": "J1", "rank": 20, "pts": 26, "matches": 32, "diff": -25},
        "清水": {"category": "J2", "rank": 1, "pts": 71, "matches": 32, "diff": 30},
        "横浜FC": {"category": "J2", "rank": 2, "pts": 69, "matches": 32, "diff": 28},
        "長崎": {"category": "J2", "rank": 3, "pts": 62, "matches": 32, "diff": 25},
        "千葉": {"category": "J2", "rank": 4, "pts": 55, "matches": 32, "diff": 18},
        "岡山": {"category": "J2", "rank": 5, "pts": 53, "matches": 32, "diff": 15},
    }
    return FALLBACK_DB.get(short_name, {"category": "J1", "rank": 10, "pts": 40, "matches": 30, "diff": 0})

# --- 統計的勝率推定エンジン ---
def estimate_match_probs(h_metrics, a_metrics, is_rain=False, is_derby=False,
                         home_adv=0.25, ppg_weight=0.65, draw_base=0.26):
    h_ppg = h_metrics["pts"] / max(h_metrics["matches"], 1)
    a_ppg = a_metrics["pts"] / max(a_metrics["matches"], 1)
    
    cat_offset = 0.0
    if h_metrics["category"] == "J1" and a_metrics["category"] == "J2":
        cat_offset = 0.50
    elif h_metrics["category"] == "J2" and a_metrics["category"] == "J1":
        cat_offset = -0.50
        
    ppg_diff = (h_ppg - a_ppg) + cat_offset
    derby_factor = 0.6 if is_derby else 1.0
    
    delta = ppg_diff * ppg_weight * derby_factor
    raw_home = math.exp(delta + home_adv)
    raw_away = math.exp(-delta)
    
    closeness = math.exp(-abs(delta) * 1.8)
    draw_prob = draw_base + (closeness * 0.05) + (0.05 if is_rain else 0.0)
    draw_prob = min(max(draw_prob, 0.18), 0.38)
    
    remain = 1.0 - draw_prob
    home_prob = remain * (raw_home / (raw_home + raw_away))
    away_prob = remain * (raw_away / (raw_home + raw_away))
    
    return round(home_prob, 3), round(draw_prob, 3), round(away_prob, 3)

# --- サイドバー操作 ---
st.sidebar.header("⚙️ システム設定")

if st.sidebar.button("🔄 最新データを更新・再取得"):
    st.cache_data.clear()
    st.rerun()

round_keys = list(ROUNDS_SCHEDULE.keys())
selected_round_key = st.sidebar.selectbox("🎟️ 対象の開催回", round_keys, index=0, key="r_selector")
current_round_data = ROUNDS_SCHEDULE[selected_round_key]
DEADLINE = current_round_data["deadline"]
all_matches_in_round = current_round_data["matches"]
round_num = current_round_data["round_num"]

# くじ種別の選択
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
    total_slots = len(raw_matches)

# 締切カウントダウン
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
st.sidebar.subheader("🎯 投資・マルチ購入配分")

if total_slots == 5:
    strategy_plan = st.sidebar.radio(
        "マルチ配分プラン",
        [
            "🔥 高配当狙い包囲網 (トリプル2・ダブル2・シングル1 / 3,600円)",
            "⚡ スマートマルチ (トリプル1・ダブル3・シングル1 / 2,400円)",
            "🛡️ 本命手堅い配分 (ダブル2・シングル3 / 400円)",
            "🎲 カスタム指定"
        ],
        index=0
    )
    if "包囲網" in strategy_plan:
        num_triple = 2
        num_double = 2
    elif "スマート" in strategy_plan:
        num_triple = 1
        num_double = 3
    elif "手堅い" in strategy_plan:
        num_triple = 0
        num_double = 2
    else:
        num_triple = st.sidebar.slider("トリプル数", 0, 3, 2)
        num_double = st.sidebar.slider("ダブル数", 0, 4, 2)
else:
    st.sidebar.caption("通常toto（13試合）用マルチ設定")
    num_double = st.sidebar.slider("ダブル数", 0, 8, 4)
    num_triple = st.sidebar.slider("トリプル数", 0, 3, 1)

combinations = (3 ** num_triple) * (2 ** num_double)
total_cost = combinations * 100

st.sidebar.metric(label="合計購入口数", value=f"{combinations:,} 口")
st.sidebar.metric(label="合計投資金額", value=f"{total_cost:,} 円")

total_combinations_pool = (3 ** total_slots)
coverage_rate = round((combinations / total_combinations_pool) * 100, 2)
st.sidebar.caption(f"全{total_combinations_pool:,}通り中 {combinations:,}通りをカバー（カバレッジ: {coverage_rate}%）")

# --- タブ構成 ---
tab1, tab2 = st.tabs(["🎯 最新予想・分析マークシート", "📈 バックテスト＆係数検証シミュレーター"])

# ==================== タブ1：最新予想 ====================
with tab1:
    st.subheader(f"📋 【{selected_round_key}】 {target_pool}")
    
    if remaining.total_seconds() > 0:
        st.info(f"⏳ **販売締切まで：あと {time_text}** （締切: {DEADLINE.strftime('%m/%d %H:%M')}）")
    else:
        st.warning("📢 この開催回の販売は終了しました。")

    matches_analyzed = []
    for rm in raw_matches:
        h_name = rm["home"]
        a_name = rm["away"]
        m_date = rm.get("date", "2026-10-14")
        
        h_m = get_team_metrics(h_name)
        a_m = get_team_metrics(a_name)
        
        pair = {h_name, a_name}
        derby_label = None
        for d_set, d_name in DERBIES:
            if d_set == pair:
                derby_label = d_name
                break
                
        w_info = fetch_weather_for_date(h_name, m_date)
        
        hp, dp, ap = estimate_match_probs(h_m, a_m, is_rain=w_info["is_rain"], is_derby=(derby_label is not None))
        
        p_first, p_second, p_third = sorted([hp, dp, ap], reverse=True)
        uncertainty = p_first - p_second
        
        matches_analyzed.append({
            "no": rm["no"],
            "home": h_name, "away": a_name, "date": m_date,
            "home_cat": h_m["category"], "away_cat": a_m["category"],
            "home_rank": h_m["rank"], "away_rank": a_m["rank"],
            "home_pts": h_m["pts"], "away_pts": a_m["pts"],
            "home_p": hp, "draw_p": dp, "away_p": ap,
            "weather": w_info["desc"], "stadium": w_info["stadium"],
            "derby": derby_label, "uncertainty": uncertainty,
            "top_prob": p_first
        })

    sorted_by_chaos = sorted(matches_analyzed, key=lambda x: x["uncertainty"])
    triple_nos = [m["no"] for m in sorted_by_chaos[:num_triple]]

    remaining_pool = [m for m in sorted_by_chaos[num_triple:]]
    sorted_by_reliability = sorted(remaining_pool, key=lambda x: x["top_prob"], reverse=True)

    num_single = max(total_slots - num_triple - num_double, 0)
    single_nos = [m["no"] for m in sorted_by_reliability[:num_single]]
    double_nos = [m["no"] for m in sorted_by_reliability[num_single:]]

    results = []
    for m in matches_analyzed:
        choices = [
            {"mark": "1", "prob": m["home_p"]},
            {"mark": "0", "prob": m["draw_p"]},
            {"mark": "2", "prob": m["away_p"]}
        ]
        choices = sorted(choices, key=lambda x: x["prob"], reverse=True)
        c1, c2, c3 = choices

        is_1 = is_0 = is_2 = False

        if m["no"] in triple_nos:
            buy_badge = "🔴 トリプル (全抑え)"
            selection = "【1】 【0】 【2】"
            is_1 = is_0 = is_2 = True
        elif m["no"] in double_nos:
            buy_badge = "🟡 ダブル (2択)"
            m_a, m_b = sorted([c1["mark"], c2["mark"]])
            selection = f"【{m_a}】 【{m_b}】"
            if "1" in [m_a, m_b]:
                is_1 = True
            if "0" in [m_a, m_b]:
                is_0 = True
            if "2" in [m_a, m_b]:
                is_2 = True
        else:
            buy_badge = "⚪ シングル (本命1点)"
            selection = f"【{c1['mark']}】"
            if c1["mark"] == "1":
                is_1 = True
            elif c1["mark"] == "0":
                is_0 = True
            elif c1["mark"] == "2":
                is_2 = True

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**第{m['no']}試合** @ {m['stadium']} ({m['date']})")
            st.write(f"🏠 **{m['home']}** ({m['home_cat']} {m['home_rank']}位/{m['home_pts']}pt) vs 🚩 **{m['away']}** ({m['away_cat']} {m['away_rank']}位/{m['away_pts']}pt)")
            if m["derby"]:
                st.error(m["derby"])
            st.caption(f"天候: {m['weather']}")
        with col2:
            st.write(f"モデル勝率: **【1】{int(m['home_p']*100)}%** | **【0】{int(m['draw_p']*100)}%** | **【2】{int(m['away_p']*100)}%**")
            st.caption(f"配分枠: {buy_badge}")
        with col3:
            st.info(f"買い目: **{selection}**")

        results.append({
            "試合番号": f"第{m['no']}試合",
            "対戦カード": f"{m['home']} vs {m['away']}",
            "配分タイプ": buy_badge,
            "マーク": selection,
            "is_1": is_1, "is_0": is_0, "is_2": is_2
        })
        st.divider()

    st.subheader("👀 打ち間違い防止：楽天toto 照合用マークシート")
    st.link_button("🛒 楽天toto 公式購入画面を開く", "https://toto.rakuten.co.jp/")
    sheet_rows = []
    for r in results:
        m1 = "🟥【 1 】" if r["is_1"] else " ( 1 ) "
        m0 = "🟩【 0 】" if r["is_0"] else " ( 0 ) "
        m2 = "🟦【 2 】" if r["is_2"] else " ( 2 ) "
        sheet_rows.append({
            "試合": r["試合番号"],
            "対戦カード": r["対戦カード"],
            "購入枠": r["配分タイプ"],
            " ホーム勝ち ": m1,
            " [0] その他(引分) ": m0,
            " アウェイ勝ち ": m2,
        })
    st.dataframe(pd.DataFrame(sheet_rows), use_container_width=True, hide_index=True)

# ==================== タブ2：バックテスト＆係数検証 ====================
with tab2:
    st.subheader("📈 統計係数の最適化シミュレーター")
    st.caption("スライダーで係数を調整し、過去の実績データ（第1653回〜第1659回）に対する的中率と回収率の変化を検証できます。")

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        param_home_adv = st.slider("ホームアドバンテージ補正", min_value=0.05, max_value=0.50, value=0.25, step=0.05)
    with col_p2:
        param_ppg_weight = st.slider("戦力差 (PPG) の感度係数", min_value=0.30, max_value=1.20, value=0.65, step=0.05)
    with col_p3:
        param_draw_base = st.slider("引き分けの基準発生率", min_value=0.18, max_value=0.35, value=0.26, step=0.02)

    PAST_ROUNDS = [
        {"round": 1659, "matches": [("広島", "いわき"), ("岡山", "千葉"), ("清水", "長崎"), ("鳥取", "東京V"), ("川崎F", "宮崎")], "actual": ["1", "1", "1", "2", "1"], "payout": 1910},
        {"round": 1658, "matches": [("町田", "京都"), ("柏", "G大阪"), ("藤枝", "湘南"), ("甲府", "富山"), ("大分", "山形")], "actual": ["1", "0", "0", "1", "2"], "payout": 38400},
        {"round": 1657, "matches": [("札幌", "岡山"), ("栃木SC", "広島"), ("磐田", "千葉"), ("金沢", "清水"), ("FC大阪", "福岡")], "actual": ["2", "2", "1", "2", "2"], "payout": 1810},
        {"round": 1656, "matches": [("山形", "鳥栖"), ("富山", "横浜FC"), ("徳島", "栃木SC"), ("大宮", "甲府"), ("宮崎", "札幌")], "actual": ["1", "0", "0", "1", "1"], "payout": 43510},
        {"round": 1655, "matches": [("鹿島", "甲府"), ("神戸", "鳥栖"), ("町田", "栃木SC"), ("G大阪", "徳島"), ("柏", "今治")], "actual": ["1", "1", "1", "1", "1"], "payout": 210},
        {"round": 1654, "matches": [("福岡", "広島"), ("浦和", "東京V"), ("清水", "千葉"), ("岡山", "京都"), ("FC東京", "名古屋")], "actual": ["2", "1", "1", "0", "1"], "payout": 11890},
        {"round": 1653, "matches": [("水戸", "川崎F"), ("清水", "福岡"), ("G大阪", "FC東京"), ("町田", "横浜FM"), ("長崎", "名古屋")], "actual": ["2", "1", "0", "2", "1"], "payout": 57810},
    ]

    total_cost_bt = 0
    total_payout_bt = 0
    win_count_bt = 0
    total_hits_bt = 0
    bt_logs = []

    for item in PAST_ROUNDS:
        r_matches = []
        for pair in item["matches"]:
            h_t, a_t = pair
            hm = get_team_metrics(h_t)
            am = get_team_metrics(a_t)
            hp, dp, ap = estimate_match_probs(
                hm, am, is_rain=False, is_derby=False,
                home_adv=param_home_adv, ppg_weight=param_ppg_weight, draw_base=param_draw_base
            )
            p_f, p_s, p_t = sorted([hp, dp, ap], reverse=True)
            r_matches.append({"home": h_t, "away": a_t, "hp": hp, "dp": dp, "ap": ap, "unc": p_f - p_s, "top_p": p_f})

        s_chaos = sorted(r_matches, key=lambda x: x["unc"])
        t_list = s_chaos[:2]
        rem = s_chaos[2:]
        s_rel = sorted(rem, key=lambda x: x["top_p"], reverse=True)
        s_list = s_rel[:1]
        d_list = s_rel[1:]

        hit_cnt = 0
        all_ok = True

        for act, m_obj in zip(item["actual"], r_matches):
            ch = sorted([("1", m_obj["hp"]), ("0", m_obj["dp"]), ("2", m_obj["ap"])], key=lambda x: x, reverse=True)
            c_f, c_s, c_t = ch
            if m_obj in t_list:
                allowed = ["1", "0", "2"]
            elif m_obj in d_list:
                allowed = [c_f[0], c_s[0]]
            else:
                allowed = [c_f[0]]

            if act in allowed:
                hit_cnt += 1
            else:
                all_ok = False

        c_cost = (3 ** 2) * (2 ** 2) * 100  # 36口 = 3,600円
        total_cost_bt += c_cost
        total_hits_bt += hit_cnt

        if all_ok:
            win_count_bt += 1
            pay = item["payout"]
            total_payout_bt += pay
            res_str = f"🎉 1等的中！ ({pay:,}円)"
        else:
            pay = 0
            res_str = f"不的中 ({hit_cnt}/5試合)"

        bt_logs.append({
            "開催回": f"第{item['round']}回",
            "投資額": f"{c_cost:,} 円",
            "的中試合数": f"{hit_cnt} / 5",
            "判定": res_str,
            "払戻金": f"{pay:,} 円",
            "収支": f"{pay - c_cost:,} 円"
        })

    bt_roi = round((total_payout_bt / total_cost_bt) * 100, 1) if total_cost_bt > 0 else 0
    bt_acc = round((total_hits_bt / (len(PAST_ROUNDS) * 5)) * 100, 1)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(label="シミュレーション通算回収率", value=f"{bt_roi} %", delta=f"{bt_roi - 100:.1f}%")
    with m2:
        st.metric(label="1等当せん数", value=f"{win_count_bt} 回 / {len(PAST_ROUNDS)}回中")
    with m3:
        st.metric(label="1試合平均的中率", value=f"{bt_acc} %")
    with m4:
        st.metric(label="通算純利益", value=f"{total_payout_bt - total_cost_bt:,} 円")

    st.write("")
    st.dataframe(pd.DataFrame(bt_logs), use_container_width=True, hide_index=True)