# API Documentation

Base URL: `http://localhost:8000` (or `http://localhost:8100` if running via Docker default in Makefile)

## Authentication
All endpoints except authentication routes require a valid JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### Authentication

#### 1. Sign Up
- **URL**: `/auth/signup`
- **Method**: `POST`
- **Content-Type**: `application/json`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "John Doe"
}
```

#### 2. Login
- **URL**: `/auth/login`
- **Method**: `POST`
- **Content-Type**: `application/json`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer"
  }
}
```

### Business Management

#### 3. Create Business Profile
Create a business profile with custom agent configuration.

- **URL**: `/business`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Auth**: Required

**Request Body**:
```json
{
  "business_name": "Acme Support",
  "description": "Customer support for Acme products",
  "website": "https://acme.com",
  "custom_agent_instruction": "Always be professional and mention our 24/7 support availability."
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Business profile created successfully",
  "data": {
    "id": "uuid",
    "user_id": "uuid",
    "business_name": "Acme Support",
    "description": "Customer support for Acme products",
    "website": "https://acme.com",
    "custom_agent_instruction": "Always be professional and mention our 24/7 support availability.",
    "created_at": "2025-12-08T00:00:00",
    "updated_at": "2025-12-08T00:00:00"
  }
}
```

#### 4. Get Business Profile
Retrieve the current user's business profile.

- **URL**: `/business`
- **Method**: `GET`
- **Auth**: Required

**Response**:
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "user_id": "uuid",
    "business_name": "Acme Support",
    "description": "Customer support for Acme products",
    "website": "https://acme.com",
    "custom_agent_instruction": "Always be professional and mention our 24/7 support availability.",
    "created_at": "2025-12-08T00:00:00",
    "updated_at": "2025-12-08T00:00:00"
  }
}
```

#### 5. Update Business Profile
Update business profile fields.

- **URL**: `/business`
- **Method**: `PUT`
- **Content-Type**: `application/json`
- **Auth**: Required

**Request Body** (all fields optional):
```json
{
  "business_name": "Updated Name",
  "description": "New description",
  "website": "https://newsite.com",
  "custom_agent_instruction": "New instructions for the agent"
}
```

### Document Management

#### 6. Upload Documents
Uploads one or more files to the staging area.

- **URL**: `/documents/upload`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Auth**: Required

**Request Body**:
- `files`: List of files to upload (Binary)

**Response**:
```json
{
  "status": "success",
  "message": "Files uploaded successfully",
  "data": {
    "files": [
      "document1.pdf",
      "notes.txt"
    ]
  }
}
```

#### 7. List Documents
Get all documents for the current user.

- **URL**: `/documents`
- **Method**: `GET`
- **Auth**: Required

**Response**:
```json
{
  "status": "success",
  "data": [
    "document1.pdf",
    "notes.txt"
  ]
}
```

#### 8. Process Documents
Triggers the processing of uploaded documents (text splitting, embedding, and indexing).

- **URL**: `/rag/process`
- **Method**: `POST`
- **Auth**: Required

**Response**:
```json
{
  "status": "success",
  "data": [
    {
      "filename": "document1.pdf",
      "chunks_created": 15,
      "status": "success"
    },
    {
      "filename": "notes.txt",
      "chunks_created": 8,
      "status": "success"
    }
  ]
}
```

### Chat

#### 9. Chat with Agent
Interact with the AI agent which uses your business configuration and processed documents as context.

> **Note**: You must create a business profile before using this endpoint.

- **URL**: `/chat`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Auth**: Required

**Request Body**:
```json
{
  "message": "What are your support hours?"
}
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "response": "We offer 24/7 support availability for all our customers. You can reach us anytime...",
    "sources": []
  }
}
```

## Key Features

- **User-Scoped Data**: Each user's documents and business configuration are isolated
- **Dynamic Agent**: Agent is created with your business name and custom instructions
- **Context-Aware**: Agent only accesses your uploaded documents
- **Session Management**: Conversation history is maintained per user

## Running the API

You can access the interactive Swagger UI at `/docs` (e.g., `http://localhost:8000/docs`) to test endpoints directly in the browser.

## Workflow

1. **Sign up** or **Login** to get authentication tokens
2. **Create a business profile** with your business details and custom agent instructions
3. **Upload documents** related to your business
4. **Process documents** to make them searchable
5. **Chat with the agent** - it will use your business context and documents to provide relevant responses

