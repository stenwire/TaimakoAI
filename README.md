# Taimako

**Taimako** is a modern SaaS platform designed to empower businesses with AI-driven customer experience tools. It provides an intelligent, retrieval-augmented generation (RAG) chat widget that can be easily embedded into any website, allowing businesses to automate customer support and engagement using their own knowledge base.

## 🚀 Key Features

*   **Smart Chat Widget**: A lightweight, highly customizable chat widget that sits on client websites. It uses advanced RAG techniques to answer user queries based on uploaded documents.
*   **Agentic RAG Engine**: Powered by a robust backend agent that acts as an intelligent assistant, capable of understanding context and providing accurate answers.
*   **Business Dashboard**: A comprehensive dashboard for business owners to:
    *   Manage their workspace and profile.
    *   Upload and index documents (PDFs, text, etc.) for the knowledge base.
    *   Monitor chat interactions and analytics.
    *   Configure widget appearance and behavior.
*   **Secure Authentication**: Integrated Google OAuth2 for secure and seamless user sign-in.
*   **Multi-Tenancy**: Built from the ground up to support multiple business tenants, keeping data isolated and secure.

## 🏗 Architecture

Taimako is built as a modern full-stack application with a clear separation of concerns:

### Frontend (`/frontend`)
*   **Framework**: Next.js (React)
*   **Styling**: Tailwind CSS, generic CSS variables for theming.
*   **Language**: TypeScript.
*   **Key Pages**:
    *   Landing Page: public-facing marketing page.
    *   App Dashboard: `/app/dashboard` (protected routes).
    *   Widget: `/widget/[public_widget_id]` (iframe/embedded view).

### Backend (`/agentic_rag_api`)
*   **Framework**: FastAPI (Python).
*   **Database**: SQL database (accessed via SQLAlchemy).
*   **Vector Search**: Integrated vector store for RAG operations (implementation details in `rag_service`).
*   **Auth**: OAuth2 with JWT tokens.

## 🛠 Tech Stack

*   **Frontend**: Next.js, React, Tailwind CSS, Lucide React, Framer Motion.
*   **Backend**: Python 3.x, FastAPI, SQLAlchemy, Alembic, Pydantic.
*   **Infrastructure**: Docker (implied), potential AWS/Cloud deployment.

## 📦 Getting Started

### Prerequisites
*   Node.js & npm/yarn
*   Python 3.10+
*   PostgreSQL (or equivalent SQL DB)

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/taimako.git
    cd taimako
    ```

2.  **First Time Setup**:
    ```bash
    # Build containers
    make build

    # Start everything (PostgreSQL will initialize on first run)
    make start

    # In another terminal, run migrations
    make migrate
    ```

3.  **Access the App**:
    *   Frontend: `http://localhost:3000`
    *   Backend API Docs: `http://localhost:8000/docs`

## 🤝 Contributing


## 📄 License

