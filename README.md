# GymGenius AI - Fitness Equipment Recognition App

A complete fitness AI application that uses computer vision to recognize gym equipment and provide personalized workout recommendations.

## 🎯 Features

- **Camera-based equipment recognition** using TensorFlow Lite (Mobile)
- **File upload recognition** for web platform
- **Exercise library** with instructions for each equipment type
- **Video demonstrations** for proper form
- **Workout generator** that creates personalized plans
- **Real-time AI inference** on mobile device
- **Responsive web design** for all screen sizes
- **Cross-platform compatibility** (iOS, Android, Web)
- **Complete web application** with all mobile features

## 📁 Project Structure

```
fitness-ai-app/
├── mobile/                 # React Native app with Expo
│   ├── src/
│   │   └── screens/       # App screens
│   ├── App.js             # Main app component
│   └── package.json       # Dependencies
├── backend/               # FastAPI server
│   ├── main.py           # API endpoints
│   ├── database.py       # Database models
│   └── requirements.txt   # Python dependencies
├── ml-model/             # AI model training
│   ├── train_model.py    # Training script
│   └── README.md         # Model documentation
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites

- Node.js 16+
- Python 3.8+
- Expo CLI

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install backend dependencies
pip install -r backend/requirements.txt

# Install ML dependencies
pip install -r ml-model/requirements.txt
```

### 2. Setup Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

The API will be available at `http://localhost:8000`

#### OpenAI ChatGPT setup (optional, for AI guidance)

Set your OpenAI API key as an environment variable before starting the backend:

```bash
# PowerShell
$env:OPENAI_API_KEY = "YOUR_KEY_HERE"

# bash
export OPENAI_API_KEY="YOUR_KEY_HERE"
```

You can get your API key from https://platform.openai.com/api-keys

New endpoint:

```http
POST /ai/guidance
{
  "equipment": "Bench",
  "locale": "ru"
}
```

Response contains `description`, `exercises` (name, muscles, steps[]) and `safety`.

### 2. Setup Mobile App

```bash
cd mobile
npm install
npm start
```

Then scan the QR code with Expo Go app on your phone, or press `i` for iOS simulator.

**For real devices (Expo Go):**

If you're using Expo Go on a real device, you need to configure the backend IP address:

1. Find your computer's local IP address:
   - Windows: `ipconfig` (look for IPv4 Address)
   - Mac/Linux: `ifconfig` or `ip addr`

2. Set the backend URL before starting Expo:
   ```bash
   # Windows PowerShell
   $env:BACKEND_URL="http://YOUR_IP:8000"
   npm start
   
   # Mac/Linux
   export BACKEND_URL="http://YOUR_IP:8000"
   npm start
   ```

   Example: `$env:BACKEND_URL="http://192.168.1.100:8000"`

3. Make sure your phone and computer are on the same Wi-Fi network.

4. Ensure the backend is running and accessible from your network (check firewall settings).

### 3. 🌐 Web Version

```bash
cd mobile
npm install
npm run web
```

**If you get web dependency errors, run:**
```bash
npx expo install react-native-web@~0.19.6 react-dom@18.2.0
```

**If you get static rendering errors, run:**
```bash
npx expo install @expo/metro-runtime
npm start -- --clear
```

**If you see a white screen, run:**
```bash
npm install @react-navigation/native@^7.0.0 @react-navigation/native-stack@^7.0.0
npm start -- --clear
```

**If Expo Go complains about SDK version, run:**
```bash
npm install expo@~54.0.0 react-native@0.75.4
npm start -- --clear
```

**If you get PlatformConstants error, run:**
```bash
npm install @react-navigation/native@^6.1.18 @react-navigation/native-stack@^6.11.0
npm start -- --clear
```

**If you get Bridgeless mode error, run:**
```bash
npm start -- --clear
# Then restart Expo Go on your device
```

**If Expo still gives errors, do a full reset:**
```bash
cd mobile
rm -rf node_modules .expo package-lock.json
npm install
npx expo install --fix
npm start -- --clear
```

The web app will be available at `http://localhost:19006`

**Web Features:**
- ✅ **Full functionality** - all screens and features work
- ✅ **File upload** instead of camera for equipment recognition
- ✅ **Responsive design** for all screen sizes
- ✅ **Complete API integration** with backend
- ✅ **Dark theme** optimized for web
- ✅ **Navigation** between all screens
- ✅ **Exercise library** and workout generator

