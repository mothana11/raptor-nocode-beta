# 🚀 Deploy Travel Chatbot on Replit

This guide will help you deploy the travel chatbot on Replit so your teammates can easily demo it.

## 📋 Quick Setup Steps

### 1. Create a Replit Account
- Go to [replit.com](https://replit.com)
- Sign up or log in to your account

### 2. Import Your Project
**Option A: From GitHub (Recommended)**
1. Push your code to GitHub first (if not already done)
2. In Replit, click "Create Repl"
3. Select "Import from GitHub"
4. Paste your repository URL
5. Click "Import from GitHub"

**Option B: Upload Files**
1. Create a new Python Repl
2. Upload all your project files to the Repl

### 3. Set Environment Variables
In your Replit project, go to the "Secrets" tab (🔒 icon in left sidebar) and add:

```
OPENAI_API_KEY=sk-your-openai-api-key-here
SECRET_KEY=your-jwt-secret-key-here
DATABASE_URL=sqlite:///./travel_chatbot.db
```

**To generate a SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Run the Project
1. Click the "Run" button in Replit
2. Wait for dependencies to install and frontend to build
3. Your app will be available at: `https://your-repl-name.your-username.repl.co`

## 🌐 Sharing Your Demo

### Public Access
- Your Replit URL is automatically public
- Share the URL with teammates: `https://your-repl-name.your-username.repl.co`
- No authentication required for viewers

### Features Available in Demo
✅ **User Registration & Login**
✅ **AI-powered travel assistance**
✅ **Flight search and booking**
✅ **Hotel search and booking**
✅ **Trip rescheduling**
✅ **Refund requests**
✅ **Voice input support**
✅ **File upload capabilities**
✅ **Persistent user data**

## 🔧 Troubleshooting

### Common Issues

**1. Dependencies not installing:**
- Make sure `replit.nix` and `requirements.txt` are present
- Try stopping and restarting the Repl

**2. Frontend not building:**
- Check that `frontend/package.json` exists
- Ensure Node.js is available in the environment

**3. Database errors:**
- The SQLite database will be created automatically
- User data persists across Repl restarts

**4. API key errors:**
- Verify `OPENAI_API_KEY` is set in Secrets
- Make sure the key has sufficient credits

### Performance Tips
- Replit may sleep after inactivity - first visit might be slow
- For production demos, consider upgrading to Replit Hacker plan
- Database is stored in Repl filesystem and persists

## 📊 Monitoring Demo Usage

### Analytics Available
- User registrations and logins
- Chat interactions and tool usage
- Booking attempts and completions
- User feedback and behavior patterns

### Viewing Analytics
1. Access the Repl console
2. Check the SQLite database for user data
3. Monitor server logs for real-time activity

## 🚀 Going Live

### Custom Domain (Optional)
1. Upgrade to Replit Hacker plan
2. Go to Settings → Custom Domain
3. Configure your domain to point to the Repl

### Production Considerations
- **Scale**: Replit works for demos; consider Railway/Vercel for production
- **Database**: Migrate to PostgreSQL for larger scale
- **Monitoring**: Add proper logging and error tracking
- **Security**: Review CORS settings for production use

## 🎯 Demo Script for Teammates

### Quick Demo Flow (5 minutes)
1. **Registration**: Show new user signup
2. **Voice Input**: Demonstrate voice-to-text feature
3. **Flight Search**: "Find flights from NYC to Paris"
4. **Hotel Booking**: "Book a hotel in Paris for 3 nights"
5. **File Upload**: Upload a travel document
6. **Rescheduling**: "Reschedule my flight to next week"
7. **Personalization**: Show how chatbot remembers preferences

### Key Features to Highlight
- 🤖 **AI-powered responses** using GPT-4
- 🎤 **Voice input** for hands-free interaction
- 📁 **File handling** for travel documents
- 🧠 **Memory** - remembers user preferences
- 🛡️ **Authentication** - secure user accounts
- 📱 **Responsive design** - works on mobile

---

**Need help?** Check the console logs or reach out to the development team! 