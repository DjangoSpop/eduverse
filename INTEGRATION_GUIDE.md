# Eduverse - Complete Integration Guide

## 🎯 First Successful Run - Step by Step

This guide walks you through the complete process of running Eduverse for the first time, from starting the backend to playing an interactive lesson in Unity.

---

## ⚡ Quick Run (5 Minutes)

### Terminal 1: Start Backend

```bash
cd eduverse/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
python main.py
```

### Terminal 2: Generate a Lesson

```bash
# Upload sample curriculum (create a simple PDF first)
curl -X POST "http://localhost:8000/api/curriculum/upload" \
  -F "file=@sample_curriculum.pdf" \
  -F "title=Ocean Science"

# Save the curriculum_id from response

# Analyze it
curl -X POST "http://localhost:8000/api/curriculum/analyze" \
  -H "Content-Type: application/json" \
  -d '{"curriculum_id": "YOUR_CURRICULUM_ID"}'

# Generate lesson
curl -X POST "http://localhost:8000/api/lessons/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "curriculum_id": "YOUR_CURRICULUM_ID",
    "target_duration_minutes": 20,
    "preferred_theme": "ocean"
  }'

# Save the lesson_id from response
```

### Unity: Open and Play

1. Open Unity Hub
2. Add project: `eduverse/unity/EduverseClient`
3. Open with Unity 2021.3 LTS
4. Install packages when prompted (TextMeshPro, Newtonsoft JSON)
5. Open `MainScene`
6. Find `LessonLoader` in hierarchy
7. Paste your `lesson_id` in Inspector
8. **Press Play!** 🎮

---

## 📋 Detailed Step-by-Step Guide

### Phase 1: Backend Setup (10 minutes)

#### Step 1.1: Install Backend Dependencies

```bash
cd eduverse/backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 1.2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

Add your Anthropic API key:
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Get your key at: https://console.anthropic.com/

#### Step 1.3: Start Backend Server

```bash
python main.py
```

You should see:
```
╔══════════════════════════════════════════════════════════════╗
║                  EDUVERSE API SERVER                         ║
║      AI-Powered Interactive Learning Platform                ║
╚══════════════════════════════════════════════════════════════╝

Server URL: http://localhost:8000
API Documentation: http://localhost:8000/docs
```

✅ **Test**: Open http://localhost:8000/health in browser - should show `{"status":"healthy"}`

---

### Phase 2: Generate Your First Lesson (5 minutes)

#### Step 2.1: Create Sample Curriculum PDF

Create a simple text file and save as PDF, or use any educational PDF you have. Example content:

```
Ocean Life and Marine Biology

The ocean is home to many amazing creatures. Dolphins are intelligent
mammals that use echolocation to find food. They communicate with
each other using clicks and whistles.

Coral reefs are beautiful underwater ecosystems. They provide homes
for thousands of species of fish and other marine animals.
```

#### Step 2.2: Upload via API Docs (Easy Method)

1. Open http://localhost:8000/docs
2. Find `POST /api/curriculum/upload`
3. Click "Try it out"
4. Upload your PDF file
5. Click "Execute"
6. **Copy the `curriculum_id`** from response

#### Step 2.3: Analyze Curriculum

Still in API docs:
1. Find `POST /api/curriculum/analyze`
2. Click "Try it out"
3. Paste your `curriculum_id`
4. Click "Execute"
5. Wait ~10 seconds for AI analysis
6. Review the extracted learning objectives!

#### Step 2.4: Generate Interactive Lesson

1. Find `POST /api/lessons/generate`
2. Click "Try it out"
3. Enter:
   ```json
   {
     "curriculum_id": "YOUR_CURRICULUM_ID",
     "target_duration_minutes": 20,
     "preferred_theme": "ocean"
   }
   ```
4. Click "Execute"
5. **Copy the `lesson_id`** - You'll need this for Unity!

Example response:
```json
{
  "lesson_id": "lesson-abc123",
  "title": "Ocean Life and Marine Biology",
  "theme": "ocean",
  "scene_count": 3,
  "estimated_duration_minutes": 20,
  "status": "ready"
}
```

#### Step 2.5: Preview the Lesson (Optional)

Click `GET /api/lessons/{lesson_id}` and paste your lesson ID to see the complete SceneSpec that Unity will use!

---

### Phase 3: Unity Setup (15 minutes)

#### Step 3.1: Open Unity Project

1. Open Unity Hub
2. Click "Add" → "Add project from disk"
3. Navigate to `eduverse/unity/EduverseClient`
4. Select Unity 2021.3 LTS or newer
5. Click "Open"

Wait for Unity to import (first time: 5-10 minutes)

#### Step 3.2: Install Required Packages

**When prompted**, click "Import TMP Essentials"

Then install Newtonsoft JSON:
1. **Window → Package Manager**
2. Click **+** → "Add package by name"
3. Enter: `com.unity.nuget.newtonsoft-json`
4. Click "Add"

#### Step 3.3: Create Main Scene

Unity doesn't save scenes by default, so let's create one:

1. **File → New Scene**
2. **File → Save As**
3. Save as `MainScene` in `Assets/Scenes/`

#### Step 3.4: Add Core GameObjects

In the Hierarchy, create these GameObjects:

**1. APIClient**
- Right-click → Create Empty
- Name: `APIClient`
- Add Component → Search "APIClient" → Add Script
- Leave default settings

**2. ConfigurationManager**
- Create Empty
- Name: `ConfigurationManager`
- Add Component → "ConfigurationManager"
- In Inspector, verify:
  - Backend URL: `http://localhost:8000`
  - Use Local Backend: ✓
  - Default Learner ID: `test-learner-123`