See `WEB_SETUP.md` for detailed web setup instructions.

### 3. API Endpoints

**Recognition:**
- `POST /recognize` - Upload image and get equipment recognition
- `POST /recognize/candidates` - Get top-k candidates for confirmation

**Exercises & Equipment:**
- `GET /exercises/{equipment_name}` - Get exercises for equipment
- `GET /exercises` - Get all exercises
- `GET /equipment/all` - Get all equipment with descriptions
- `GET /equipment/{equipment_name}/details` - Get detailed equipment info with exercises

**AI & Planning:**
- `POST /ai/guidance` - AI guidance for equipment (OpenAI ChatGPT or mock)
- `POST /ai/chat` - **Full AI chat assistant** for any training questions (OpenAI ChatGPT)
- `POST /user/analyze` - Validate/enrich user profile
- `POST /plan/generate` - Personalized plan by equipment + user
- `GET /generate-workout` - Generate workout plan

**User & History:**
- `GET /user/profile` - Get saved user profile
- `POST /user/profile` - Create/update user profile
- `POST /history/log` - Log a finished exercise set
- `GET /history/recent` - Recent workout history

**Admin:**
- `POST /admin/populate-db` - Populate database with extended equipment data

## 🌍 Multi-Language Support

The app supports 5 languages:
- 🇬🇧 **English** (en)
- 🇷🇺 **Russian** (ru) - Default
- 🇫🇷 **French** (fr)
- 🇵🇹 **Portuguese** (pt)
- 🇨🇳 **Chinese** (zh)

### How to Change Language:
1. Open the app
2. Tap the "🌐 Language" button on the home screen
3. Select your preferred language
4. The app will remember your choice

All interface elements, buttons, and messages will be translated automatically.

## 📱 App Features

### Camera Screen
- Real-time camera interface
- Capture gym equipment photos
- Flip camera support

### Result Screen
- Equipment recognition with confidence score
- Suggested exercises
- Detailed descriptions

### Exercise Library
- Browse exercises by equipment type
- View sets and reps
- Proper form instructions

### Workout Generator
- AI-powered workout recommendations
- Duration and difficulty selection
- Calorie estimates

## 🤖 AI Model

The model recognizes 5 equipment types:
- Dumbbell
- Barbell
- Bench
- Cable Machine
- Smith Machine

### Training

```bash
cd ml-model
python train_model.py
```

This will:
1. Load and preprocess images
2. Train a MobileNet-based model
3. Export as TensorFlow Lite for mobile

## 🗄️ Database

The app uses SQLite with three main tables:
- `exercises` - Exercise database
- `equipment` - Equipment catalog
- `workout_plans` - Predefined workouts

## 🛠️ Tech Stack

- **Frontend**: React Native 0.75.4, Expo SDK 54 (Mobile + Web)
- **Backend**: FastAPI, SQLite
- **AI**: TensorFlow Lite
- **Camera**: expo-camera (Mobile), expo-image-picker (Web)
- **Navigation**: React Navigation v6
- **Web**: Responsive design, File upload API

## 📦 Dependencies

### Mobile/Web
- expo@~54.0.0
- react-native@0.75.4
- expo-camera (Mobile)
- expo-image-picker (Web)
- @react-navigation/native@^6.1.18
- @react-navigation/native-stack@^6.11.0
- axios
- @tensorflow/tfjs
- react-native-gesture-handler
- expo-media-library

### Backend
- fastapi
- uvicorn
- sqlalchemy
- tensorflow
- pillow

## 🎨 UI/UX

- Dark theme optimized for gym environment
- Smooth animations
- Intuitive navigation
- Accessible design

## 🔄 Development Workflow

1. **Mobile**: Use Expo Go for live reload
2. **Backend**: Automatic reload with uvicorn
3. **Testing**: Update mock data for quick iteration

## 📝 Todo

- [ ] Collect real equipment images for training
- [ ] Implement video demonstrations
- [ ] Add user accounts
- [ ] Track workout history
- [ ] Social sharing features
- [ ] Push notifications
- [ ] Offline mode

## 🤝 Contributing

Feel free to submit issues and pull requests!

## 📄 License

MIT License - feel free to use for your projects!

## 🙏 Acknowledgments

Built with:
- Expo
- FastAPI
- TensorFlow
- React Native

---

**Made with 💪 for fitness enthusiasts**

