# RAG Chatbot Query Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>(script.js)
    participant FastAPI as FastAPI Server<br/>(app.py)
    participant RAG as RAG System<br/>(rag_system.py)
    participant Session as Session Manager<br/>(session_manager.py)
    participant AI as AI Generator<br/>(ai_generator.py)
    participant Claude as Anthropic Claude<br/>(API)
    participant Tools as Tool Manager<br/>(search_tools.py)
    participant Vector as Vector Store<br/>(vector_store.py)
    participant Chroma as ChromaDB<br/>(Database)

    %% User Input Phase
    User->>Frontend: Types query & clicks send
    Frontend->>Frontend: Show loading spinner
    
    %% API Request Phase
    Frontend->>+FastAPI: POST /api/query<br/>{query, session_id}
    FastAPI->>FastAPI: Validate request
    
    %% Session Management
    FastAPI->>+RAG: query(user_query, session_id)
    RAG->>+Session: get_conversation_history(session_id)
    Session-->>-RAG: Previous messages context
    
    %% AI Generation with Tools
    RAG->>+AI: generate_response(query, history, tools)
    AI->>AI: Build system prompt + context
    AI->>+Claude: API call with tools enabled
    
    %% Claude Decides to Use Tools
    Claude-->>-AI: Response with tool_use
    Note over AI,Claude: Claude wants to search course content
    
    %% Tool Execution Phase
    AI->>+Tools: execute_tool("search_course_content", params)
    Tools->>+Vector: search(query, course_name, lesson_number)
    Vector->>Vector: Convert query to embeddings
    Vector->>+Chroma: Similarity search with filters
    Chroma-->>-Vector: Ranked results + metadata
    Vector-->>-Tools: SearchResults with documents
    Tools->>Tools: Format results with sources
    Tools-->>-AI: Formatted search context
    
    %% Final AI Response
    AI->>+Claude: Second API call with search results
    Claude-->>-AI: Final synthesized answer
    AI-->>-RAG: Generated response text
    
    %% Session Update
    RAG->>Session: add_exchange(session_id, query, response)
    RAG->>Tools: get_last_sources() for citations
    RAG-->>-FastAPI: (answer, sources)
    
    %% Response to Frontend
    FastAPI-->>-Frontend: QueryResponse{answer, sources, session_id}
    Frontend->>Frontend: Remove loading spinner
    Frontend->>Frontend: Display answer with sources
    Frontend->>User: Show formatted response
    
    %% Session Persistence
    Note over Frontend: session_id stored for next query
    Note over Session: Conversation history maintained
```

## Key Components & Responsibilities

### Frontend Layer
- **script.js**: User interface, API calls, message display
- **HTML/CSS**: Chat interface, loading states, source citations

### API Layer  
- **app.py**: FastAPI endpoints, request validation, CORS handling
- **models.py**: Pydantic models for request/response structure

### RAG Orchestration
- **rag_system.py**: Main coordinator between all components
- **session_manager.py**: Conversation history and context management

### AI & Search
- **ai_generator.py**: Claude API integration, tool execution handling
- **search_tools.py**: Tool definitions and search result formatting
- **vector_store.py**: ChromaDB interface, embedding generation

### Data Processing
- **document_processor.py**: Text chunking, course structure parsing
- **ChromaDB**: Vector storage, similarity search, metadata filtering

## Flow Characteristics

1. **Stateful Conversations**: Session management maintains context across queries
2. **Tool-Augmented AI**: Claude decides when to search based on query content
3. **Semantic Search**: Vector embeddings enable contextual content retrieval  
4. **Source Attribution**: Search results provide citations for transparency
5. **Filtered Search**: Can target specific courses or lessons when requested
6. **Async Processing**: Non-blocking operations with loading indicators

## Error Handling

- Network failures → Frontend shows error message
- Search failures → Tools return "No results found" 
- AI failures → FastAPI returns 500 status with error details
- Session failures → Creates new session automatically