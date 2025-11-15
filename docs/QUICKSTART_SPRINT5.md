# Sprint 5 Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Prerequisites
- Python 3.8+ installed
- Unity 2021.3 LTS or newer
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Step 1: Backend Setup (2 minutes)

```bash
# Navigate to backend directory
cd eduverse/backend

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env and add your API key
# ANTHROPIC_API_KEY=your_actual_key_here

# Start the server
python -m uvicorn main:app --reload
```

**Expected output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Step 2: Test Backend (1 minute)

```bash
# Test multilingual support
curl "http://localhost:8000/api/multilingual/languages"

# Test English mechanic generation
curl -X POST "http://localhost:8000/api/streaming/test-mechanic?language=en&mechanic_type=exciting_chase"

# Test Arabic mechanic generation
curl -X POST "http://localhost:8000/api/streaming/test-mechanic?language=ar&mechanic_type=supportive_helper"
```

**Expected**: JSON responses with mechanic data

### Step 3: Unity Setup (2 minutes)

1. **Open Unity Project**:
   ```bash
   # Open Unity Hub
   # Add project: eduverse/unity/EduverseClient
   # Open with Unity 2021.3 LTS
   ```

2. **Verify Localization Scripts**:
   - Check `Assets/Scripts/Localization/` exists
   - Verify `EduvereLocalization.cs` has no errors

3. **Test Localization** (optional):
   - Create new scene
   - Add TextMeshPro text
   - Attach `LocalizedText` component
   - Set `localizationKey = "mentor.greeting"`
   - Play scene
   - In console, run: `EduvereLocalization.Instance.SetLanguage("ar")`
   - Text should change to Arabic

### Step 4: Test Dynamic Mechanics (Optional)

1. **Add to Scene**:
   - Create empty GameObject
   - Attach `DynamicMechanicHandler` script
   - Set `backendURL = "http://localhost:8000"`

2. **Configure**:
   - `childId = "test_child"`
   - `language = "en"` (or "ar" for Arabic)
   - `childAge = 8`

3. **Play and Monitor**:
   - Check Console for "[DynamicMechanic]" logs
   - Mechanics will be requested every 5 seconds
   - Verify HTTP requests succeed

## 🎯 Common Tasks

### Test a Specific Language

**Backend**:
```bash
curl -X POST "http://localhost:8000/api/streaming/test-mechanic?language=fr&topic=mathematics"
```

**Unity**:
```csharp
EduvereLocalization.Instance.SetLanguage("fr");
```

### Test Different Mechanic Types

```bash
# Exciting chase (for bored children)
curl -X POST "http://localhost:8000/api/streaming/test-mechanic?mechanic_type=exciting_chase"

# Supportive helper (for frustrated children)
curl -X POST "http://localhost:8000/api/streaming/test-mechanic?mechanic_type=supportive_helper"

# Advanced puzzle (for mastery)
curl -X POST "http://localhost:8000/api/streaming/test-mechanic?mechanic_type=advanced_puzzle"

# Exploratory quest (for curious explorers)
curl -X POST "http://localhost:8000/api/streaming/test-mechanic?mechanic_type=exploratory_quest"
```

### Upload Multilingual Curriculum

```bash
curl -X POST "http://localhost:8000/api/multilingual/curriculum/upload" \
  -F "file=@your_document.pdf" \
  -F "force_language=ar"
```

### Check Active Streaming Sessions

```bash
curl "http://localhost:8000/api/streaming/stats"
```

## 🐛 Troubleshooting

### Backend Issues

**Problem**: `ModuleNotFoundError: No module named 'fastapi'`
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Problem**: `pydantic_settings.exceptions.SettingsError`
```bash
# Solution: Check .env file exists and is valid
cat .env
cp .env.example .env  # if missing
```

**Problem**: Backend starts but returns 500 errors
```bash
# Solution: Check API key is set
grep ANTHROPIC_API_KEY .env

# Should show: ANTHROPIC_API_KEY=sk-ant-...
# NOT: ANTHROPIC_API_KEY=placeholder_for_testing
```

### Unity Issues

**Problem**: Compilation errors about DOTween, NativeWebSocket
```
Solution: These are optional dependencies.
The code works without them. Animations are disabled.
```

