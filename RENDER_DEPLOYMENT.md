# 🚀 Render Deployment Guide - JIRA Automation

Deploy your JIRA automation system to Render in minutes! Render offers free tier with automatic deployments from GitHub.

---

## ✨ Why Render?

- ✅ **Free Tier Available** - Perfect for this project
- ✅ **Auto-Deploy from GitHub** - Push code, auto-deploy
- ✅ **Easy Setup** - No complex configuration
- ✅ **Built-in SSL** - HTTPS by default
- ✅ **Background Workers** - For scheduled tasks
- ✅ **Environment Variables** - Secure credential management

---

## 📋 Prerequisites

- ✅ GitHub account with your code: https://github.com/surac95/jira-studio-lab
- ✅ Render account (free): https://render.com

---

## 🎯 Step-by-Step Deployment

### Step 1: Create Render Account

1. Go to https://render.com
2. Click **"Get Started"**
3. Sign up with your GitHub account (recommended)
4. Authorize Render to access your repositories

---

### Step 2: Deploy Flask Web Service

1. **From Render Dashboard**, click **"New +"** → **"Web Service"**

2. **Connect Repository**:
   - Select: `surac95/jira-studio-lab`
   - Click **"Connect"**

3. **Configure Web Service**:
   ```
   Name: jira-automation-flask
   Region: Oregon (US West)
   Branch: master
   Root Directory: jira-automation
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python flask_app.py
   ```

4. **Select Plan**:
   - Choose **"Free"** plan
   - Click **"Advanced"**

5. **Add Environment Variables**:
   Click **"Add Environment Variable"** for each:
   
   ```
   JIRA_URL = https://jira.issworld.com
   JIRA_PAT_TOKEN = your_actual_token_here
   JIRA_PROJECT_KEY = ITSD
   JIRA_QUEUE_JQL = resolution = Unresolved AND "Resolver Group" = "FMS AMS Level 4 Integrations" and assignee is EMPTY ORDER BY created DESC
   
   MISTRAL_API_KEY = your_actual_mistral_key_here
   
   SLACK_BOT_TOKEN = xoxb-your-actual-token-here
   SLACK_CHANNEL_ID = C07XXXXXXXXX
   
   LOG_LEVEL = INFO
   FLASK_ENV = production
   PORT = 5000
   ```

6. **Create Web Service**:
   - Click **"Create Web Service"**
   - Wait 2-3 minutes for deployment
   - You'll get a URL like: `https://jira-automation-flask.onrender.com`

---

### Step 3: Deploy Background Worker (Scheduler)

1. **From Render Dashboard**, click **"New +"** → **"Background Worker"**

2. **Connect Repository**:
   - Select: `surac95/jira-studio-lab`
   - Click **"Connect"**

3. **Configure Background Worker**:
   ```
   Name: jira-automation-scheduler
   Region: Oregon (US West)
   Branch: master
   Root Directory: jira-automation
   Runtime: Python 3
   Build Command: pip install -r requirements.txt && pip install schedule==1.2.0
   Start Command: python scheduler.py
   ```

4. **Select Plan**:
   - Choose **"Free"** plan

5. **Add Environment Variables**:
   Same as Step 2 (copy from Flask service or add manually):
   
   ```
   JIRA_URL = https://jira.issworld.com
   JIRA_PAT_TOKEN = your_actual_token_here
   JIRA_PROJECT_KEY = ITSD
   JIRA_QUEUE_JQL = resolution = Unresolved AND "Resolver Group" = "FMS AMS Level 4 Integrations" and assignee is EMPTY ORDER BY created DESC
   
   MISTRAL_API_KEY = your_actual_mistral_key_here
   
   SLACK_BOT_TOKEN = xoxb-your-actual-token-here
   SLACK_CHANNEL_ID = C07XXXXXXXXX
   
   LOG_LEVEL = INFO
   ```

6. **Create Background Worker**:
   - Click **"Create Background Worker"**
   - Wait 2-3 minutes for deployment

---

### Step 4: Configure Slack Interactive URL

1. **Get your Render URL** from Step 2 (e.g., `https://jira-automation-flask.onrender.com`)

2. **Go to Slack App Settings**:
   - Visit: https://api.slack.com/apps
   - Select your app
   - Go to **"Interactivity & Shortcuts"**

3. **Enable Interactivity**:
   - Toggle **"Interactivity"** to **ON**
   - Set **Request URL**: `https://jira-automation-flask.onrender.com/slack/interactive`
   - Click **"Save Changes"**

4. **Test the URL**:
   - Slack will verify the URL
   - Should show ✅ "Verified"

---

## 🎉 Deployment Complete!

Your system is now running on Render:

### What's Running:

1. **Flask Web Service** 🌐
   - URL: `https://jira-automation-flask.onrender.com`
   - Handles Slack interactive buttons
   - Always available (with free tier limitations)

