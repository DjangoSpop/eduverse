# Eduverse Unity Client - Setup Guide

## 🎮 Unity Client Overview

The Unity client for Eduverse fetches lesson specifications from the backend API and builds interactive 3D learning worlds. This guide will help you set up and configure the Unity project.

---

## 📋 Prerequisites

- **Unity 2021.3 LTS** or newer
- **Visual Studio 2019+** or VS Code with C# extension
- **Newtonsoft JSON for Unity** (install via Package Manager)
- **TextMeshPro** (included with Unity)
- **DOTween** (optional, for animations)

---

## 🚀 Quick Start

### Step 1: Open the Project

1. Open Unity Hub
2. Click "Add" → "Add project from disk"
3. Navigate to `eduverse/unity/EduverseClient`
4. Open with Unity 2021.3 LTS or newer

### Step 2: Install Required Packages

Open **Window → Package Manager** and install:

1. **TextMeshPro** (should prompt automatically)
   - Click "Import TMP Essentials"

2. **Newtonsoft JSON**
   - Add via Git URL: `com.unity.nuget.newtonsoft-json`
   - Or search for "Newtonsoft Json" in Package Manager

3. **DOTween** (Optional but recommended)
   - Asset Store: https://assetstore.unity.com/packages/tools/animation/dotween-hotween-v2-27676
   - Or via Package Manager if available

### Step 3: Configure Backend Connection

1. Find the `ConfigurationManager` prefab or create a GameObject with the `ConfigurationManager` script
2. In the Inspector, set:
   - **Backend URL**: `http://localhost:8000` (your FastAPI backend)
   - **Default Learner ID**: `test-learner-123`
   - **Default Lesson ID**: Your generated lesson ID from backend

### Step 4: Create Main Scene

1. Create a new scene: **File → New Scene**
2. Save as `MainScene` in `Assets/Scenes/`

3. Add these GameObjects:
   - **APIClient** (Add `APIClient.cs` script)
   - **ConfigurationManager** (Add `ConfigurationManager.cs` script)
   - **GameCoordinator** (Add `GameCoordinator.cs` script)
   - **LessonLoader** (Add `LessonLoader.cs` script)

4. Create UI Canvas:
   - **Canvas** (UI → Canvas)
     - Add `LoadingScreen.cs` to a child panel
     - Add `GamificationUI.cs` to a child panel
     - Add `ChallengeUI.cs` to a child panel
     - Add `DialogueUI.cs` to a child panel

### Step 5: Create Prefab Library

1. **Right-click in Project** → Create → Eduverse → Prefab Library
2. Name it `PrefabLibrary`
3. Assign prefabs for:
   - **Environments**: ocean, space, jungle, etc.
   - **Characters**: NPCs, mentors
   - **Collectibles**: coins, tokens, etc.
   - **Interactables**: portals, buttons, etc.

---

## 📁 Project Structure

```
Assets/
├── Scenes/
│   └── MainScene.unity
│
├── Scripts/
│   ├── Core/
│   │   ├── APIClient.cs           # Backend communication ⭐
│   │   └── LessonLoader.cs        # Lesson loading & world building ⭐
│   │
│   ├── Data/
│   │   ├── SceneSpecModels.cs     # Data models matching backend ⭐
│   │   └── PrefabLibrary.cs       # Prefab management
│   │
│   ├── Interaction/
│   │   ├── CollectibleObject.cs   # Collectible items
│   │   ├── NPCMentor.cs           # NPC characters
│   │   └── InteractableObject.cs  # Portals, buttons, etc.
│   │
│   ├── UI/
│   │   ├── LoadingScreen.cs       # Loading screen with progress
│   │   ├── GamificationUI.cs      # XP, level, progress bar
│   │   ├── ChallengeUI.cs         # Quiz/challenge display
│   │   └── DialogueUI.cs          # NPC dialogue
│   │
│   ├── Managers/
│   │   ├── GameCoordinator.cs     # Main game flow manager ⭐
│   │   └── ConfigurationManager.cs # Settings & configuration
│   │
│   └── Utilities/
│       └── SafeAreaHandler.cs     # Mobile safe area handling
│
├── Prefabs/
│   ├── UI/
│   ├── Environments/
│   ├── Characters/
│   └── Interactables/
│
└── Resources/
```

