# 🚂 Deploy Travel Chatbot on Railway (Private Repo)

Railway is perfect for keeping your code private while sharing a public demo with your teammates.

## 🚀 Quick Setup (5 minutes)

### 1. Create Railway Account
- Go to [railway.app](https://railway.app)
- Sign up with your GitHub account
- Railway automatically gets access to your private repos

### 2. Deploy from Private GitHub Repo
1. **Click "New Project"**
2. **Select "Deploy from GitHub repo"**
3. **Choose your private `raptor-nocode-beta` repository**
4. **Railway will auto-detect it's a Python project**

### 3. Configure Environment Variables
In Railway dashboard → **Variables** tab, add:
```
OPENAI_API_KEY=sk-your-openai-api-key-here
SECRET_KEY=your-jwt-secret-key-here
DATABASE_URL=sqlite:///./travel_chatbot.db
PORT=8000
```

### 4. Configure Build Settings
In Railway dashboard → **Settings** tab:
- **Build Command:** `cd frontend && npm install && npm run build && cd ../backend && pip install -r requirements.txt`
- **Start Command:** `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Root Directory:** Leave blank (uses project root)

### 5. Deploy
- Click **"Deploy"**
- Railway builds and deploys automatically
- You get a public URL: `https://your-app-name.up.railway.app`

## 🌐 Share with Teammates

### ✅ **What Your Teammates Get:**
- **Public demo URL** (no Railway account needed)
- **Full travel chatbot functionality**
- **User registration and login**
- **AI-powered chat with voice input**
- **File uploads and booking features**

### 🔒 **What Stays Private:**
- **Your source code** (only you can see it)
- **Your GitHub repository**
- **Environment variables and secrets**
- **Database and user data**

## 🛠 **Automatic Features**

### Railway Provides:
- ✅ **HTTPS by default**
- ✅ **Custom domain support**
- ✅ **Automatic deployments** (on git push)
- ✅ **Built-in monitoring and logs**
- ✅ **PostgreSQL database** (if you want to upgrade from SQLite)
- ✅ **Persistent storage** for SQLite
- ✅ **Zero-config Docker deployment**

## 💡 **Alternative: Use Railway CLI**

If you prefer command line:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up
```

## 🔄 **Continuous Deployment**

Once set up:
1. **Push to GitHub** → Railway auto-deploys
2. **Environment changes** → Update via Railway dashboard
3. **Zero downtime** deployments
4. **Rollback support** if needed

## 📊 **Monitoring Your Demo**

### Railway Dashboard Shows:
- **Real-time logs** of user interactions
- **Performance metrics** (CPU, memory, requests)
- **Database usage** and user registrations
- **Deployment history** and status

### Your App Logs Show:
- User logins and registrations
- Chat interactions and AI responses
- Booking attempts and completions
- File uploads and voice input usage

## 💰 **Pricing**

### Railway Free Tier:
- **$5/month** in free credits
- **Enough for demos** and development
- **No credit card required** to start

### Upgrade Options:
- **Pro Plan:** $20/month for production use
- **Custom domains** and advanced features

## 🎯 **Demo Script for Teammates**

Share this with your teammates along with the Railway URL:

### "Try Our AI Travel Assistant!"
1. **Visit:** `https://your-app-name.up.railway.app`
2. **Register** a new account
3. **Test voice input:** Click microphone and say "Find flights to Paris"
4. **Upload a document:** Try uploading a travel itinerary
5. **Make a booking:** Follow through with a flight or hotel booking
6. **Reschedule/Refund:** Test the modification features

## 🆚 **Railway vs Other Options**

| Feature | Railway | Vercel | Render | Heroku |
|---------|---------|--------|---------|---------|
| Private repos | ✅ | ✅ | ✅ | ✅ |
| Full-stack apps | ✅ | ⚠️ | ✅ | ✅ |
| Database included | ✅ | ❌ | ✅ | ⚠️ |
| Free tier | ✅ | ✅ | ✅ | ❌ |
| Easy setup | ✅ | ✅ | ✅ | ✅ |

**Railway wins** for full-stack apps with databases!

---

**Need help?** Railway has excellent docs and support for any deployment issues! 