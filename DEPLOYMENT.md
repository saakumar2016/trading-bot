# 🚀 Deployment Guide

This guide explains how to deploy the Trading Bot safely without exposing secrets.

## Quick Start

**Key Principle**: Secrets (tokens, credentials) are NEVER committed to GitHub. They're managed separately per environment.

## Local Development Setup

### 1. Copy .env template
```bash
cp .env.example .env
```

### 2. Fill in your credentials
```env
TELEGRAM_TOKEN=your_bot_token_here
CHAT_ID=your_chat_id_here
SYMBOL=^NSEI
TIMEFRAME=1m
REFRESH_INTERVAL=10
LOG_LEVEL=INFO
```

### 3. Run locally
```bash
source venv/bin/activate
streamlit run app.py
```

✅ **`.env` is in `.gitignore` - it will NOT be pushed to GitHub**

---

## Streamlit Cloud Deployment (Recommended)

### Step 1: Push code to GitHub (without secrets)

```bash
# Make sure .env is NOT tracked
git status  # Should NOT show .env file

# Commit and push
git add .
git commit -m "Add trading bot"
git push origin main
```

✅ **Only code is pushed, no tokens**

### Step 2: Connect to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your GitHub repo, branch, and `app.py` as the main file

### Step 3: Add Secrets in Streamlit Cloud UI

1. Click the **≡ menu** (top-right of your deployed app)
2. Select **"Settings"**
3. Go to **"Secrets"** tab
4. Enter your secrets in TOML format:

```toml
telegram_token = "8720340833:AAHk_..."
chat_id = "5647013625"
symbol = "^NSEI"
timeframe = "1m"
refresh_interval = 10
log_level = "INFO"
```

5. Click **"Save"**

✅ **Secrets are stored securely on Streamlit's servers**

---

## Alternative: Local Streamlit Secrets (Development)

For testing Streamlit secrets locally before deployment:

### 1. Create local secrets file
```bash
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

### 2. Edit `.streamlit/secrets.toml`
```toml
telegram_token = "your_token_here"
chat_id = "your_chat_id"
symbol = "^NSEI"
timeframe = "1m"
```

### 3. Run locally
```bash
streamlit run app.py
```

✅ **`.streamlit/secrets.toml` is in `.gitignore` - safe**

---

## Configuration Priority

The bot loads configuration in this order (first match wins):

1. **Streamlit Secrets** (`.streamlit/secrets.toml` or Streamlit Cloud Secrets)
2. **Environment Variables** (`.env` file)
3. **Default Values** (in `config.py`)

This means:
- ✅ Local dev: Uses `.env`
- ✅ Streamlit Cloud: Uses cloud secrets
- ✅ Docker: Can use environment variables

---

## Docker Deployment

### 1. Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Set environment variables (can be overridden at runtime)
ENV TELEGRAM_TOKEN=""
ENV CHAT_ID=""
ENV SYMBOL="^NSEI"
ENV TIMEFRAME="1m"
ENV REFRESH_INTERVAL="10"
ENV LOG_LEVEL="INFO"

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. Build image
```bash
docker build -t trading-bot .
```

### 3. Run with secrets
```bash
docker run -e TELEGRAM_TOKEN="your_token" \
           -e CHAT_ID="your_chat_id" \
           -p 8501:8501 \
           trading-bot
```

---

## Environment Variable Methods

Choose one for your deployment platform:

### Heroku
```bash
heroku config:set TELEGRAM_TOKEN="your_token"
heroku config:set CHAT_ID="your_chat_id"
```

### AWS / GCP / Azure
Use their Secrets Manager or environment variables in deployment settings

### GitHub Actions (CI/CD)
```yaml
env:
  TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
  CHAT_ID: ${{ secrets.CHAT_ID }}
```

---

## Security Checklist

Before pushing to GitHub:

- [ ] Run `git status` and verify `.env` is NOT listed
- [ ] Run `git log --all --full-history -- .env` to check if ever committed
- [ ] Verify `.gitignore` includes `.env` and `.streamlit/secrets.toml`
- [ ] Check for hardcoded tokens in Python files (should use config.py)
- [ ] Test with dummy token locally before deploying

If you accidentally committed secrets:

1. **REVOKE THE TOKEN IMMEDIATELY** (Telegram BotFather)
2. Use `git filter-branch` or `BFG Repo-Cleaner` to remove from history
3. Generate new token
4. Force push (be careful!)

---

## Troubleshooting

### ❌ "TELEGRAM_TOKEN not set"
- Local: Add to `.env` file
- Streamlit Cloud: Go to Settings → Secrets and add `telegram_token`
- Docker: Pass `-e TELEGRAM_TOKEN="..."` flag

### ❌ "Could not fetch data"
- Check internet connection
- yfinance may be rate-limited from cloud (wait 5 min)
- Check logs in Streamlit Cloud for errors

### ✅ How to verify secrets are loaded
Look for logs showing which configuration source is used.

---

## Best Practices

1. **Never hardcode secrets** - Always use environment variables or .streamlit/secrets.toml
2. **Use .gitignore properly** - Verify files won't be committed
3. **Rotate tokens regularly** - Regenerate in Telegram BotFather periodically
4. **Use specific permissions** - Telegram bot should only have message sending permission
5. **Monitor for abuse** - Check Telegram message history for unusual activity
6. **Keep backups** - Backup your trade history (`data/trades.csv`) regularly

---

## Summary

| Environment | Method | File | Gitignored |
|-------------|--------|------|-----------|
| **Local Dev** | `.env` | `.env` | ✅ Yes |
| **Streamlit Cloud** | Web UI | Cloud secrets | ✅ Yes (cloud) |
| **Docker** | Environment vars | N/A | ✅ N/A |
| **Heroku** | Heroku CLI | N/A | ✅ Cloud managed |

**No matter the deployment method, your secrets are safe!** ✅