**Problem**: Arabic text shows as boxes/question marks
```
Solution: Install Arabic-compatible font in TextMeshPro
1. Font Asset Creator in Unity
2. Import Google Noto Sans Arabic
3. Assign to LocalizedText components
```

**Problem**: DynamicMechanicHandler not requesting mechanics
```
Solution: Check backend URL and connectivity
1. Verify backend is running: curl http://localhost:8000/
2. Check Unity console for HTTP errors
3. Ensure firewall allows localhost:8000
```

## 📚 Next Steps

### For Developers
1. Read [SPRINT5_IMPLEMENTATION.md](./SPRINT5_IMPLEMENTATION.md) for full technical details
2. Explore API docs at `http://localhost:8000/docs`
3. Review code comments in key files:
   - `backend/app/services/streaming_engine.py`
   - `unity/.../Localization/EduvereLocalization.cs`

### For Testing
1. Set up different child profiles (different ages, languages)
2. Test behavior triggers (idle, errors, mastery)
3. Verify mechanics spawn correctly
4. Test all 7 supported languages

### For Customization
1. Add new translations to `LocalizedText.cs`
2. Create custom mechanic types in `streaming_engine.py`
3. Add new language support
4. Customize cultural adaptation prompts

## 🎨 Example: Complete Multilingual Workflow

```bash
# 1. Upload Arabic math curriculum
curl -X POST "http://localhost:8000/api/multilingual/curriculum/upload" \
  -F "file=@arabic_math.pdf" \
  -F "force_language=ar"
# Response: {"curriculum_id": "curr_abc123", ...}

# 2. Generate Arabic lesson
curl -X POST "http://localhost:8000/api/multilingual/lessons/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "curriculum_id": "curr_abc123",
    "age_range": "6-8",
    "target_duration_minutes": 20
  }'
# Response: {"lesson_id": "lesson_xyz789", ...}

# 3. In Unity: Set up for Arabic child
EduvereLocalization.Instance.SetLanguage("ar");
dynamicMechanicHandler.childId = "ahmed_001";
dynamicMechanicHandler.language = "ar";

# 4. Test mechanic generation for this child
curl -X POST "http://localhost:8000/api/streaming/test-mechanic?language=ar&age=7&topic=mathematics"
```

## 📊 Performance Expectations

**Backend**:
- Cold start: 2-3 seconds
- Language detection: < 100ms
- Mechanic generation: 2-5 seconds (streaming)
- API response: < 50ms

**Unity**:
- Scene load with localization: < 1 second
- Language switch: < 100ms
- Mechanic spawn: < 50ms

## 🔗 Useful Links

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/
- **Streaming Stats**: http://localhost:8000/api/streaming/stats

## 💡 Pro Tips

1. **Development**: Use `--reload` flag for auto-restart on code changes
   ```bash
   python -m uvicorn main:app --reload
   ```

2. **Testing**: Enable debug logging
   ```bash
   # In .env
   LOG_LEVEL=DEBUG
   ```

3. **Unity**: Enable console logs in DynamicMechanicHandler inspector
   ```csharp
   [SerializeField] private bool enableDebugLogs = true;
   ```

4. **Multilingual**: Test RTL rendering early
   ```csharp
   // Quick test in Unity console
   EduvereLocalization.Instance.SetLanguage("ar");
   EduvereLocalization.Instance.SetLanguage("he");
   ```

## ✅ Verification Checklist

- [ ] Backend starts without errors
- [ ] `/api/multilingual/languages` returns 7 languages
- [ ] `/api/streaming/test-mechanic` generates valid JSON
- [ ] Arabic mechanic has Arabic text (not English)
- [ ] Unity project compiles without errors
- [ ] LocalizedText component works
- [ ] DynamicMechanicHandler requests mechanics
- [ ] Console shows no HTTP errors

## 🎉 Success!

If all checklist items pass, Sprint 5 is working correctly!

You now have:
- ✅ Multilingual curriculum processing
- ✅ Real-time adaptive content generation
- ✅ RTL text support
- ✅ Behavior-based difficulty adjustment
- ✅ Cultural adaptation

Ready for pilot testing with real children! 🚀
