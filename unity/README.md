# Eduverse Unity Client

## 🎮 Interactive 3D Learning Platform

Unity client that transforms curriculum PDFs into interactive 3D learning experiences for children aged 6-10.

---

## ✨ Features

- **Automatic World Generation**: Fetches lesson specs from backend and builds 3D worlds
- **Interactive Learning**: Collectibles, NPCs, challenges, and puzzles
- **AI Mentor**: Guided learning with themed mentor characters
- **Gamification**: XP, levels, badges, and progress tracking
- **Real-time Analytics**: Session tracking and performance analytics
- **Multi-Platform**: Android tablets and desktop

---

## 🚀 Quick Start

1. **Open Project** in Unity 2021.3 LTS or newer
2. **Install Packages**:
   - TextMeshPro (auto-prompts)
   - Newtonsoft JSON (`com.unity.nuget.newtonsoft-json`)
3. **Configure Backend** in ConfigurationManager:
   - Backend URL: `http://localhost:8000`
4. **Set Lesson ID** in LessonLoader from your backend
5. **Press Play**!

Full setup guide: [UNITY_SETUP.md](UNITY_SETUP.md)

---

## 📁 Project Structure

```
Assets/
├── Scripts/
│   ├── Core/              # Core game systems
│   ├── Data/              # Data models
│   ├── Interaction/       # Interactive objects
│   ├── UI/                # User interface
│   ├── Managers/          # Game managers
│   └── Utilities/         # Helper scripts
│
├── Scenes/
│   └── MainScene.unity    # Main game scene
│
├── Prefabs/               # Reusable prefabs
│   ├── UI/
│   ├── Environments/
│   ├── Characters/
│   └── Interactables/
│
└── Resources/             # Runtime-loaded assets
```

---

## 🔑 Key Components

### LessonLoader
Fetches lessons from backend and builds the 3D world.

### APIClient
Handles all communication with the FastAPI backend.

### GameCoordinator
Manages gameplay flow, XP, challenges, and session tracking.

### SceneSpecModels
C# data models matching the backend's Python models exactly.

---

## 🎯 Integration with Backend

### Backend Flow

```
1. Teacher uploads PDF → Backend analyzes
2. Backend generates SceneSpec JSON
3. Unity calls GET /api/lessons/{id}
4. Unity parses JSON and builds 3D world
5. Child plays and learns
6. Unity logs events to backend
```

### API Endpoints Used

```csharp
// Fetch lesson
GET /api/lessons/{lesson_id}

// Start session
POST /api/sessions/start

// Log events
POST /api/sessions/event

// End session
POST /api/sessions/end
```

---

## 🎨 Creating Content

### 1. Create Environment Prefabs

```
1. Build your environment (terrain, skybox, objects)
2. Save as prefab: Prefabs/Environments/ocean_reef
3. Add to PrefabLibrary with key: "environments/ocean_reef"
```

### 2. Create Character Prefabs

```
1. Create NPC model
2. Save as prefab: Prefabs/Characters/mentor
3. Add to PrefabLibrary with key: "characters/ocean_mentor"
```

Note: Don't add scripts to prefabs - they're added automatically!

### 3. Theme Mapping

Backend themes → Unity prefabs:
- `ocean` → coral reef, underwater cave, ocean surface
- `space` → space station, asteroid field, moon base
- `jungle` → rainforest, clearing, tree canopy
- `city` → plaza, park, museum
- `lab` → science lab, experiment room
- `fantasy` → magic forest, castle, garden

---

## 🎮 Gameplay Features

### Collectibles
- Float and rotate
- Award XP when collected
- Trigger collection effects
- Log to analytics

### NPCs
- Display dialogue
- Provide hints and guidance
- Award XP for interaction
- Themed personalities

### Challenges
- Multiple choice quizzes
- Drag & drop puzzles (coming soon)
- Voice interactions (coming soon)
- Sequence ordering (coming soon)

### Gamification
- **XP System**: Earn XP for actions
- **Levels**: Level up with XP milestones
- **Progress Bar**: Visual progress tracking
- **XP Popups**: Floating text when earning XP