---

## 🔧 Component Setup

### 1. LessonLoader Setup

The `LessonLoader` is the core component that fetches and builds lessons.

**Inspector Settings:**
- **Lesson ID**: Enter your lesson ID from backend
- **Learner ID**: Enter your learner ID
- **World Root**: Empty transform to hold spawned objects
- **Loading Screen**: Reference to LoadingScreen component
- **Prefab Library**: Reference to PrefabLibrary asset

**How it works:**
1. Calls `APIClient.GetLesson(lessonId)`
2. Receives `SceneSpecification` JSON
3. Starts a session via `APIClient.StartSession()`
4. Builds the 3D world from scene data
5. Spawns objects at specified positions
6. Sets up challenges

### 2. APIClient Setup

No configuration needed! It's a singleton that auto-initializes.

**Key Methods:**
```csharp
// Fetch lesson
yield return APIClient.Instance.GetLesson(lessonId, onSuccess, onError);

// Start session
yield return APIClient.Instance.StartSession(learnerId, lessonId, onSuccess, onError);

// Log event
yield return APIClient.Instance.LogEvent(sessionId, eventType, data, success, xp, onSuccess, onError);

// End session
yield return APIClient.Instance.EndSession(sessionId, completion, status, onSuccess, onError);
```

### 3. GameCoordinator Setup

Coordinates all gameplay systems.

**Inspector Settings:**
- **Gamification UI**: Reference to GamificationUI
- **Challenge UI**: Reference to ChallengeUI

**Responsibilities:**
- Manages gameplay flow
- Tracks collectibles and challenges
- Awards XP
- Logs events to backend
- Handles scene transitions

### 4. UI Components

#### LoadingScreen
- Shows progress during lesson loading
- Displays loading stages
- Handles errors

#### GamificationUI
- Shows XP and level
- Displays XP progress bar
- Shows XP popups when earned
- Handles level-up effects

#### ChallengeUI
- Displays quiz questions
- Handles multiple choice answers
- Shows hints
- Displays feedback (correct/incorrect)

#### DialogueUI
- Shows NPC dialogue
- Typing text effect
- Auto-hides after duration

---

## 🎨 Creating Prefabs

### Environment Prefabs

1. Create an environment (terrain, skybox, lighting)
2. Save as prefab: `Environments/coral_reef`
3. Add to PrefabLibrary with key: `environments/coral_reef`

### Character Prefabs

1. Create NPC model (capsule or custom model)
2. Add animator if needed
3. Save as prefab: `Characters/ocean_mentor`
4. Add to PrefabLibrary with key: `characters/ocean_mentor`

**Note:** Don't add `NPCMentor.cs` to the prefab - it's added automatically by LessonLoader!

### Collectible Prefabs

1. Create collectible object (sphere with material)
2. Add simple animation or rotation
3. Save as prefab: `Collectibles/ocean_token`
4. Add to PrefabLibrary with key: `collectibles/ocean_token`

**Note:** `CollectibleObject.cs` is added automatically!

---

## 🔌 Backend Integration

### Connecting to Backend

The Unity client communicates with the FastAPI backend via REST API.

**Development** (local backend):
```csharp
// Set in ConfigurationManager
backendURL = "http://localhost:8000";
```

**Production**:
```csharp
backendURL = "https://api.eduverse.com";
```

### Testing the Integration

1. **Start the backend**:
   ```bash
   cd backend
   python main.py
   ```

