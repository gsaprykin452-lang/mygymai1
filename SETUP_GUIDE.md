# Setup Guide - GymGenius AI

Complete step-by-step guide to get your fitness AI app running.

## 🚀 Quick Setup (5 minutes)

### Step 1: Backend Setup

```bash
cd fitness-ai-app/backend
pip install -r requirements.txt
python main.py
```

Expected output:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**✅ Backend is ready!**

### Step 2: Mobile Setup

Open a **NEW terminal** window:

```bash
cd fitness-ai-app/mobile
npm install
npm start
```

Expected output:
```
› Metro waiting on exp://192.168.x.x:8081
› Scan the QR code above with Expo Go
```

**✅ Mobile app is ready!**

### Step 3: Run on Device

**Option A: Physical Phone**
1. Install **Expo Go** from App Store/Play Store
2. Scan the QR code from terminal
3. App opens automatically

**Option B: iOS Simulator (Mac only)**
- Press `i` in the terminal

**Option C: Android Emulator**
- Press `a` in the terminal

## 📱 Testing the App

### 1. Home Screen
- Tap **"Scan Equipment"** button
- Tap **"Generate Workout"** button

### 2. Camera Screen
- Tap the 📸 button to capture
- Equipment is recognized (mock data for now)
- See result screen with AI confidence

### 3. Exercise List
- Browse exercises for recognized equipment
- Tap any exercise to see details

### 4. Workout Generator
- Tap **"Generate Workout"** button
- Get personalized workout plan
- See duration, difficulty, and calories

## 🧪 API Testing

### Test Backend

```bash
# Health check
curl http://localhost:8000/

# Get all exercises
curl http://localhost:8000/exercises

# Get exercises for specific equipment
curl http://localhost:8000/exercises/Dumbbell

# Generate workout
curl http://localhost:8000/generate-workout?difficulty=beginner
```

### View API Docs
Open browser: http://localhost:8000/docs

## 🔧 Troubleshooting

### Problem: `pip install` fails
**Solution:**
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Problem: Expo won't start
**Solution:**
```bash
cd mobile
rm -rf node_modules
npm install
npm start --reset-cache
```

### Problem: Camera not working
**Solution:**
- Make sure camera permissions are granted
- For iOS: Go to Settings → Expo Go → Camera → Allow
- For Android: Tap "Grant Permission" button

### Problem: Backend won't connect
**Solution:**
- Check that backend is running: `python main.py`
- Verify port 8000 is not in use
- Try `http://127.0.0.1:8000` instead of `localhost`

### Problem: Database errors
**Solution:**
```bash
cd backend
rm *.db
python main.py
# Database will be recreated automatically
```

## 📁 Project Structure

```
fitness-ai-app/
├── mobile/              # React Native app
│   ├── App.js          # Main app
│   ├── src/screens/    # All screens
│   └── package.json
│
├── backend/            # FastAPI server
│   ├── main.py        # API routes
│   ├── database.py   # SQLite models
│   └── requirements.txt
│
└── ml-model/          # AI training
    └── train_model.py
```

## 🎨 What's Next?

### Immediate Next Steps
1. Collect real equipment images
2. Train the ML model
3. Test on real gym equipment

### Features to Add
- User accounts
- Workout history
- Progress tracking
- Social sharing
- Video demonstrations

### Improvements
- Real-time inference with TensorFlow Lite
- Offline mode
- Push notifications
- Multiple languages

## 💡 Development Tips

### Hot Reload
- **Backend:** Auto-restarts on code change
- **Mobile:** Shake device to reload, or `Cmd+R` (iOS)

### Debugging
```bash
# Backend logs
# Check terminal where you ran `python main.py`

# Mobile logs
# Enable remote debugging in Expo Go

# Database
# Check `backend/gymgenius.db` file
```

### Making Changes

**To add new exercises:**
Edit `backend/main.py` → `load_sample_data()` function

**To change UI:**
Edit files in `mobile/src/screens/`

**To test ML:**
Run `python ml-model/train_model.py`

## 📞 Support

- **Documentation:** See README.md
- **Project Overview:** See PROJECT_OVERVIEW.md
- **Quick Start:** See QUICKSTART.md

## ✨ You're All Set!

Your fitness AI app is now running. Start scanning gym equipment and generating workouts!

**Happy coding! 💪**

