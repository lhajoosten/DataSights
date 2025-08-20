# DataSights - Architecture Decisions

**Project:** CSV to Chart LLM Application  
**Developer:** lhajoosten  
**Date:** August 2025

## Overview

A full-stack application that lets users upload CSV files and generate charts through natural language questions using LLM integration.

## Technology Choices

### Backend: Python FastAPI
- **Why:** Fast development, automatic API docs, strong typing with Pydantic
- **Trade-off:** Python vs familiar .NET, but rapid prototyping won

### Frontend: React + TypeScript
- **Why:** Component composition fits charts well, strong typing, fast iteration
- **Trade-off:** More setup than Angular, but flexible for this use case

### Charts: Recharts
- **Why:** React-native, TypeScript support, sufficient chart types for MVP
- **Trade-off:** Less powerful than D3, but much simpler to implement

### Data: Pandas
- **Why:** Industry standard, handles CSV edge cases, rich data operations
- **Trade-off:** Memory usage, but fine for 10MB limit

## Architecture

```
Backend (FastAPI)                Frontend (React + TypeScript)
├── api/        (REST endpoints) ├── features/    (feature modules)
├── services/   (business logic) ├── services/    (API calls)
├── models/     (Pydantic DTOs)  ├── components/  (UI elements)
└── core/       (config, utils)  ├── types/       (TypeScript interfaces)
                 └── core/        (shared config/utils)
```

- Clear separation of concerns in both backend and frontend.
- Shared naming conventions for easier onboarding and maintenance.
- Modular structure supports scaling and feature growth.


## Key Decisions

### Multi-dimensional Charts
- **Problem:** "Show by region and product" needs grouped visualization
- **Solution:** Enhanced chart renderer with data reshaping for multi-series
- **Implementation:** Separate series keys, color mapping, proper aggregation

### LLM Integration
- **Approach:** Structured prompts with JSON response format
- **Fallback:** Rule-based responses when OpenAI unavailable
- **Safety:** No code execution, only pandas operations

### Error Handling
- **Strategy:** Graceful degradation with user-friendly messages
- **Layers:** Client validation → Server validation → LLM fallback
- **UX:** Clear feedback, retry mechanisms, helpful suggestions

## Current Limitations

- **File size:** 10MB limit for memory efficiency
- **Chart types:** 4 basic types (bar, line, scatter, pie)
- **LLM:** Single model dependency (OpenAI)
- **Scale:** In-memory processing only

## What Worked Well

- **Type safety** across frontend/backend boundary
- **Clean architecture** scaled well under time pressure
- **Component composition** enabled rapid chart development
- **Structured LLM responses** provided reliable chart generation

## Key Insights

- **Multi-dimensional grouping** was more complex than expected
- **Error handling** critical for LLM-powered apps
- **Fallback strategies** essential for reliability
- **Data reshaping** needed for proper chart visualization

---

*Simple, clean code following .NET development principles adapted to Python/React stack.*