2. **Generate a lesson** (via backend API docs at http://localhost:8000/docs):
   - Upload curriculum PDF
   - Analyze it
   - Generate lesson
   - Copy the `lesson_id`

3. **Configure Unity**:
   - Set the `lesson_id` in LessonLoader
   - Set a `learner_id` in ConfigurationManager

4. **Press Play** in Unity Editor!

### Expected Flow

1. **Loading screen appears**
2. **Progress updates**: "Connecting to server..." → "Starting session..." → "Building world..."
3. **Scene builds**: Environment loads, objects spawn
4. **Gameplay starts**: Can interact with objects, collect items
5. **Challenges appear**: Answer questions, earn XP
6. **Session tracked**: All events logged to backend

---

## 🎮 Player Controller

The current implementation uses simple collision-based interaction. You'll need to add a player controller:

### Option 1: First-Person Controller

```csharp
// Use Unity's CharacterController
// Tag the player GameObject with "Player"
```

### Option 2: Third-Person Controller

```csharp
// Use Cinemachine for camera
// Add movement controls
// Tag character with "Player"
```

### Option 3: Point-and-Click

```csharp
// Click on objects to interact
// Move player via NavMesh
```

**Important**: Tag your player GameObject as "Player" for interactions to work!

---

## 📱 Building for Android

### 1. Switch Platform

- **File → Build Settings**
- Select **Android**
- Click **Switch Platform** (takes 5-10 minutes)

### 2. Player Settings

**File → Build Settings → Player Settings:**

- **Company Name**: Your company
- **Product Name**: Eduverse
- **Package Name**: com.yourcompany.eduverse
- **Version**: 1.0.0

**Other Settings:**
- **Scripting Backend**: IL2CPP
- **API Compatibility**: .NET Standard 2.1
- **Target Architectures**: ARMv7 + ARM64

**Quality Settings:**
- Set default quality to "Medium" for mobile

### 3. Build APK

- **File → Build Settings → Build**
- Choose output location
- Wait for build (10-20 minutes first time)
- Install APK on device via USB

---

## 🐛 Troubleshooting

### Common Issues

#### "Newtonsoft.Json not found"
**Solution**: Install via Package Manager
```
Window → Package Manager → Add package by name:
com.unity.nuget.newtonsoft-json
```

#### "API connection failed"
**Solution**:
1. Check backend is running (`python main.py`)
2. Verify backend URL in ConfigurationManager
3. Check firewall settings
4. Try `http://127.0.0.1:8000` instead of `localhost`

#### "Prefab not found" warnings
**Solution**:
- Create prefabs for each environment/object
- Add them to PrefabLibrary
- Ensure prefab keys match backend response exactly

#### Objects not spawning
**Solution**:
- Check World Root is assigned in LessonLoader
- Verify PrefabLibrary is assigned
- Check Console for errors
- Make sure prefab keys match exactly

#### UI not showing
**Solution**:
- Check Canvas is set to Screen Space - Overlay
- Verify UI references in GameCoordinator
- Check EventSystem exists in scene

---

## 🎯 Testing Checklist

Before building for production:

- [ ] Backend connection works
- [ ] Lesson loads successfully
- [ ] Loading screen shows progress
- [ ] Environment spawns correctly
- [ ] Objects spawn at correct positions
- [ ] Can collect collectibles
- [ ] Can interact with NPCs
- [ ] Dialogue displays correctly
- [ ] Challenges display and work
- [ ] XP is awarded correctly
- [ ] Level up works
- [ ] Session starts successfully
- [ ] Events are logged to backend
- [ ] Session ends properly
- [ ] Works on target device (Android/desktop)

---

## 📚 Next Steps

### Phase 1: Get it Working ✅
- [x] Set up Unity project
- [x] Connect to backend
- [x] Load and display first lesson
- [x] Test on device

### Phase 2: Polish
- [ ] Add player controller
- [ ] Create theme-specific prefabs (ocean, space, jungle)
- [ ] Add sound effects and music
- [ ] Improve visual effects
- [ ] Add particle effects for collections
- [ ] Improve UI/UX

### Phase 3: Advanced Features
- [ ] Voice interaction (TTS/STT)
- [ ] Multiplayer support
- [ ] Offline mode
- [ ] Advanced analytics
- [ ] Parental dashboard

---

## 📞 Support

For help:
- Check backend API documentation: `backend/docs/API.md`
- Review Unity console for errors
- Test backend endpoints at: http://localhost:8000/docs
- Check network connectivity

---

**Unity Client Ready! Start the backend and press Play! 🎮**
