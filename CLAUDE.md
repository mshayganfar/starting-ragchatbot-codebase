# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Quick start using the shell script
chmod +x run.sh
./run.sh

# Manual start
cd backend && uv run --python 3.11 uvicorn app:app --reload --port 8000
```

### Dependency Management
```bash
# Install/sync dependencies
uv sync

# Run with specific Python version
uv run --python 3.11 <command>
```

### Code Quality Tools
```bash
# Format code with black and isort
./scripts/format.sh

# Run linting checks (flake8, black, isort)
./scripts/lint.sh

# Run tests
./scripts/test.sh

# Run complete quality check suite (format + lint + test)
./scripts/check-all.sh

# Manual commands (if needed)
uv run --python 3.11 black .
uv run --python 3.11 isort .
uv run --python 3.11 flake8 .
uv run --python 3.11 pytest tests/ -v
```

### Environment Setup
- Create `.env` file with `ANTHROPIC_API_KEY=your_api_key_here`
- Requires Python 3.11 or higher
- Uses uv package manager for dependency management

## High-Level Architecture

This is a RAG (Retrieval-Augmented Generation) chatbot system for course materials with the following key components:

### Core Architecture Pattern
The system follows a modular RAG pipeline:
1. **Document Processing** → **Vector Storage** → **AI Generation** → **Web Interface**
2. Uses tool-based search where the AI can call search functions rather than receiving pre-filtered context

### Key Components

#### RAGSystem (rag_system.py)
- Main orchestrator that coordinates all components
- Handles document ingestion via `add_course_document()` and `add_course_folder()`
- Processes queries through `query()` method using tool-based approach
- Manages conversation context through SessionManager

#### VectorStore (vector_store.py)
- Dual ChromaDB collections: `course_catalog` (metadata) and `course_content` (chunks)
- Uses SentenceTransformer embeddings (all-MiniLM-L6-v2)
- Semantic search with filtering by course name and lesson number
- Course name resolution through vector search of catalog

#### Document Processing (document_processor.py)
- Parses structured course documents with expected format:
  ```
  Course Title: [title]
  Course Link: [url] 
  Course Instructor: [instructor]
  Lesson N: [lesson title]
  [lesson content]
  ```
- Sentence-based chunking with configurable overlap (800 chars, 100 overlap)
- Adds contextual prefixes to chunks (e.g., "Course X Lesson Y content: ...")

#### AI Generation (ai_generator.py)
- Uses Anthropic Claude (claude-sonnet-4-20250514) via official SDK
- Tool-based architecture where AI calls search functions as needed
- Conversation memory support through session management
- System prompt optimized for educational content with search tool usage

#### Search Tools (search_tools.py)
- `CourseSearchTool`: Allows AI to search course content with optional filtering
- Tool-based approach enables AI to decide when and how to search
- Supports course name resolution and lesson-specific queries

#### Web Interface
- FastAPI backend serving REST API (`/api/query`, `/api/courses`)
- Static file serving for frontend (HTML/CSS/JS in `/frontend`)
- CORS enabled for development

### Data Models (models.py)
- `Course`: Contains title, instructor, course_link, and lessons list
- `Lesson`: Individual lesson with number, title, and lesson_link  
- `CourseChunk`: Text chunk with course context and metadata

### Configuration (config.py)
- Centralized config using environment variables and defaults
- Key settings: chunk size (800), overlap (100), max results (5), embedding model

### Key Design Decisions
1. **Tool-based RAG**: AI decides when to search rather than always providing context
2. **Dual vector collections**: Separate course metadata from content for efficient filtering
3. **Contextual chunking**: Chunks include course and lesson context for better retrieval
4. **Session management**: Conversation history maintained per session
5. **Course name resolution**: Semantic matching of user-provided course names to actual titles

This architecture enables natural language querying of course materials with intelligent context retrieval and conversation continuity.