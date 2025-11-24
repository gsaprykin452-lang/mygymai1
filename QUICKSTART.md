# Quick Start Guide

Get your GymGenius AI app running in 5 minutes!

## Step 1: Start Backend

Open terminal and run:

```bash
cd fitness-ai-app/backend
pip install -r requirements.txt
python main.py
```

You'll see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ Backend is running!

## Step 2: Start Mobile App

Open a **new** terminal and run:

```bash
cd fitness-ai-app/mobile
npm install
npm start
```

You'll see:
- Expo DevTools opens in browser
- QR code in terminal
- Instructions to run on simulator

## Step 3: Run on Device

### Option A: Physical Device
1. Install **Expo Go** app from App Store/Play Store
2. Scan the QR code from terminal

### Option B: iOS Simulator
Press `i` in the terminal (Mac only)

### Option C: Android Emulator
Press `a` in the terminal

## Testing the App

1. **Home Screen**: Tap "Scan Equipment"
2. **Camera**: Take a photo of any equipment
3. **Result**: See AI recognition with confidence score
4. **Exercises**: Browse recommended exercises
5. **Workout**: Generate a personalized workout plan

## API Testing

Test the backend directly:

```bash
curl http://localhost:8000/
# Response: {"message": "GymGenius AI API", "status": "running"}

curl http://localhost:8000/exercises
# Returns list of all exercises
```

## Troubleshooting

### Backend won't start
```bash
# Make sure you're in the backend directory
cd fitness-ai-app/backend
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Mobile app won't start
```bash
# Clear cache and reinstall
cd fitness-ai-app/mobile
rm -rf node_modules
npm install
npm start --reset-cache
```

### Camera not working
- Make sure camera permissions are granted
- For iOS: Check Info.plist for camera usage description
- For Android: Check AndroidManifest.xml for permissions

## Next Steps

- Collect real equipment images for training
- Train the ML model: `cd ml-model && python train_model.py`
- Add your own exercises to the database
- Customize the UI theme

## Development Tips

- Backend auto-reloads on code changes
- Mobile app hot-reloads (shake device to reload)
- Check terminal for errors
- API docs at: http://localhost:8000/docs

Happy coding! 💪

