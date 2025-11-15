# Firebase Analytics Setup Guide for Eduverse

## 🔥 Quick Start (15 minutes)

This guide will help you set up Firebase Analytics for Eduverse to track learner engagement, progress, and behavior.

---

## 📋 Prerequisites

- Unity 2021.3 LTS or newer
- Eduverse Unity client (Sprint 4+)
- Google account
- Android device for testing (Firebase doesn't work in Unity Editor)

---

## Step 1: Create Firebase Project

### 1.1 Go to Firebase Console

Navigate to: https://console.firebase.google.com

### 1.2 Create New Project

1. Click "Create a project"
2. **Project name**: `Eduverse` (or your preferred name)
3. Click "Continue"
4. **Enable Google Analytics**: ✓ (recommended)
5. Choose or create Analytics account
6. Click "Create project"
7. Wait for setup to complete (~30 seconds)
8. Click "Continue"

---

## Step 2: Add Android App

### 2.1 Register Android App

1. In Firebase Console, click "Add app"
2. Select **Android** icon
3. Fill in app details:
   - **Android package name**: `com.yourcompany.eduverse`
     - Must match Unity's Package Name (see Unity → File → Build Settings → Player Settings)
   - **App nickname**: `Eduverse Android` (optional)
   - **Debug signing certificate SHA-1**: Leave blank for now
4. Click "Register app"

### 2.2 Download Configuration File

1. Download `google-services.json`
2. **Important**: Place this file in your Unity project's `Assets/` folder
   - Example: `Assets/google-services.json`
3. Click "Next"

### 2.3 Skip SDK Instructions

1. Click "Next" (we'll handle SDK in Unity)
2. Click "Continue to console"

---

## Step 3: Add iOS App (Optional)

### 3.1 Register iOS App

1. In Firebase Console, click "Add app"
2. Select **iOS** icon
3. Fill in app details:
   - **iOS bundle ID**: `com.yourcompany.eduverse`
     - Must match Unity's Bundle Identifier
   - **App nickname**: `Eduverse iOS` (optional)
4. Click "Register app"

### 3.2 Download Configuration File

1. Download `GoogleService-Info.plist`
2. **Important**: Place this file in your Unity project's `Assets/` folder
   - Example: `Assets/GoogleService-Info.plist`
3. Click "Next", then "Continue to console"

---

## Step 4: Install Firebase Unity SDK

### 4.1 Download SDK

1. Go to: https://firebase.google.com/download/unity
2. Download **Firebase Unity SDK** (latest version)
3. Extract the `.zip` file

### 4.2 Import Analytics Package

1. In Unity, go to **Assets → Import Package → Custom Package**
2. Navigate to extracted SDK folder
3. Select `FirebaseAnalytics.unitypackage`
4. Click "Open"
5. In Import dialog, click "Import" (import all files)
6. Wait for import to complete (~1 minute)

### 4.3 Import Additional Packages (Optional)

For full Firebase features, also import:
- `FirebaseAuth.unitypackage` - User authentication
- `FirebaseDatabase.unitypackage` - Realtime Database
- `FirebaseStorage.unitypackage` - Cloud Storage

**Note**: For Sprint 4, only Analytics is required.

---

## Step 5: Configure AnalyticsLogger

### 5.1 Uncomment Firebase Code

Open `Assets/Scripts/UI/AnalyticsLogger.cs` and make these changes:

**Line 6-9 - Uncomment imports**:
```csharp
// Before:
// using Firebase;
// using Firebase.Analytics;
// using Firebase.Extensions;

// After:
using Firebase;
using Firebase.Analytics;
using Firebase.Extensions;
```

**Line 77-93 - Uncomment initialization**:
```csharp
// In InitializeFirebase() method
FirebaseApp.CheckAndFixDependenciesAsync().ContinueWithOnMainThread(task =>
{
    if (task.Result == DependencyStatus.Available)
    {
        firebaseInitialized = true;
        FirebaseAnalytics.SetAnalyticsCollectionEnabled(true);

        if (enableDebugLogs)
            Debug.Log("[AnalyticsLogger] Firebase Analytics initialized successfully");
    }
    else
    {
        Debug.LogError($"[AnalyticsLogger] Firebase initialization failed: {task.Result}");
    }
});
```

**Line 474-520 - Uncomment LogToFirebase**:
```csharp
// In LogToFirebase() method - uncomment the entire FirebaseAnalytics.LogEvent block
Parameter[] firebaseParams = new Parameter[evt.parameters.Count];
// ... (full implementation in file)
FirebaseAnalytics.LogEvent(evt.eventName, firebaseParams);
```

**Line 580-585 - Uncomment SetUserProperty**:
```csharp
// In SetUserProperty() method
FirebaseAnalytics.SetUserProperty(propertyName, value);
```

**Line 595-600 - Uncomment SetUserId**:
```csharp
// In SetUserId() method
FirebaseAnalytics.SetUserId(userId);
```

### 5.2 Configure in Unity Inspector

1. Find or create `AnalyticsLogger` GameObject in scene
2. In Inspector, configure:
   - **Enable Firebase Analytics**: ✓
   - **Enable Backend Analytics**: ✓
   - **Enable Debug Logs**: ✓ (for testing)
   - **Batch Size**: 10
   - **Batch Interval**: 30

---

## Step 6: Android Build Configuration

### 6.1 Player Settings

**File → Build Settings → Player Settings**:

**Other Settings**:
- **Package Name**: `com.yourcompany.eduverse` (must match Firebase)
- **Minimum API Level**: 21 (Android 5.0) or higher
- **Target API Level**: 33 (Android 13) or higher
- **Scripting Backend**: IL2CPP
- **Target Architectures**: ARMv7 ✓, ARM64 ✓

**Publishing Settings**:
- **Custom Main Gradle Template**: ✓ (Firebase will prompt if needed)
- **Custom Gradle Properties Template**: ✓

### 6.2 Verify google-services.json

1. Check that `google-services.json` is in `Assets/`
2. Unity should automatically process it for Android builds
3. If not, check Console for warnings

---

## Step 7: Build and Test

### 7.1 Build APK

1. **File → Build Settings**
2. Select **Android**
3. Click "Build" (or "Build and Run")
4. Wait for build to complete (~5-10 minutes)

### 7.2 Install on Device

1. Connect Android device via USB
2. Enable USB debugging on device
3. Install APK:
   - Via Unity: "Build and Run"
   - Via ADB: `adb install eduverse.apk`
   - Via file transfer: Copy APK and install manually

### 7.3 Enable Debug Mode

To see events in real-time in Firebase Console:

```bash
# Replace with your package name
adb shell setprop debug.firebase.analytics.app com.yourcompany.eduverse

# To disable debug mode later:
adb shell setprop debug.firebase.analytics.app .none.
```

### 7.4 Verify Events

1. Open app on device
2. Play through a lesson (collect items, answer challenges, etc.)
3. Go to Firebase Console: https://console.firebase.google.com
4. Select your project
5. Navigate to **Analytics → DebugView**
6. You should see events appearing in real-time:
   - `session_start`
   - `xp_gained`
   - `collectible_collected`
   - `challenge_completed`
   - etc.

**Note**: If using DebugView, events appear immediately. Otherwise, events appear in Firebase Console after ~24 hours.

---

## Step 8: Monitor Analytics

### 8.1 Real-Time Monitoring (DebugView)

**Firebase Console → Analytics → DebugView**

Shows events as they happen (when debug mode enabled):
- Event name
- Event parameters
- User properties
- Timestamp

Perfect for testing and debugging.

### 8.2 Historical Data (Events Dashboard)

**Firebase Console → Analytics → Events**

Available ~24 hours after first events:
- Event counts
- User engagement
- Event parameters
- Funnels and conversions

### 8.3 User Analytics

**Firebase Console → Analytics → Users**

See:
- Active users (daily, weekly, monthly)
- User retention
- User lifetime value
- Cohort analysis

### 8.4 Custom Dashboards

**Firebase Console → Analytics → Dashboards**

Create custom dashboards for:
- Learning progress metrics
- Engagement rates
- Challenge completion rates
- Badge unlock rates

---

## 🎯 Key Events Tracked

Eduverse automatically tracks these events:

### Session Events
- `app_open` - App launched
- `session_start` - Learning session started
- `session_end` - Learning session ended

### Gameplay Events
- `xp_gained` - XP awarded (with amount and reason)
- `level_up` - Player leveled up
- `badge_unlocked` - Badge unlocked (with badge ID/name)
- `collectible_collected` - Item collected
- `challenge_started` - Challenge begun
- `challenge_completed` - Challenge finished (with success/failure)
- `quiz_answer` - Quiz question answered (with correctness)

### Interaction Events
- `npc_interaction` - Talked to NPC
- `curiosity_changed` - Curiosity bar changed

### Scene Events
- `scene_loaded` - 3D scene loaded
- `scene_completed` - Scene finished

### Loading Events
- `loading_stage_changed` - Loading stage progressed
- `loading_completed` - Loading finished

### Error Events
- `error_occurred` - Error happened (with type and message)

---

## 📊 Example Queries

### Find Most Engaged Learners

```sql
-- In BigQuery (link Firebase to BigQuery in Console)
SELECT
  user_id,
  COUNT(*) as total_events,
  SUM(CASE WHEN event_name = 'challenge_completed' THEN 1 ELSE 0 END) as challenges,
  SUM(CAST(event_params.value.int_value AS INT64)) as total_xp
FROM `your-project.analytics_*.events_*`
WHERE event_name IN ('xp_gained', 'challenge_completed')
  AND event_params.key = 'amount'
GROUP BY user_id
ORDER BY total_xp DESC
LIMIT 100
```

### Challenge Difficulty Analysis

```sql
SELECT
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'challenge_id') as challenge,
  COUNT(*) as attempts,
  SUM(CASE WHEN (SELECT value.bool_value FROM UNNEST(event_params) WHERE key = 'success') THEN 1 ELSE 0 END) as successes,
  ROUND(SUM(CASE WHEN (SELECT value.bool_value FROM UNNEST(event_params) WHERE key = 'success') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate
FROM `your-project.analytics_*.events_*`
WHERE event_name = 'challenge_completed'
GROUP BY challenge
ORDER BY success_rate ASC
```

---

## 🐛 Troubleshooting

### Problem: "Firebase not initialized"

**Symptoms**: Console shows "Firebase SDK not installed" warning

**Solution**:
1. Check `google-services.json` is in `Assets/`
2. Verify Firebase SDK imported correctly
3. Uncomment Firebase code in `AnalyticsLogger.cs`
4. Rebuild project

### Problem: No events in DebugView

**Symptoms**: Playing on device but no events showing

**Solution**:
1. Enable debug mode: `adb shell setprop debug.firebase.analytics.app com.yourcompany.eduverse`
2. Verify package name matches Firebase Console
3. Check device is connected to internet
4. Force close and restart app
5. Check Console for Firebase errors

### Problem: "Dependency resolution failed"

**Symptoms**: Build errors about missing dependencies

**Solution**:
1. Go to **Assets → External Dependency Manager → Android Resolver → Settings**
2. Enable "Auto-resolution"
3. Click **Assets → External Dependency Manager → Android Resolver → Force Resolve**
4. Wait for resolution to complete
5. Rebuild project

### Problem: Build fails with Gradle errors

**Symptoms**: Android build fails with Gradle configuration errors

**Solution**:
1. Update Gradle templates:
   - Enable "Custom Main Gradle Template"
   - Enable "Custom Gradle Properties Template"
2. Check minimum Android API level (21+)
3. Update Android SDK tools in Unity Hub
4. Clear build cache: Delete `Library/Bee` folder
5. Rebuild

### Problem: Events not appearing in Dashboard

**Symptoms**: DebugView works but Dashboard shows no data

**Solution**:
1. Wait 24 hours (data processing delay)
2. Check that analytics collection is enabled in Firebase Console
3. Verify sufficient event volume (need multiple users/sessions)
4. Check time range selector in Dashboard

---

## ✅ Verification Checklist

### Setup Verification
- [ ] Firebase project created
- [ ] Android/iOS app registered in Firebase
- [ ] `google-services.json` in `Assets/` (Android)
- [ ] `GoogleService-Info.plist` in `Assets/` (iOS)
- [ ] Firebase SDK imported to Unity
- [ ] Firebase code uncommented in `AnalyticsLogger.cs`
- [ ] Package name matches between Unity and Firebase

### Build Verification
- [ ] APK builds successfully
- [ ] APK installs on device
- [ ] App launches without crashes
- [ ] Console shows "Firebase Analytics initialized successfully"
- [ ] No Firebase-related errors in logs

### Analytics Verification
- [ ] Debug mode enabled on device
- [ ] DebugView shows events in real-time
- [ ] `session_start` event appears
- [ ] `xp_gained` event appears on XP award
- [ ] `badge_unlocked` event appears on badge unlock
- [ ] User properties set correctly
- [ ] Event parameters contain expected data

### Production Readiness
- [ ] Debug logs disabled (`enableDebugLogs = false`)
- [ ] Debug mode disabled on devices
- [ ] Analytics dashboard configured
- [ ] Custom events defined if needed
- [ ] BigQuery linked (for advanced queries)
- [ ] Team members granted access to Firebase Console

---

## 📚 Additional Resources

### Firebase Documentation
- **Firebase Unity Setup**: https://firebase.google.com/docs/unity/setup
- **Firebase Analytics**: https://firebase.google.com/docs/analytics/get-started?platform=unity
- **Event Logging**: https://firebase.google.com/docs/analytics/events?platform=unity
- **User Properties**: https://firebase.google.com/docs/analytics/user-properties?platform=unity

### Unity Integration
- **External Dependency Manager**: https://github.com/googlesamples/unity-jar-resolver
- **Android Resolver**: Handles Gradle dependencies automatically

### BigQuery Integration
- **Link Firebase to BigQuery**: https://firebase.google.com/docs/analytics/bigquery-export
- **Query Event Data**: https://firebase.google.com/docs/analytics/query-data

---

## 🎓 Best Practices

### Event Naming
- Use lowercase with underscores: `challenge_completed`
- Keep names under 40 characters
- Be consistent across platforms
- Use prefixes for grouping: `edu_xp_gained`, `edu_badge_unlocked`

### Event Parameters
- Limit to 25 parameters per event
- Use descriptive names: `challenge_id` not `id`
- Keep string values under 100 characters
- Use consistent types (don't mix strings and ints)

### User Properties
- Set early in app lifecycle
- Update when values change
- Use for segmentation: `grade_level`, `learning_style`
- Limit to 25 properties per user

### Performance
- Batch events when possible (Eduverse does this automatically)
- Don't log too frequently (>500 events/second)
- Avoid logging in tight loops
- Cache user properties

### Privacy
- Follow COPPA/GDPR guidelines (Eduverse targets children)
- Get parental consent for analytics
- Anonymize personally identifiable information
- Provide opt-out option
- Document data retention policy

---

## 🚀 Next Steps

After Firebase is working:

1. **Set up Crashlytics**:
   - Import `FirebaseCrashlytics.unitypackage`
   - Automatically track crashes and errors
   - Get real-time crash reports

2. **Add Remote Config**:
   - Import `FirebaseRemoteConfig.unitypackage`
   - Change app behavior without redeploying
   - A/B test features

3. **Implement Cloud Messaging**:
   - Import `FirebaseMessaging.unitypackage`
   - Send push notifications
   - Engage inactive users

4. **Link to BigQuery**:
   - Export all analytics data
   - Run advanced SQL queries
   - Create custom reports

5. **Set up Predictions**:
   - Predict user churn
   - Identify high-value users
   - Personalize experience

---

## 📞 Support

**Firebase Issues**:
- Firebase Support: https://firebase.google.com/support
- Stack Overflow: Tag with `firebase` and `unity3d`
- Firebase Community: https://firebase.google.com/community

**Eduverse-Specific Issues**:
- Check `docs/SPRINT4_IMPLEMENTATION.md`
- Review code comments in `AnalyticsLogger.cs`
- Test with `enableDebugLogs = true`

---

**Firebase Setup Complete! 🔥**

You're now tracking comprehensive analytics for learner engagement, progress, and behavior. Use these insights to improve Eduverse and create better learning experiences!
