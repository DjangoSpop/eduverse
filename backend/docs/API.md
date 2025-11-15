# Eduverse API Documentation

## Base URL

**Development**: `http://localhost:8000`
**Production**: `https://api.eduverse.com`

## Authentication

Currently no authentication is required for the MVP. All endpoints are publicly accessible.

**Future**: JWT bearer tokens will be required for production deployment.

## Response Format

All successful responses return JSON with appropriate HTTP status codes:

- `200 OK` - Request successful
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `413 Payload Too Large` - File too large
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

Error responses:

```json
{
  "detail": "Error message here"
}
```

---

## Curriculum Endpoints

### Upload Curriculum

Upload a curriculum PDF for processing.

**Endpoint**: `POST /api/curriculum/upload`

**Request**:
- Content-Type: `multipart/form-data`
- Body:
  - `file`: PDF file (required, max 10MB)
  - `title`: Custom title (optional)

**Response**: `200 OK`

```json
{
  "curriculum_id": "uuid-string",
  "title": "Grade 2 Ocean Science",
  "page_count": 5,
  "word_count": 1234,
  "extracted_text_preview": "First 200 characters of text...",
  "status": "ready_for_generation"
}
```

**Errors**:
- `400`: Invalid file format or corrupted PDF
- `413`: File too large (> 10MB)
- `500`: Processing error

**Example**:

```bash
curl -X POST "http://localhost:8000/api/curriculum/upload" \
  -F "file=@ocean_science.pdf" \
  -F "title=Ocean Science Grade 2"
```

---

### Analyze Curriculum

Analyze curriculum content using Claude AI.

**Endpoint**: `POST /api/curriculum/analyze`

**Request**:

```json
{
  "curriculum_id": "uuid-string",
  "force_reanalysis": false
}
```

**Response**: `200 OK`

```json
{
  "curriculum_id": "uuid-string",
  "status": "completed",
  "analysis": {
    "learning_objectives": [...],
    "key_concepts": [...],
    "recommended_age_range": "6-8",
    "difficulty_estimate": 2,
    "narrative_theme": "ocean",
    "gamification_ideas": [...]
  },
  "message": "Analysis completed successfully"
}
```

**Errors**:
- `404`: Curriculum not found
- `500`: Analysis failed

---

### Get Curriculum

Retrieve curriculum by ID.

**Endpoint**: `GET /api/curriculum/{curriculum_id}`

**Response**: `200 OK`

```json
{
  "id": "uuid-string",
  "title": "Ocean Science",
  "filename": "ocean_science.pdf",
  "full_text": "Complete extracted text...",
  "pages": [...],
  "metadata": {...},
  "ai_analysis": {...},
  "status": "analyzed"
}
```

---

### List Curricula

List all uploaded curricula with pagination.

**Endpoint**: `GET /api/curriculum/`

**Query Parameters**:
- `skip` (default: 0): Number of items to skip
- `limit` (default: 100): Max items to return

**Response**: `200 OK`

```json
[
  {
    "id": "uuid-1",
    "title": "Ocean Science",
    "status": "analyzed",
    ...
  },
  {
    "id": "uuid-2",
    "title": "Space Exploration",
    "status": "uploaded",
    ...
  }
]
```

---

## Lesson Endpoints

### Generate Lesson

Generate an interactive lesson from analyzed curriculum.

**Endpoint**: `POST /api/lessons/generate`

**Request**:

```json
{
  "curriculum_id": "uuid-string",
  "age_range": "6-8",
  "preferred_theme": "ocean",
  "target_duration_minutes": 20,
  "title_override": "Ocean Adventure"
}
```

**Parameters**:
- `curriculum_id` (required): Source curriculum
- `age_range` (optional): Target age range (e.g., "6-8")
- `preferred_theme` (optional): ocean|space|jungle|city|lab|fantasy
- `target_duration_minutes` (optional, default: 20): 5-120
- `title_override` (optional): Custom lesson title

**Response**: `200 OK`

```json
{
  "lesson_id": "lesson-uuid",
  "title": "Ocean Adventure",
  "theme": "ocean",
  "scene_count": 3,
  "estimated_duration_minutes": 20,
  "learning_objectives_count": 4,
  "status": "ready",
  "message": "Lesson generated successfully"
}
```

**Errors**:
- `404`: Curriculum not found
- `400`: Invalid parameters or curriculum not analyzed
- `500`: Generation failed

---

### Get Lesson (Unity Fetch)

Retrieve complete SceneSpec for Unity to build 3D world.

**Endpoint**: `GET /api/lessons/{lesson_id}`

**Response**: `200 OK`

