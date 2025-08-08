# 🚀 Deploy to Replit - Quick Guide

## Step 1: Import from GitHub
1. Go to [replit.com](https://replit.com)
2. Click "Create Repl"
3. Choose "Import from GitHub"
4. Enter: `https://github.com/mothana11/raptor-nocode-beta.git`
5. Click "Import"

## Step 2: Configure Environment Variables
1. In your Replit, go to "Tools" → "Secrets"
2. Add these environment variables:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   SECRET_KEY=your_secret_key_here
   RAPID_API_KEY=your_rapid_api_key_here
   AMADEUS_CLIENT_ID=your_amadeus_client_id_here
   AMADEUS_CLIENT_SECRET=your_amadeus_client_secret_here
   AMADEUS_ACCESS_TOKEN=your_amadeus_access_token_here
   ```

## Step 3: Run the Project
1. Click the "Run" button
2. The script will automatically:
   - Install Python dependencies
   - Build the frontend (if npm is available)
   - Create the environment file
   - Start the server

## Step 4: Access Your App
- Your app will be available at the Replit URL
- The frontend will be served from the backend
- Share the URL with your colleagues for demo

## Troubleshooting

### If you see "python: command not found"
- ✅ Fixed! The script now uses `python3`

### If you see "npm: command not found"
- ✅ Fixed! The script now checks for npm and skips frontend build if not available

### If the server doesn't start
- Check the console for error messages
- Make sure all environment variables are set in Replit Secrets
- Try running `python3 -m uvicorn main:app --host 0.0.0.0 --port 8000` manually

## Demo Features Ready
- ✅ AI-powered chat interface
- ✅ Real flight search via Amadeus API
- ✅ Real hotel search via Booking.com API
- ✅ User authentication system
- ✅ Booking management

Your travel chatbot is now ready for demo! 🎉 