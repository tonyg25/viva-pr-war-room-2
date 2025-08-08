
import os
import time
import json
import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from dotenv import load_dotenv

from scoring import score_statement, score_decisions

st.set_page_config(page_title="VIVA PR War Room (Prototype)", layout="wide")

load_dotenv()
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "").strip()
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN", "").strip()

SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

@st.cache_data(ttl=120)
def get_news_uk():
    if not NEWSAPI_KEY:
        # Simulated news items
        return pd.DataFrame([
            {"time": datetime.utcnow().isoformat(timespec="seconds"), "source": "BBC (sim)", "title": "Universities face debate over campus speech policies", "url": ""},
            {"time": datetime.utcnow().isoformat(timespec="seconds"), "source": "Guardian (sim)", "title": "College suspends lecturer after social media controversy", "url": ""},
        ])
    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {"country": "gb", "pageSize": 20, "apiKey": NEWSAPI_KEY}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        rows = []
        for a in data.get("articles", []):
            rows.append({
                "time": a.get("publishedAt"),
                "source": a.get("source", {}).get("name"),
                "title": a.get("title"),
                "url": a.get("url"),
            })
        return pd.DataFrame(rows)
    except Exception as e:
        st.warning(f"NewsAPI error (showing simulated data): {e}")
        return pd.DataFrame([
            {"time": datetime.utcnow().isoformat(timespec="seconds"), "source": "BBC (sim)", "title": "Universities face debate over campus speech policies", "url": ""},
            {"time": datetime.utcnow().isoformat(timespec="seconds"), "source": "Guardian (sim)", "title": "College suspends lecturer after social media controversy", "url": ""},
        ])

def get_tweets(query: str):
    if not X_BEARER_TOKEN:
        return pd.DataFrame([
            {"created_at": datetime.utcnow().isoformat(timespec="seconds"), "text": "Free speech under attack again. Academic freedom is dead. (simulated)", "retweets": 23, "likes": 120},
            {"created_at": datetime.utcnow().isoformat(timespec="seconds"), "text": "Racism has no place on campus — due process matters. (simulated)", "retweets": 12, "likes": 88},
        ])
    try:
        headers = {"Authorization": f"Bearer {X_BEARER_TOKEN}"}
        url = "https://api.twitter.com/2/tweets/search/recent"
        params = {
            "query": query,
            "max_results": 10,
            "tweet.fields": "created_at,lang,public_metrics"
        }
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        rows = []
        for t in data.get("data", []):
            pm = t.get("public_metrics", {})
            rows.append({
                "created_at": t.get("created_at"),
                "text": t.get("text"),
                "retweets": pm.get("retweet_count", 0),
                "likes": pm.get("like_count", 0)
            })
        if not rows:
            return pd.DataFrame([{"created_at": datetime.utcnow().isoformat(timespec="seconds"), "text": "No recent tweets found for this query.", "retweets": 0, "likes": 0}])
        return pd.DataFrame(rows)
    except Exception as e:
        st.warning(f"Twitter API error (showing simulated data): {e}")
        return pd.DataFrame([
            {"created_at": datetime.utcnow().isoformat(timespec="seconds"), "text": "Free speech under attack again. Academic freedom is dead. (simulated)", "retweets": 23, "likes": 120},
            {"created_at": datetime.utcnow().isoformat(timespec="seconds"), "text": "Racism has no place on campus — due process matters. (simulated)", "retweets": 12, "likes": 88},
        ])

@st.cache_resource
def load_scenario():
    with open("scenario_data.json", "r") as f:
        return json.load(f)

scenario = load_scenario()

st.title("VIVA PR War Room — Live Prototype")
st.caption("Live UK headlines + live social (optional) + crisis simulation + scoring + replay")

with st.sidebar:
    st.subheader("Quick Setup")
    st.write("• Optional: add API keys in a `.env` file for live data.")
    st.write("• Without keys, the app runs in demo mode with simulated data.")
    st.markdown("**Keys:** `NEWSAPI_KEY`, `X_BEARER_TOKEN`")
    st.divider()
    st.subheader("Navigation")
    page = st.radio("Go to", ["Dashboard", "Live Headlines", "Live Social", "Scenario Player", "Take Actions & Score", "Replay Sessions"])

if page == "Dashboard":
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### UK Headlines (last 2 min)")
        news = get_news_uk()
        st.dataframe(news, use_container_width=True)
    with col2:
        st.markdown("### Social Snapshot")
        q = st.text_input("Quick query", '("free speech" OR "free expression") (campus OR college) lang:en -is:retweet')
        tweets = get_tweets(q)
        st.dataframe(tweets, use_container_width=True)

elif page == "Live Headlines":
    st.markdown("### Live UK Headlines")
    news = get_news_uk()
    st.dataframe(news, use_container_width=True)

elif page == "Live Social":
    st.markdown("### Live Social (Twitter/X Recent Search)")
    q = st.text_input("Query", '("free speech" OR "free expression") (campus OR college) lang:en -is:retweet')
    if st.button("Fetch", type="primary"):
        tweets = get_tweets(q)
        st.dataframe(tweets, use_container_width=True)
    else:
        st.info("Enter a query and click Fetch. (Works with or without API key; falls back to simulated posts.)")

