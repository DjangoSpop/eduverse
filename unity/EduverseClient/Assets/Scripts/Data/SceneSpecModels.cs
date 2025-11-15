using System;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Data models for Scene Specification from backend.
/// These models match the Python Pydantic models exactly.
/// </summary>

namespace Eduverse.Data
{
    [Serializable]
    public class Position
    {
        public float x;
        public float y;
        public float z;

        public Vector3 ToVector3()
        {
            return new Vector3(x, y, z);
        }
    }

    [Serializable]
    public class GameObjectData
    {
        public string type;           // npc, collectible, obstacle, portal
        public string name;
        public string prefab_key;
        public Position position;
        public string interaction;    // collect, voice, etc.
        public List<string> dialogue;
        public Dictionary<string, object> metadata;
        public int xp_reward;
    }

    [Serializable]
    public class Challenge
    {
        public string id;
        public string type;           // multiple_choice, drag_drop, etc.
        public string prompt;
        public string correct_answer; // Can be string or number
        public List<string> choices;
        public string hint;
        public int xp_reward;
        public string learning_objective_id;
        public int difficulty_level;
    }

    [Serializable]
    public class SceneData
    {
        public string id;
        public string name;
        public string narration;
        public string environment_prefab;
        public List<GameObjectData> objects;
        public List<Challenge> challenges;
        public string exit_condition;
        public int estimated_duration_minutes;
    }

    [Serializable]
    public class LearningObjective
    {
        public string id;
        public string text;
        public string bloom_level;    // Remember, Understand, Apply, etc.
        public string subject_area;
        public int difficulty;
    }

    [Serializable]
    public class MentorPersona
    {
        public string name;
        public string voice;
        public string personality;
        public string avatar_prefab;
    }

    [Serializable]
    public class DifficultyPolicy
    {
        public bool adaptive_enabled;
        public float success_threshold;
        public float failure_threshold;
        public float adjustment_rate;
    }

    [Serializable]
    public class SceneSpecification
    {
        public string lesson_id;
        public string title;
        public string theme;          // ocean, space, jungle, etc.
        public string age_range;
        public int estimated_duration_minutes;
        public List<LearningObjective> learning_objectives;
        public List<SceneData> scenes;
        public MentorPersona mentor_persona;
        public DifficultyPolicy difficulty_policy;
        public string created_at;
        public string curriculum_id;
    }

    // Session tracking models
    [Serializable]
    public class SessionStartRequest
    {
        public string learner_id;
        public string lesson_id;
        public Dictionary<string, string> device_info;
    }

    [Serializable]
    public class SessionStartResponse
    {
        public string id;
        public string learner_id;
        public string lesson_id;
        public string lesson_title;
        public string started_at;
        public string status;
    }

    [Serializable]
    public class SessionEventRequest
    {
        public string session_id;
        public string event_type;
        public Dictionary<string, object> event_data;
        public bool success;
        public int xp_earned;
    }

    [Serializable]
    public class SessionEndRequest
    {
        public string session_id;
        public float completion_percentage;
        public string status; // completed, abandoned
    }

    // Learner profile models
    [Serializable]
    public class LearnerProfile
    {
        public string id;
        public string name;
        public int age;
        public string grade_level;
        public string avatar_key;
        public PerformanceMetrics performance;
        public StreakData streak;
    }

    [Serializable]
    public class PerformanceMetrics
    {
        public int total_lessons_completed;
        public int total_xp_earned;
        public int current_level;
        public int xp_to_next_level;
        public float success_rate;
    }

    [Serializable]
    public class StreakData
    {
        public int current_streak_days;
        public int longest_streak_days;
    }
}