**3. GameCoordinator**
- Create Empty
- Name: `GameCoordinator`
- Add Component → "GameCoordinator"

**4. LessonLoader**
- Create Empty
- Name: `LessonLoader`
- Add Component → "LessonLoader"
- **Important:** Set these fields in Inspector:
  - **Lesson ID**: Paste your lesson ID from backend!
  - **Learner ID**: `test-learner-123`
  - **World Root**: Create new Empty GameObject called "World" and drag it here

**5. World Container**
- Create Empty
- Name: `World`
- This will hold all spawned objects

#### Step 3.5: Create Basic UI

1. Right-click Hierarchy → **UI → Canvas**

2. On Canvas, set:
   - Render Mode: Screen Space - Overlay
   - Canvas Scaler → UI Scale Mode: Scale With Screen Size
   - Reference Resolution: 1920 x 1080

3. Right-click Canvas → **UI → Panel** (4 times for 4 panels):

**Panel 1: Loading Screen**
- Name: `LoadingPanel`
- Add Component → "LoadingScreen"
- Add child Text (TextMeshPro): "Loading..."
- Add child Slider for progress bar

**Panel 2: Gamification UI**
- Name: `GamificationPanel`
- Add Component → "GamificationUI"
- Add child Text: "XP: 0 / 100"
- Add child Text: "Level 1"
- Add child Slider for XP bar

**Panel 3: Challenge UI**
- Name: `ChallengePanel`
- Add Component → "ChallengeUI"
- Add child Text: "Challenge Prompt"
- Add 4 child Buttons for multiple choice
- Start with it Disabled

**Panel 4: Dialogue UI**
- Name: `DialoguePanel`
- Add Component → "DialogueUI"
- Add child Text: "Speaker"
- Add child Text: "Dialogue"
- Start with it Disabled

#### Step 3.6: Link References

1. Select `LessonLoader` in Hierarchy
2. In Inspector:
   - Loading Screen: Drag `LoadingPanel`
   - World Root: Drag `World`

3. Select `GameCoordinator`
4. In Inspector:
   - Gamification UI: Drag `GamificationPanel`
   - Challenge UI: Drag `ChallengePanel`

#### Step 3.7: Create Prefab Library