elif page == "Scenario Player":
    st.markdown(f"### Scenario: {scenario['title']}")
    st.write("**Baseline sentiment:**", scenario["baseline_sentiment"])
    if "sim_start" not in st.session_state:
        st.session_state.sim_start = None

    colA, colB = st.columns([1,2])
    with colA:
        if st.button("▶ Start / Restart Simulation", type="primary"):
            st.session_state.sim_start = time.time()
        elapsed = 0
        if st.session_state.sim_start:
            elapsed = int((time.time() - st.session_state.sim_start)//60) + 1  # minutes
        minute = st.slider("Minute", 0, 60, value=min(60, elapsed))
        st.caption("Tip: press Start to auto-advance each minute; or drag the slider.")

    with colB:
        st.markdown("#### Event Feed")
        evs = [e for e in scenario["events"] if e.get("minute", 0) <= minute]
        if not evs:
            st.write("Awaiting first event...")
        else:
            for e in evs:
                et = e.get("type")
                st.write("---")
                if et == "headline":
                    st.markdown(f"**T+{e['minute']}m – Headline ({e['source']}):** {e['title']} _(tone: {e.get('tone','n/a')})_")
                elif et == "tweet":
                    st.markdown(f"**T+{e['minute']}m – Tweet {e['handle']} ({e['followers']:,} followers):** {e['text']}")
                elif et == "email":
                    st.markdown(f"**T+{e['minute']}m – Email from {e['from']}:** {e['subject']} — {e['body']}")
                elif et == "media_request":
                    st.markdown(f"**T+{e['minute']}m – Media request ({e['from']}):** {e['request']}")
                elif et == "trend":
                    st.markdown(f"**T+{e['minute']}m – Hashtag Trend:** {e['hashtag']} — {e['mentions_30m']:,} mentions")
                elif et == "post":
                    st.markdown(f"**T+{e['minute']}m – {e['platform']} ({e['actor']}):** {e['text']}")
                elif et == "linkedin":
                    st.markdown(f"**T+{e['minute']}m – LinkedIn ({e['actor']}):** {e['text']}")
                elif et == "tv":
                    st.markdown(f"**T+{e['minute']}m – TV ({e['source']}):** {e['segment']} — {e['format']}")
                elif et == "opportunity":
                    st.markdown(f"**T+{e['minute']}m – Opportunity:** {e['title']} — {e['question']}")
                elif et == "internal":
                    st.markdown(f"**T+{e['minute']}m – Internal note:** {e['text']}")
                elif et == "wrap":
                    st.markdown(f"**T+{e['minute']}m – Wrap summary:** {e['summary']}")

elif page == "Take Actions & Score":
    st.markdown("### Submit your actions and get instant feedback")
    with st.form("actions_form"):
        st.subheader("Holding Statement")
        statement = st.text_area("Paste your holding statement here", height=220)
        st.subheader("Decision Points")
        respond_now = st.selectbox("T+8 min — Respond now or delay?", ["Respond now with holding statement", "Delay pending internal review"])
        bbc_request = st.selectbox("T+25 min — BBC Today request", ["Accept live principal interview", "Decline and issue written statement", "Offer deputy spokesperson instead"])
        charity_story = st.selectbox("T+45 min — Push charity story now or hold?", ["Push now", "Hold"])
        submitted = st.form_submit_button("Get Score", type="primary")

    if submitted:
        st.write("---")
        s = score_statement(statement)
        d = score_decisions({
            "respond_now": respond_now,
            "bbc_request": bbc_request,
            "charity_story": charity_story
        })
        total = min(100, s["score"] * 0.7 + d["score"])  # weight statement 70, decisions 30
        st.metric("Overall Score", f"{int(total)}/100")
        st.write("**Statement feedback:**")
        for n in s["notes"]:
            st.write("•", n)
        st.write("**Decision feedback:**")
        for n in d["notes"]:
            st.write("•", n)

        # Save session
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        session_data = {
            "timestamp_utc": ts,
            "statement": statement,
            "statement_breakdown": s,
            "decisions": {
                "respond_now": respond_now,
                "bbc_request": bbc_request,
                "charity_story": charity_story
            },
            "decisions_breakdown": d,
            "overall": int(total)
        }
        path = os.path.join(SESSIONS_DIR, f"session_{ts}.json")
        with open(path, "w") as f:
            json.dump(session_data, f, indent=2)
        st.success(f"Saved session: {path}")

elif page == "Replay Sessions":
    st.markdown("### Replay & Debrief")
    files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")]
    if not files:
        st.info("No saved sessions yet. Run a score first.")
    else:
        choice = st.selectbox("Choose a session", files)
        if choice:
            with open(os.path.join(SESSIONS_DIR, choice), "r") as f:
                data = json.load(f)
            st.json(data)
            st.metric("Overall Score", f"{data.get('overall', 0)}/100")
            st.write("**Statement feedback:**")
            for n in data.get("statement_breakdown", {}).get("notes", []):
                st.write("•", n)
            st.write("**Decision feedback:**")
            for n in data.get("decisions_breakdown", {}).get("notes", []):
                st.write("•", n)