```json
{
  "lesson_id": "uuid",
  "title": "Ocean Adventure",
  "theme": "ocean",
  "age_range": "6-8",
  "estimated_duration_minutes": 20,
  "learning_objectives": [
    {
      "id": "obj-1",
      "text": "Understand ocean ecosystems",
      "bloom_level": "Understand",
      "subject_area": "Science",
      "difficulty": 2
    }
  ],
  "scenes": [
    {
      "id": "scene-1",
      "name": "Coral Reef Discovery",
      "narration": "Welcome to the coral reef!",
      "environment_prefab": "environments/coral_reef",
      "objects": [
        {
          "type": "npc",
          "name": "Captain Coral",
          "prefab_key": "characters/ocean_mentor",
          "position": {"x": 0, "y": 0, "z": 3},
          "interaction": "voice",
          "dialogue": ["Hello!", "Let's explore!"],
          "xp_reward": 10
        }
      ],
      "challenges": [
        {
          "id": "challenge-1",
          "type": "multiple_choice",
          "prompt": "What do dolphins use to find food?",
          "correct_answer": "Echolocation",
          "choices": ["Echolocation", "Eyes", "Smell", "Touch"],
          "hint": "Think about sound waves!",
          "xp_reward": 15,
          "learning_objective_id": "obj-1",
          "difficulty_level": 2
        }
      ],
      "exit_condition": "complete_all_challenges",
      "estimated_duration_minutes": 7
    }
  ],
  "mentor_persona": {
    "name": "Captain Coral",
    "voice": "friendly_adult",
    "personality": "adventurous and curious",
    "avatar_prefab": "characters/ocean_mentor"
  },
  "difficulty_policy": {
    "adaptive_enabled": true,
    "success_threshold": 0.8,
    "failure_threshold": 0.4,
    "adjustment_rate": 0.2
  },
  "created_at": "2024-01-15T10:00:00",
  "curriculum_id": "curriculum-uuid"
}
```

**Unity Integration**:

Unity fetches this endpoint during the loading screen and uses the SceneSpec to:
1. Load environment prefabs
2. Spawn game objects at specified positions
3. Set up challenges and interactions
4. Configure the AI mentor

---

### List Lessons

List all generated lessons with optional filters.

**Endpoint**: `GET /api/lessons/`

**Query Parameters**:
- `skip` (default: 0): Pagination offset
- `limit` (default: 100): Max items
- `theme` (optional): Filter by theme
- `curriculum_id` (optional): Filter by source curriculum

**Response**: `200 OK`

```json
[
  {
    "lesson_id": "lesson-1",
    "title": "Ocean Adventure",
    "theme": "ocean",
    "age_range": "6-8",
    "estimated_duration_minutes": 20,
    "scene_count": 3,
    "learning_objectives_count": 4,
    "created_at": "2024-01-15T10:00:00",
    "curriculum_id": "curriculum-1"
  }
]
```

---

## Session Endpoints

### Start Session

Start a new learning session when a child begins playing.

**Endpoint**: `POST /api/sessions/start`

**Request**:

```json
{
  "learner_id": "learner-uuid",
  "lesson_id": "lesson-uuid",
  "device_info": {
    "platform": "Android",
    "device_model": "Samsung Tab A8"
  }
}
```

**Response**: `200 OK`

```json
{
  "id": "session-uuid",
  "learner_id": "learner-uuid",
  "lesson_id": "lesson-uuid",
  "lesson_title": "Ocean Adventure",
  "started_at": "2024-01-15T10:00:00",
  "status": "in_progress",
  "total_xp_earned": 0,
  ...
}
```

---

### Log Event

Log events during gameplay (challenges, interactions, etc.).

**Endpoint**: `POST /api/sessions/event`

**Request**:

```json
{
  "session_id": "session-uuid",
  "event_type": "challenge_completed",
  "event_data": {
    "challenge_id": "challenge-1",
    "attempts": 2
  },
  "success": true,
  "xp_earned": 15
}
```

**Response**: `200 OK`

```json
{
  "message": "Event logged successfully",
  "event_type": "challenge_completed"
}
```

---

### End Session

End a learning session when the child finishes or quits.

**Endpoint**: `POST /api/sessions/end`

**Request**:

```json
{
  "session_id": "session-uuid",
  "completion_percentage": 1.0,
  "status": "completed"
}
```

**Response**: `200 OK`

```json
{
  "session_id": "session-uuid",
  "learner_id": "learner-uuid",
  "lesson_title": "Ocean Adventure",
  "duration_minutes": 18.5,
  "total_xp_earned": 150,
  "challenges_completed": 12,
  "challenges_attempted": 15,
  "success_rate": 0.80,
  "completion_percentage": 1.0,
  "started_at": "2024-01-15T10:00:00",
  "ended_at": "2024-01-15T10:18:30"
}
```

---

## Learner Endpoints

### Create Learner

Create a new learner profile.

**Endpoint**: `POST /api/learners/`

**Request**:

```json
{
  "name": "Emma",
  "age": 7,
  "grade_level": "Grade 2",
  "parent_email": "parent@example.com"
}
```

**Response**: `200 OK`

```json
{
  "id": "learner-uuid",
  "name": "Emma",
  "age": 7,
  "grade_level": "Grade 2",
  "avatar_key": "avatars/default",
  "performance": {
    "total_lessons_completed": 0,
    "total_xp_earned": 0,
    "current_level": 1,
    ...
  },
  "streak": {
    "current_streak_days": 0,
    "longest_streak_days": 0
  },
  "created_at": "2024-01-15T10:00:00",
  "last_active": "2024-01-15T10:00:00"
}
```

---

### Get Learner

Retrieve learner profile.

**Endpoint**: `GET /api/learners/{learner_id}`

**Response**: `200 OK`

Complete learner profile with all progress data.

---

## Rate Limits

**MVP**: No rate limits

**Production**:
- 100 requests/minute per IP
- 1000 requests/hour per API key

---

## Webhooks (Future)

Coming in v2.0:
- `session.completed` - Notify when session ends
- `learner.level_up` - Notify on level up
- `badge.earned` - Notify on badge earned

---

## SDK Support (Future)

- Python SDK
- Unity C# SDK
- JavaScript SDK

---

For more information, visit the [interactive API documentation](http://localhost:8000/docs).
