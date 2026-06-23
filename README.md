# RAG Document Q&A System

A production-ready Retrieval-Augmented Generation (RAG) application for intelligent document querying.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React/TS)                   │
│            Chat UI · Document Manager · Admin Dashboard      │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│                     Backend (FastAPI)                        │
│   Auth · Document Processing · Embeddings · RAG · Admin     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   Vector DB (ChromaDB)                       │
│                 Semantic Search · Embeddings                  │
├─────────────────────────────────────────────────────────────┤
│                   SQLite (Relational DB)                     │
│         Users · Documents · Conversations · Messages         │
└─────────────────────────────────────────────────────────────┘
```

### Features
- **Document Upload**: Upload PDF, DOCX, TXT files
- **Embedding Generation**: Automatic text chunking and embedding
- **Semantic Search**: Vector similarity search across documents
- **RAG Q&A**: Retrieval-Augmented Generation for accurate answers
- **Conversation History**: Persistent chat history with context
- **User Authentication**: JWT-based auth with roles (admin/user)
- **Admin Dashboard**: User management, document statistics, system monitoring

```

## Tech Stack

| Layer              | Technology                         |
| ------------------ | ---------------------------------- |
| Backend            | Python 3.12+, FastAPI              |
| Frontend           | React 19, TypeScript, Vite         |
| Vector Database    | ChromaDB                           |
| Relational DB      | SQLite                             |
| Auth               | JWT (access + refresh tokens)      |
| LLM API            | OpenAI-compatible API              |
| Containerization   | Docker, Docker Compose             |
| Deployment         | Oracle Cloud Infrastructure        |
| Reverse Proxy      | Nginx                              |
| SSL                | Let's Encrypt                      |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Configuration management
│   │   ├── models.py            # Pydantic models
│   │   ├── database.py          # Database operations
│   │   ├── auth.py              # Authentication logic
│   │   ├── dependencies.py      # Dependency injection
│   │   ├── routes/
│   │   │   ├── auth.py          # Auth endpoints
│   │   │   ├── documents.py     # Document management
│   │   │   ├── chat.py          # Chat/RAG endpoints
│   │   │   ├── conversations.py # Conversation history
│   │   │   └── admin.py         # Admin endpoints
│   │   └── services/
│   │       ├── document_processor.py  # PDF/DOCX/TXT parsing
│   │       ├── embedding_service.py   # Embedding generation
│   │       ├── vector_store.py        # ChromaDB operations
│   │       ├── rag_service.py         # Retrieval + Generation
│   │       └── conversation_service.py # Conversation management
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Routes and app shell
│   │   ├── main.tsx             # Entry point
│   │   ├── index.css            # Global styles
│   │   ├── components/
│   │   │   ├── Layout.tsx       # Navigation layout
│   │   │   ├── ChatMessage.tsx  # Message bubble
│   │   │   ├── DocumentCard.tsx # Document card
│   │   │   └── ProtectedRoute.tsx # Auth guard
│   │   ├── pages/
│   │   │   ├── Login.tsx        # Login page
│   │   │   ├── Account.tsx      # Account settings
│   │   │   ├── Chat.tsx         # Chat interface
│   │   │   ├── Documents.tsx    # Document management
│   │   │   ├── Conversations.tsx # History view
│   │   │   └── Admin.tsx        # Admin dashboard
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx  # Auth state management
│   │   ├── services/
│   │   │   └── api.ts           # API client
│   │   └── types/
│   │       └── index.ts         # TypeScript types
│   ├── package.json
│   ├── vite.config.ts
│   ├── nginx.conf
│   ├── Dockerfile
│   └── index.html
├── docker-compose.yml
├── .env
├── deploy/
│   └── setup.sh                 # Deployment scripts
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.12+
- Node.js 22+
- Docker (optional, for containerized deployment)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd <repo-name>
   ```

2. **Configure environment variables**
   ```bash
   cp .env .env.local
   # Edit .env.local with your LLM_API_KEY
   ```

3. **Backend setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

4. **Frontend setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. Open http://localhost:5173 in your browser.

### Docker Setup
```bash
docker compose up --build
```

## Environment Variables

| Variable                  | Description                        | Default                                    |
| ------------------------- | ---------------------------------- | ------------------------------------------ |
| `LLM_API_KEY`             | API key for LLM provider           | (required)                                 |
| `LLM_ENDPOINT`            | LLM API endpoint                   | `https://api.openai.com/v1`                |
| `LLM_MODEL`               | LLM model for generation           | `gpt-4o-mini`                              |
| `EMBEDDING_MODEL`         | Model for embeddings               | `text-embedding-3-small`                   |
| `JWT_SECRET_KEY`          | Secret for JWT signing             | (change in production)                     |
| `JWT_EXPIRE_MINUTES`      | Access token expiry                | `30`                                       |
| `JWT_REFRESH_EXPIRE_DAYS` | Refresh token expiry               | `7`                                        |
| `CHROMA_PERSIST_DIR`      | ChromaDB persistence directory     | `./data/chromadb`                          |
| `UPLOAD_DIR`              | Upload directory                   | `./data/uploads`                           |
| `DATABASE_URL`            | SQLite database URL                | `sqlite:///./data/rag_app.db`              |

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive Swagger documentation.

### Core Endpoints

#### Authentication
| Method | Endpoint               | Description              |
| ------ | ---------------------- | ------------------------ |
| POST   | `/api/auth/register`   | Register new user        |
| POST   | `/api/auth/login`      | Login                    |
| POST   | `/api/auth/refresh`    | Refresh access token     |
| POST   | `/api/auth/logout`     | Logout                   |
| GET    | `/api/auth/me`         | Get current user         |

#### Documents
| Method | Endpoint                    | Description              |
| ------ | --------------------------- | ------------------------ |
| POST   | `/api/documents/upload`     | Upload document          |
| GET    | `/api/documents`            | List user documents      |
| GET    | `/api/documents/{id}`       | Get document details     |
| DELETE | `/api/documents/{id}`       | Delete document          |
| GET    | `/api/documents/{id}/chunks`| View document chunks     |

#### Chat / RAG
| Method | Endpoint                    | Description              |
| ------ | --------------------------- | ------------------------ |
| POST   | `/api/chat/send`            | Send message with RAG    |
| GET    | `/api/chat/{id}/messages`   | Get conversation messages|

#### Conversations
| Method | Endpoint                    | Description              |
| ------ | --------------------------- | ------------------------ |
| GET    | `/api/conversations`        | List user conversations  |
| POST   | `/api/conversations`        | Create new conversation  |
| DELETE | `/api/conversations/{id}`   | Delete conversation      |
| PATCH  | `/api/conversations/{id}`   | Update conversation title|

#### Admin
| Method | Endpoint                    | Description              |
| ------ | --------------------------- | ------------------------ |
| GET    | `/api/admin/stats`          | System statistics        |
| GET    | `/api/admin/users`          | List all users           |
| PATCH  | `/api/admin/users/{id}`     | Update user role/status  |

## Deployment

### Oracle Cloud Infrastructure (OCI)

1. Provision a compute instance (Ubuntu 22.04+)
2. Install Docker and Docker Compose
3. Clone the repository
4. Set up environment variables
5. Run `docker compose up -d`
6. Configure Nginx with SSL via Let's Encrypt

See `deploy/setup.sh` for the automated deployment script.

## CI/CD

The project uses GitHub Actions for CI/CD:
- **CI**: Run tests on every push and PR
- **CD**: Deploy to Oracle Cloud on push to main branch

## License

MIT