---

## 📱 Platform Support

### Desktop
- Windows, Mac, Linux
- Keyboard and mouse controls
- Higher quality graphics

### Android
- Tablets (primary target)
- Touch controls
- Optimized performance
- Safe area handling for notches

### iOS (Coming Soon)
- iPad support
- ARKit integration
- Apple Pencil support

---

## 🔧 Configuration

### ConfigurationManager Settings

```csharp
// Backend
backendURL = "http://localhost:8000";        // Development
productionURL = "https://api.eduverse.com";  // Production

// IDs
defaultLearnerId = "test-learner-123";
defaultLessonId = "test-lesson-456";

// Debug
enableDebugLogs = true;
mockAPIResponses = false;
```

### Build Settings

**Android**:
- API Level: 24+ (Android 7.0+)
- Scripting Backend: IL2CPP
- Architectures: ARMv7 + ARM64

**Desktop**:
- Scripting Backend: Mono or IL2CPP
- Target: x64

---

## 🐛 Debugging

### Enable Debug Logs

Set `enableDebugLogs = true` in ConfigurationManager to see detailed logs:

```
[API] GET http://localhost:8000/api/lessons/123
[LessonLoader] Loaded lesson: Ocean Adventure
[GameCoordinator] Session started: session-456
[Collectible] Collected: Ocean Token (+5 XP)
```

### Common Issues

**API connection failed**:
- Check backend is running
- Verify URL in ConfigurationManager
- Test in browser: http://localhost:8000/health

**Prefabs not loading**:
- Check PrefabLibrary has entries
- Verify prefab keys match backend exactly
- Check Console for "Prefab not found" warnings

**UI not showing**:
- Verify Canvas exists
- Check UI references in GameCoordinator
- Ensure EventSystem exists

---

## 📊 Performance Optimization

### Mobile Optimization

- Use object pooling for collectibles
- Limit draw calls (combine meshes)
- Use texture atlases
- Enable GPU Instancing
- Set quality settings to "Medium"

### Network Optimization

- Cache lesson data locally
- Batch analytics events
- Use compression for large responses
- Implement offline mode

---

## 🚀 Build & Deploy

### Development Build

```
File → Build Settings → Build
- Enable Development Build
- Enable Script Debugging
- Connect Profiler
```

### Production Build

```
File → Build Settings → Build
- Disable Development Build
- Set IL2CPP (Android)
- Enable optimization
- Sign with keystore
```

---

## 📈 Analytics Integration

The client automatically tracks:

- **Session Events**: Start, end, duration
- **Interactions**: Collectibles, NPCs, challenges
- **Performance**: Success rate, completion percentage
- **XP**: Earned from all sources
- **Progress**: Scenes completed, objectives achieved

All tracked via `GameCoordinator` and sent to backend.

---

## 🔄 Update Flow

When backend updates:

1. Backend changes SceneSpec structure
2. Update `SceneSpecModels.cs` to match
3. Update UI/interaction scripts if needed
4. Test integration
5. Deploy new client build

---

## 📚 Documentation

- **Setup Guide**: [UNITY_SETUP.md](UNITY_SETUP.md)
- **Backend API**: `../backend/docs/API.md`
- **Main README**: `../README.md`
- **Quick Start**: `../QUICKSTART.md`

---

## 🎯 Roadmap

### Version 1.0 (Current)
- [x] Lesson loading from backend
- [x] Basic world generation
- [x] Collectibles and NPCs
- [x] Challenge system
- [x] Session tracking
- [x] Gamification (XP, levels)

### Version 1.1 (Next)
- [ ] Voice interactions (TTS/STT)
- [ ] Advanced challenges (drag-drop, sequencing)
- [ ] More themes and environments
- [ ] Player controller
- [ ] Sound and music

### Version 2.0 (Future)
- [ ] Multiplayer support
- [ ] AR mode
- [ ] Offline lessons
- [ ] Parental dashboard
- [ ] Achievement system

---

## 🤝 Contributing

See main repository [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## 📄 License

See [LICENSE](../LICENSE)

---

**Ready to build amazing learning experiences! 🎮📚**
