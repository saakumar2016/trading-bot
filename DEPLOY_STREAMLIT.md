# 📋 Streamlit Cloud Deployment Checklist

Follow these steps to deploy safely to Streamlit Cloud without exposing secrets.

## ✅ Pre-Deployment (5 min)

1. **Verify secrets are protected**
   ```bash
   git status
   # Should NOT show: .env
   # Should NOT show: .streamlit/secrets.toml
   ```

2. **Check .gitignore**
   ```bash
   cat .gitignore | grep -E "\.env|secrets\.toml"
   # Should show both
   ```

3. **Verify code has no hardcoded tokens**
   ```bash
   grep -r "YOUR_TOKEN\|8720340833" . --include="*.py"
   # Should return nothing (only .env is ok)
   ```

4. **Run locally to test**
   ```bash
   streamlit run app.py
   # Should load without errors
   # Check that bot can access data
   ```

## 🚀 Deploy to Streamlit Cloud (5 min)

### Step 1: Push Code to GitHub
```bash
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

**Verify**: No `.env` in pushed files ✅

---

### Step 2: Create Streamlit App
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Select:
   - **Repository**: your-username/trading-bot
   - **Branch**: main
   - **Main file path**: app.py

Click **"Deploy"** (takes 2-3 minutes)

---

### Step 3: Add Secrets
Once deployed, your app is live but won't work yet (no token).

1. Click the **≡ menu** (top-right)
2. Select **Settings**
3. Go to **Secrets** tab
4. Copy-paste this template and fill in YOUR values:

```toml
# Paste this into Streamlit Cloud Secrets:

telegram_token = "YOUR_BOT_TOKEN"
chat_id = "YOUR_CHAT_ID"
symbol = "^NSEI"
timeframe = "1m"
refresh_interval = 10
log_level = "INFO"
```

**Where to get these?**
- `telegram_token`: From @BotFather on Telegram
- `chat_id`: From @userinfobot on Telegram
- Others: Keep defaults unless you know what you're doing

5. Click **Save**
6. App will auto-restart with secrets ✅

---

### Step 4: Verify Deployment
1. Go back to your app
2. Wait for it to restart (30-60 seconds)
3. Check:
   - Dashboard loads without errors
   - Market data appears
   - Try clicking **Backtest** and **Analysis** pages
   - Main metrics display correctly

✅ **Done! Your bot is live and safe!**

---

## 📱 Test Telegram Alerts (Optional)

1. Find a signal on the live dashboard
2. Check your Telegram chat
3. Should receive trade alert message

If not receiving:
- Check logs: Click ≡ menu → **Logs**
- Verify token and chat ID are correct
- Restart app: Click ≡ menu → **Reboot app**

---

## 🔄 Update Code Later

When you update code:

```bash
# Make changes locally
# Test with: streamlit run app.py

# Push to GitHub (secrets stay local, won't be pushed)
git add .
git commit -m "Update strategy parameters"
git push origin main

# Streamlit Cloud auto-detects changes
# App redeploys automatically (2-3 minutes)
```

**Secrets persist** - No need to re-enter them ✅

---

## 🚨 Emergency: Token Compromised

If your token is leaked:

1. **IMMEDIATELY** Go to @BotFather on Telegram
2. Select your bot → **Edit** → **Edit Commands** → back out
3. Or create **NEW bot** and get new token
4. Update Streamlit Cloud Secrets with new token
5. Verify messages still arrive

---

## 📊 Monitor Your Bot

**Check logs** (daily):
1. Click ≡ menu → **Logs**
2. Look for errors or warnings
3. Verify data is being fetched

**Check trades** (daily):
1. Go to **Data/Files** in your local project
2. Check `data/trades.csv` is growing
3. Download and analyze results

**Check alert history** (weekly):
1. Review Telegram chat
2. Verify alerts are triggering correctly
3. Adjust parameters if needed

---

## ⚠️ Important Reminders

- **Never commit `.env` or `secrets.toml`** - They're in `.gitignore`
- **Never share your token** - Treat like a password
- **Rotate tokens monthly** - Generate new ones periodically
- **Monitor for abuse** - Check Telegram for suspicious messages
- **Backup trades** - Download `data/trades.csv` regularly

---

## Quick Commands

```bash
# Test locally before deploying
streamlit run app.py

# Check what will be committed (should NOT include .env)
git status

# Check commit history for accidental secrets
git log --all --oneline -- .env

# Undo last commit if you accidentally committed secrets
git reset HEAD~1
```

---

## Support

- **Streamlit Docs**: https://docs.streamlit.io
- **Streamlit Cloud Secrets**: https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/secrets-management
- **Telegram Bot Docs**: https://core.telegram.org/bots
- **This Project**: Check README.md and DEPLOYMENT.md

**You're all set! 🚀**