1. **Right-click in Project** → Create → Eduverse → Prefab Library
2. Name it `PrefabLibrary`
3. For now, leave it empty (we'll create placeholder objects)

4. Select `LessonLoader`
5. Drag `PrefabLibrary` to the Prefab Library field

---

### Phase 4: First Run! (The Moment of Truth)

#### Step 4.1: Double-Check Settings

- [ ] Backend is running at http://localhost:8000
- [ ] You have a valid `lesson_id`
- [ ] LessonLoader has the lesson_id set
- [ ] ConfigurationManager has correct backend URL
- [ ] UI panels exist and are referenced
- [ ] PrefabLibrary exists (even if empty)

#### Step 4.2: Press Play!

Click the **Play** button in Unity Editor

#### Step 4.3: What Should Happen

**Loading Sequence (5-10 seconds):**

1. Loading screen appears
2. Console shows:
   ```
   [API] GET http://localhost:8000/api/lessons/YOUR_LESSON_ID
   [LessonLoader] Loaded lesson: Ocean Life
   [API] POST http://localhost:8000/api/sessions/start
   [LessonLoader] Session started: session-xyz
   [LessonLoader] Building scene: Scene 1
   [GameCoordinator] Lesson loaded: Ocean Life
   ```

3. Loading screen disappears
4. World appears (placeholder cubes/spheres for now)
5. Objects spawn at positions from backend
6. Console shows objects being created

**What You'll See:**
- Placeholder environment (plane)
- Floating spheres (collectibles)
- Colored capsules (NPCs)
- Basic scene layout from backend data

#### Step 4.4: Basic Interaction

Since we don't have a player controller yet, you won't be able to move around, but you should see:

- ✅ Loading screen working
- ✅ Backend connection successful
- ✅ Lesson data fetched
- ✅ Session started
- ✅ Objects spawned
- ✅ XP UI visible
- ✅ Console logs showing activity

---

### Phase 5: Verify Integration (2 minutes)

#### Check Backend Logs

In your backend terminal, you should see:

```
[API] GET /api/lessons/lesson-abc123
[API] Response: {...}
[API] POST /api/sessions/start
[API] Event logged: lesson_started
```

#### Check Unity Console

Should show (no errors!):

```
[Configuration] Initialized
[API] GET http://localhost:8000/api/lessons/lesson-abc123
[LessonLoader] Loaded lesson: Ocean Life
[LessonLoader] Scene built with 5 objects and 2 challenges
[GameCoordinator] Lesson loaded
```

#### Verify Session in Backend

Go to http://localhost:8000/docs and call `GET /api/sessions/learner/test-learner-123` to see your active session!

---

## 🎉 Success Indicators

You've successfully integrated Eduverse if you see:

- ✅ Backend running on port 8000
- ✅ Lesson generated with AI analysis
- ✅ Unity connects to backend
- ✅ Loading screen shows progress
- ✅ Objects spawn in scene
- ✅ Session tracked in backend
- ✅ No errors in console
- ✅ UI displays correctly

---

## 🐛 Troubleshooting

### Issue: "Connection failed"

**Symptoms**: Unity shows "Failed to load lesson: Connection refused"

**Solutions**:
1. Check backend is running: http://localhost:8000/health
2. Try `http://127.0.0.1:8000` instead of `localhost`
3. Check firewall settings
4. Verify port 8000 is not blocked

### Issue: "Lesson not found"

**Symptoms**: "Failed to load lesson: Lesson not found"

**Solutions**:
1. Double-check lesson_id in LessonLoader matches backend
2. Generate a new lesson via backend API
3. Call `GET /api/lessons` to list available lessons
4. Copy exact lesson_id (case-sensitive!)

### Issue: "Missing assembly reference"

**Symptoms**: "The type or namespace 'Newtonsoft' could not be found"

**Solutions**:
1. Window → Package Manager
2. Install Newtonsoft JSON: `com.unity.nuget.newtonsoft-json`
3. Restart Unity
4. Reimport scripts

### Issue: "NullReferenceException"

**Symptoms**: Errors about null references in console

**Solutions**:
1. Check all references are assigned in Inspector
2. Ensure UI panels exist
3. Verify PrefabLibrary exists
4. Check World Root is assigned

### Issue: "Nothing spawns"

**Symptoms**: Loading works but no objects appear

**Solutions**:
1. Check Console for "Prefab not found" warnings
2. These are expected - we're using placeholders
3. Verify World Root exists
4. Check scene camera can see World (position 0,0,0)

---

## 📈 Next Steps

### Immediate Improvements

1. **Add Player Controller**
   ```csharp
   // Add CharacterController to a capsule
   // Tag it as "Player"
   // Add basic movement script
   ```

2. **Create Real Prefabs**
   - Design ocean environment
   - Model NPC characters
   - Create collectible models
   - Add to PrefabLibrary

3. **Add Camera**
   - First-person or third-person
   - Or Cinemachine for smooth camera

4. **Polish UI**
   - Better loading screen design
   - Animated XP popups
   - Styled challenge panels

### Enhancements

1. **Sound & Music**
   - Background music for themes
   - Sound effects for collections
   - Voice for dialogue

2. **Visual Effects**
   - Particle effects for collections
   - Shader effects
   - Animated UI elements

3. **More Interactions**
   - Drag & drop challenges
   - Voice input (future)
   - Mini-games

---

## 🎯 Testing Different Lessons

Want to try different themes?

### Generate Space Theme

```bash
curl -X POST "http://localhost:8000/api/lessons/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "curriculum_id": "YOUR_CURRICULUM_ID",
    "preferred_theme": "space",
    "target_duration_minutes": 15
  }'
```

### Generate Jungle Theme

```bash
curl -X POST "http://localhost:8000/api/lessons/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "curriculum_id": "YOUR_CURRICULUM_ID",
    "preferred_theme": "jungle",
    "target_duration_minutes": 25
  }'
```

Then just update the `lesson_id` in Unity and press Play again!

---

## 📊 View Analytics

After playing, check the analytics:

1. Go to http://localhost:8000/docs
2. Call `GET /api/sessions/learner/{learner_id}`
3. See all your play sessions!
4. View XP earned, completion percentage, success rate

---

## 🚀 Deploy to Production

Ready to go live?

### Backend Deployment

```bash
# Deploy to cloud (Render, Railway, Fly.io, etc.)
# Add production DATABASE_URL
# Set ENVIRONMENT=production
# Configure ALLOWED_ORIGINS for Unity app
```

### Unity Build

```bash
# Android APK
File → Build Settings → Android → Build

# Desktop Executable
File → Build Settings → PC, Mac & Linux Standalone → Build
```

---

## 🎓 Conclusion

**Congratulations! 🎉**

You've successfully:
- ✅ Set up the complete Eduverse platform
- ✅ Generated an AI-powered lesson
- ✅ Integrated Unity with the backend
- ✅ Tracked learning sessions
- ✅ Built your first interactive 3D lesson!

The system is now ready for:
- Creating more lessons from any curriculum PDF
- Adding visual content (environments, characters)
- Deploying to devices
- Testing with real learners

**You now have a working AI-powered educational platform!** 🚀📚

---

For questions or issues, check:
- Backend API Docs: http://localhost:8000/docs
- Unity Setup: `unity/UNITY_SETUP.md`
- Project README: `README.md`
