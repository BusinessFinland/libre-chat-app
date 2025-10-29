# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LibreChat for Business Finland is an AI chat application forked from Danny Avila's open-source LibreChat project. It provides a web-based interface for interacting with various AI language models and includes advanced features like agents, assistants, and file handling.

## Architecture

This is a full-stack JavaScript/TypeScript application with a monorepo structure:

- **Backend (api/)**: Node.js/Express server with MongoDB database
- **Frontend (client/)**: React + Vite application with TypeScript
- **Packages**: Shared libraries for data-provider, data-schemas, and MCP integration
- **Configuration**: Docker-compose for containerized deployment

### Key Technologies
- **Backend**: Express.js, Passport.js (auth), Mongoose (MongoDB), various AI SDKs (OpenAI, Anthropic, Google)
- **Frontend**: React 18, Recoil (state), TanStack Query, Radix UI, Tailwind CSS
- **Build Tools**: Vite (frontend), Node.js (backend), Jest (testing)
- **Database**: MongoDB with Mongoose ODM

## Common Development Commands

### Backend Development
```bash
# Start backend in development mode
npm run backend:dev

# Start backend in production mode  
npm run backend

# Run backend tests
npm run test:api
```

### Frontend Development
```bash
# Start frontend development server
npm run frontend:dev

# Build frontend for production
npm run frontend

# Run frontend tests
npm run test:client
```

### Full Stack Development
```bash
# Build data provider and dependencies
npm run build:data-provider
npm run build:mcp
npm run build:data-schemas

# Run E2E tests
npm run e2e
npm run e2e:headed
```

### Code Quality
```bash
# Lint code
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format
```

### Docker Development
```bash
# Start services with Docker Compose
docker-compose up -d

# Stop services
docker-compose down
```

## Project Structure

### Backend (api/)
- `server/` - Express server setup and main routes
- `models/` - Mongoose schemas and database models
- `controllers/` - Route handlers for different endpoints
- `middleware/` - Authentication, validation, and other middleware
- `services/` - Business logic and external service integrations
- `strategies/` - Passport.js authentication strategies
- `lib/` - Database connection and utilities
- `utils/` - Helper functions and utilities

### Frontend (client/)
- `src/components/` - React components organized by feature
- `src/hooks/` - Custom React hooks
- `src/store/` - Recoil state management
- `src/routes/` - React Router configuration
- `src/utils/` - Client-side utilities
- `src/data-provider/` - API integration logic

### Packages
- `data-provider/` - Shared API client and data fetching logic
- `data-schemas/` - Zod schemas for data validation
- `mcp/` - Model Context Protocol integration

## Key Features

- **Multi-Model Support**: OpenAI, Anthropic, Google, Ollama, and custom endpoints
- **Agents**: Autonomous AI agents with tool calling capabilities
- **Assistants**: OpenAI-style assistants with file and code interpretation
- **File Handling**: Upload, process, and manage files with vector search
- **Authentication**: Multiple providers (local, OAuth, LDAP)
- **Conversation Management**: Persistent chat history with search and organization
- **Plugin System**: Extensible tool and plugin architecture

## Environment Setup

The application requires a `.env` file in the root directory. Key environment variables include:
- Database connection (`MONGO_URI`)
- AI provider API keys (OpenAI, Anthropic, etc.)
- Authentication configuration
- Feature toggles and service URLs

Refer to `librechat.example.yaml` for configuration examples.

## Testing

- **Frontend**: Jest with React Testing Library
- **Backend**: Jest with Supertest for API testing
- **E2E**: Playwright for end-to-end testing
- **A11y**: Accessibility testing with axe-core

## Deployment

The application supports multiple deployment methods:
- Docker Compose (development and production)
- Kubernetes with Helm charts
- Manual deployment with Node.js

Configuration files:
- `docker-compose.yml` - Main compose file
- `charts/` - Helm charts for Kubernetes
- `config/` - Deployment and management scripts