2. **Background Worker** ⚙️
   - Runs scheduler every hour
   - Processes JIRA tickets automatically
   - Sends Slack notifications

---

## 📊 Monitor Your Services

### View Logs:

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click on your service** (Flask or Scheduler)
3. **Click "Logs" tab**
4. **View real-time logs**

### Check Service Status:

- **Green dot** = Running ✅
- **Yellow dot** = Deploying 🔄
- **Red dot** = Failed ❌

---

## 🔧 Update Your Application

### Automatic Deployment:

1. **Make changes** to your code locally
2. **Commit and push** to GitHub:
   ```bash
   git add .
   git commit -m "Update feature"
   git push origin master
   ```
3. **Render auto-deploys** within 1-2 minutes!

### Manual Deployment:

1. Go to Render Dashboard
2. Click on your service
3. Click **"Manual Deploy"** → **"Deploy latest commit"**

---

## 💰 Free Tier Limitations

### What You Get (Free):

- ✅ 750 hours/month web service
- ✅ Unlimited background workers
- ✅ Auto-deploy from GitHub
- ✅ Free SSL certificates
- ✅ Custom domains

### Limitations:

- ⚠️ Web service sleeps after 15 min of inactivity
- ⚠️ Takes ~30 seconds to wake up
- ⚠️ 512 MB RAM per service

### Solutions:

1. **Keep-Alive Service** (Optional):
   - Use a free uptime monitor (e.g., UptimeRobot)
   - Ping your URL every 10 minutes
   - Prevents sleep

2. **Upgrade to Paid** ($7/month):
   - No sleep
   - More resources
   - Better performance

---

## 🐛 Troubleshooting

### Service Won't Start:

1. **Check Logs** in Render Dashboard
2. **Verify Environment Variables** are set correctly
3. **Check Build Command** succeeded
4. **Ensure requirements.txt** is correct

### Slack Interactive Not Working:

1. **Verify URL** in Slack App settings
2. **Check Flask service** is running (green dot)
3. **Test URL** manually: `https://your-app.onrender.com/health`
4. **Check Logs** for errors

### Scheduler Not Running:

1. **Check Background Worker** logs
2. **Verify Environment Variables**
3. **Ensure schedule package** is installed
4. **Check for Python errors** in logs

### Environment Variables Not Loading:

1. **Go to Service Settings**
2. **Click "Environment"** tab
3. **Verify all variables** are present
4. **Re-deploy** after adding variables

---

## 🔐 Security Best Practices

### Protect Your Credentials:

1. ✅ **Never commit** `.env` file to GitHub
2. ✅ **Use Render's** environment variables
3. ✅ **Rotate tokens** regularly
4. ✅ **Use secret scanning** on GitHub

### Monitor Access:

1. Check Render access logs
2. Review Slack app permissions
3. Monitor JIRA API usage

---

## 📈 Scaling Options

### When to Upgrade:

- More than 750 hours/month needed
- Need faster response times
- Want to avoid sleep
- Need more RAM/CPU

### Upgrade Path:

1. **Starter Plan** ($7/month):
   - No sleep
   - 512 MB RAM
   - Better performance

2. **Standard Plan** ($25/month):
   - 2 GB RAM
   - More CPU
   - Priority support

---

## 🎯 Quick Reference

### Important URLs:

- **Render Dashboard**: https://dashboard.render.com
- **Your Flask App**: `https://jira-automation-flask.onrender.com`
- **Slack App Settings**: https://api.slack.com/apps
- **GitHub Repo**: https://github.com/surac95/jira-studio-lab

### Common Commands:

```bash
# View logs
# Go to Render Dashboard → Service → Logs

# Redeploy
# Dashboard → Service → Manual Deploy

# Update environment variables
# Dashboard → Service → Environment → Add/Edit

# Check service status
# Dashboard → Services (green/yellow/red dots)
```

---

## ✅ Deployment Checklist

- [ ] Render account created
- [ ] GitHub repository connected
- [ ] Flask web service deployed
- [ ] Background worker deployed
- [ ] Environment variables configured
- [ ] Slack interactive URL updated
- [ ] Services showing green (running)
- [ ] Logs checked for errors
- [ ] Test ticket processed successfully
- [ ] Slack notifications working

---

## 🆘 Need Help?

1. **Check Logs First**: Most issues show up in logs
2. **Render Documentation**: https://render.com/docs
3. **Render Community**: https://community.render.com
4. **Review this guide**: Step-by-step instructions above

---

## 🎊 Success!

Your JIRA automation is now running 24/7 on Render!

**What happens now:**
- ✅ Scheduler runs every hour
- ✅ Processes up to 10 tickets per run
- ✅ Sends Slack notifications
- ✅ Handles interactive buttons
- ✅ Auto-deploys on code changes
- ✅ Logs everything for debugging

**Enjoy your automated JIRA ticket management!** 🚀

---

Made with ❤️ for seamless automation