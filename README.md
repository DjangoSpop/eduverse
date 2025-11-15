# Eduverse - AI-Powered Interactive Learning Platform

Transform static curriculum PDFs into interactive 3D learning experiences for children aged 6-10.

## 🎯 Overview

Eduverse is an innovative educational platform that uses AI to automatically convert curriculum documents into engaging, game-like lessons. Teachers upload a PDF, and within minutes, children can play through an interactive 3D world that teaches the same concepts.

### Key Features

- **PDF to 3D**: Upload curriculum PDFs and generate interactive 3D lessons automatically
- **AI-Powered Analysis**: Uses Claude AI to extract learning objectives and create engaging content
- **Gamification**: XP, badges, streaks, and challenges to keep learners motivated
- **Adaptive Difficulty**: Automatically adjusts to each child's skill level
- **Analytics**: Track learning progress and provide insights for teachers and parents
- **Multi-Platform**: Runs on Android tablets and desktop

## 🏗️ Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Teacher   │────────▶│   Backend    │◀────────│    Unity    │
│  (Upload)   │         │   (FastAPI)  │         │   Client    │
└─────────────┘         └──────────────┘         └─────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  Claude AI   │
                        │  (Analysis)  │
                        └──────────────┘
```

### Tech Stack

- **Backend**: Python 3.10+, FastAPI, Anthropic Claude API
- **Frontend**: Unity 2021.3 LTS, C#
- **Storage**: In-memory (MVP), PostgreSQL (production)
- **Platform**: Android tablets, desktop (Windows/Mac)

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Anthropic API key ([Get one here](https://console.anthropic.com/))
- Unity 2021.3 LTS (for Unity client development)

### Backend Setup

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/eduverse.git
cd eduverse/backend
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment**

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

5. **Run the server**

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 Usage

### 1. Upload Curriculum

```bash
curl -X POST "http://localhost:8000/api/curriculum/upload" \
  -F "file=@my_curriculum.pdf" \
  -F "title=Grade 2 Ocean Science"
```

Response:
```json
{
  "curriculum_id": "abc-123",
  "title": "Grade 2 Ocean Science",
  "page_count": 5,
  "word_count": 1200,
  "status": "ready_for_generation"
}
```

### 2. Analyze Curriculum

```bash
curl -X POST "http://localhost:8000/api/curriculum/analyze" \
  -H "Content-Type: application/json" \
  -d '{"curriculum_id": "abc-123"}'
```

### 3. Generate Lesson

```bash
curl -X POST "http://localhost:8000/api/lessons/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "curriculum_id": "abc-123",
    "target_duration_minutes": 20,
    "preferred_theme": "ocean"
  }'
```

Response:
```json
{
  "lesson_id": "lesson-456",
  "title": "Ocean Life Adventure",
  "theme": "ocean",
  "scene_count": 3,
  "estimated_duration_minutes": 20,
  "status": "ready"
}
```

### 4. Retrieve Lesson (for Unity)

```bash
curl "http://localhost:8000/api/lessons/lesson-456"
```

Returns complete SceneSpec JSON that Unity uses to build the 3D world.

## 🎮 Unity Client Setup

See [unity/README.md](unity/README.md) for Unity client setup instructions.

## 🧪 Testing

Run the test suite:

```bash
cd backend
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ -v --cov=app --cov-report=html
```

## 📁 Project Structure

```
eduverse/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration, security
│   │   ├── models/         # Pydantic models
│   │   ├── services/       # Business logic
│   │   ├── storage/        # Data storage
│   │   └── utils/          # Utilities
│   ├── tests/              # Test suite
│   └── main.py             # Application entry point
│
├── unity/                  # Unity client (coming soon)
│   └── EduverseClient/
│
├── docs/                   # Documentation
└── README.md
```

## 🔧 Configuration

Edit `.env` file:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Anthropic API
ANTHROPIC_API_KEY=your_api_key_here

# Security
SECRET_KEY=your-secret-key

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

## 📊 API Endpoints

### Curriculum
- `POST /api/curriculum/upload` - Upload PDF
- `POST /api/curriculum/analyze` - Analyze with AI
- `GET /api/curriculum/{id}` - Get curriculum
- `GET /api/curriculum/` - List curricula

### Lessons
- `POST /api/lessons/generate` - Generate lesson
- `GET /api/lessons/{id}` - Get lesson (for Unity)
- `GET /api/lessons/` - List lessons

### Sessions
- `POST /api/sessions/start` - Start learning session
- `POST /api/sessions/event` - Log session event
- `POST /api/sessions/end` - End session
- `GET /api/sessions/learner/{id}` - Get learner sessions

### Learners
- `POST /api/learners/` - Create learner profile
- `GET /api/learners/{id}` - Get learner
- `PATCH /api/learners/{id}` - Update learner
- `GET /api/learners/` - List learners

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Anthropic Claude for AI-powered curriculum analysis
- FastAPI for the excellent web framework
- Unity Technologies for the game engine

## 📞 Support

For questions or issues:
- GitHub Issues: [Create an issue](https://github.com/yourusername/eduverse/issues)
- Email: support@eduverse.com

---

**Made with ❤️ for children's education**
