
# VIVA PR War Room — Streamlit Cloud Deploy

Deploy this to **Streamlit Community Cloud** with no coding.

## 1) Create a GitHub repo
- Go to https://github.com → New repository → name it `viva-pr-war-room`
- Click **Upload files** and drag in these files from this folder:
  - `app.py`
  - `scoring.py`
  - `scenario_data.json`
  - `requirements.txt`

> Do **not** upload `.env.sample` to keep keys out of the repo (you'll add keys in Streamlit Secrets).

## 2) Deploy on Streamlit Cloud
- Go to https://share.streamlit.io → Sign in with GitHub.
- Click **Deploy an app**.
- Select your repo and set **Main file path** to `app.py`.
- Click **Deploy**.

First build takes ~2–3 minutes.

## 3) Add live data keys (optional)
- In your Streamlit app page → **Settings → Secrets**.
- Paste this (replace with your real keys):

```
NEWSAPI_KEY = "your_newsapi_key"
X_BEARER_TOKEN = "your_twitter_bearer_token"
```

- Save and **Reboot** the app when prompted.

## 4) Share with your team
- Use the app URL (e.g., `https://your-handle-streamlit.app`).
- Optional: In **Settings → Permissions**, require viewers to log in and restrict to your team's emails.

You're done.
