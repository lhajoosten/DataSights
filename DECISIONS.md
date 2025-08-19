# Architecture & Design Decisions: Talk to Your Data

**Project:** CSV to Chart LLM Application  
**Developer:** lhajoosten  
**Timeline:** ~4 hours (Take-home assignment)  
**Date:** August 19, 2025

---

## Executive Summary

This document captures the key architectural decisions, trade-offs, and problem-solving approaches used in building a full-stack application that allows users to upload CSV files and generate charts through natural language questions using Large Language Models.

## Problem Statement & Constraints

### Core Requirements
- **Upload CSV files** (max 10MB) with validation and preview
- **Natural language interface** for data exploration
- **Chart generation** from user questions using LLM
- **Real-time visualization** with interactive charts
- **4-hour development timeboxed** for MVP delivery

### Technical Constraints
- Must demonstrate **full-stack capabilities** (Backend + Frontend)
- **Type safety** throughout the application
- **Clean architecture** with proper separation of concerns
- **Production-ready patterns** despite time constraints

---

## Technology Stack Decisions

### Backend: Python FastAPI + Pydantic
**Decision:** FastAPI over Django/Flask, Express.js, or ASP.NET Core

**Rationale:**
- **Automatic OpenAPI documentation** saves development time
- **Pydantic integration** provides strong typing similar to C# models
- **Async support** critical for LLM API calls without blocking
- **Fast development** with minimal boilerplate
- **Familiar patterns** for someone coming from .NET background

**Trade-offs:**
- ✅ Rapid prototyping, excellent type safety, auto-docs
- ❌ Python ecosystem learning curve vs familiar .NET
- ❌ Less enterprise tooling compared to .NET ecosystem

### Frontend: React + TypeScript + Vite
**Decision:** React over Angular, Vue.js, or Next.js

**Rationale:**
- **Component composition** fits well with modular chart requirements
- **TypeScript integration** provides type safety across client-server boundary
- **Vite tooling** for fast development and optimized builds
- **Rich ecosystem** for charts (Recharts) and UI components
- **Transferable patterns** from Angular experience

**Trade-offs:**
- ✅ Fast iteration, excellent developer experience, huge ecosystem
- ❌ More setup compared to Angular CLI scaffolding
- ❌ State management complexity for larger applications

### Data Processing: Pandas + NumPy
**Decision:** Pandas over raw CSV parsing or database solutions

**Rationale:**
- **Rich data manipulation** capabilities for chart preparation
- **Type inference** for automatic column type detection
- **Memory efficient** for files under 10MB constraint
- **Aggregation support** for chart generation requirements
- **Industry standard** for data analysis in Python

**Trade-offs:**
- ✅ Powerful data operations, handles edge cases well
- ❌ Memory usage for larger files
- ❌ Single-threaded processing limitations

### Charts: Recharts
**Decision:** Recharts over Chart.js, D3.js, or Plotly

**Rationale:**
- **React-native** composition patterns
- **TypeScript support** out of the box
- **Sufficient chart types** for MVP (bar, line, scatter, pie)
- **Customizable** but not overly complex
- **Good documentation** for rapid implementation

**Trade-offs:**
- ✅ Easy React integration, good performance
- ❌ Less feature-rich than Plotly or D3
- ❌ Limited chart types compared to enterprise solutions

---

## Architecture Decisions

### Clean Architecture Implementation

**Decision:** Layered architecture adapted from .NET Clean Architecture patterns

```
Backend Structure:
├── api/          # Controllers (Presentation Layer)
├── services/     # Application Services (Business Logic)
├── models/       # DTOs/Schemas (Data Contracts)
├── core/         # Cross-cutting concerns
└── utils/        # Infrastructure utilities

Frontend Structure:
├── features/     # Feature modules (like Angular)
├── services/     # API clients (like Angular services)
├── hooks/        # State management (like RxJS patterns)
├── components/   # Reusable UI components
└── types/        # TypeScript interfaces
```

**Rationale:**
- **Familiar patterns** from .NET/Angular experience
- **Separation of concerns** makes testing easier
- **Scalable structure** for future enhancements
- **Dependency direction** follows clean architecture principles

### API Design: RESTful with Clear Contracts

**Decision:** REST API with Pydantic schemas over GraphQL or RPC

**Endpoints Design:**
```
POST /api/v1/csv/upload          # File upload with validation
GET  /api/v1/csv/{id}/metadata   # CSV schema for LLM context
POST /api/v1/chat/ask            # Natural language processing
GET  /api/v1/health              # System health monitoring
```

**Rationale:**
- **Simple and predictable** for frontend consumption
- **Auto-generated documentation** with FastAPI
- **Type safety** with Pydantic request/response models
- **RESTful conventions** familiar to frontend developers

### State Management: Custom Hooks over Redux

**Decision:** React custom hooks over Redux, Zustand, or Context API

**Implementation:**
```typescript
useCSVUpload()  // File upload state management
useChat()       // Conversation and chart state
```

**Rationale:**
- **Simpler implementation** for limited scope
- **React-native patterns** with hooks
- **Type safety** with TypeScript
- **Minimal boilerplate** compared to Redux
- **Collocated logic** similar to Angular services

**Trade-offs:**
- ✅ Simple, no external dependencies, good performance
- ❌ Doesn't scale to complex state relationships
- ❌ No time-travel debugging like Redux DevTools

---

## Data Flow & Processing Decisions

### CSV Processing Pipeline

**Decision:** Multi-stage validation and processing pipeline

```
Upload → Client Validation → Server Validation → 
Type Inference → Data Cleaning → Preview Generation
```

**Implementation Details:**
1. **Client-side validation** (file type, size) prevents unnecessary uploads
2. **Server-side re-validation** ensures security and data integrity
3. **Intelligent type inference** handles mixed data types gracefully
4. **Data cleaning** normalizes column names and handles null values
5. **Preview generation** limits displayed rows for performance

**Rationale:**
- **Defense in depth** with multiple validation layers
- **User experience** with immediate feedback
- **Data quality** through cleaning and normalization
- **Performance** by limiting preview data size

### LLM Integration Strategy

**Decision:** OpenAI API with structured prompts and fallback mechanisms

**Prompt Engineering Approach:**
```python
System Prompt: CSV schema + available columns + chart rules
User Prompt: Natural language question + context
Response Format: Structured JSON with chart specification
```

**Fallback Strategy:**
1. **OpenAI API failure** → Rule-based chart suggestions
2. **Invalid JSON response** → Request clarification
3. **Chart validation failure** → Suggest simpler alternatives
4. **Network timeout** → Graceful error handling

**Rationale:**
- **Structured outputs** ensure predictable chart generation
- **Robust error handling** provides good user experience
- **Fallback mechanisms** work without API keys for demonstration
- **Context awareness** through CSV schema injection

### Chart Generation Pipeline

**Decision:** Server-side data processing with client-side rendering

```
User Question → LLM Processing → Chart Specification → 
Data Transformation → JSON Response → React Chart Rendering
```

**Chart Specification Format:**
```typescript
interface ChartSpec {
  chart_type: 'bar' | 'line' | 'scatter' | 'pie';
  x?: string;           // Column for X-axis
  y?: string;           // Column for Y-axis  
  aggregation?: string; // sum, mean, count, etc.
  group_by?: string[];  // Grouping columns
  filters?: FilterSpec[]; // Data filters
  explanation: string;  // Human-readable description
}
```

**Rationale:**
- **Declarative approach** separates logic from rendering
- **Type safety** with Pydantic validation on server
- **Flexibility** supports multiple chart types and operations
- **Performance** by processing data server-side

---

## Security & Data Handling Decisions

### File Upload Security

**Decision:** Multi-layered security approach

**Implementation:**
- **File type validation** (CSV only) on client and server
- **File size limits** (10MB) to prevent DoS attacks
- **Content validation** to ensure actual CSV format
- **Temporary storage** with automatic cleanup
- **No arbitrary code execution** from user data

**Rationale:**
- **Defense in depth** security model
- **Resource protection** against abuse
- **Data privacy** through temporary storage
- **Safe processing** with controlled data operations

### Data Processing Safety

**Decision:** Controlled data operations without code execution

**Implementation:**
```python
# Safe operations only
ALLOWED_AGGREGATIONS = ['sum', 'mean', 'count', 'min', 'max']
ALLOWED_OPERATORS = ['==', '!=', '>', '>=', '<', '<=', 'in', 'not_in']

# No eval() or exec() - only pandas operations
# Parameterized filters and aggregations
# Schema validation at every boundary
```

**Rationale:**
- **Prevent code injection** through LLM responses
- **Controlled operations** limit attack surface
- **Input validation** at every boundary
- **Audit trail** through structured logging

### API Security

**Decision:** Basic security measures appropriate for MVP

**Implementation:**
- **CORS configuration** for known origins
- **Request size limits** to prevent DoS
- **Error handling** without information leakage
- **Structured logging** for audit trails
- **Health checks** for monitoring

**Future Enhancements:**
- JWT authentication for user sessions
- Rate limiting per user/IP
- API key management for LLM services
- Input sanitization for production use

---

## Performance Optimization Decisions

### Frontend Performance

**Decision:** React optimization patterns for smooth UX

**Implementation:**
- **Component memoization** with React.memo for chart components
- **Efficient re-renders** with proper dependency arrays
- **Virtualized scrolling** for large datasets (future enhancement)
- **Code splitting** with React.lazy for route components
- **Asset optimization** with Vite's build tools

### Backend Performance

**Decision:** Async processing with caching strategies

**Implementation:**
- **Async file processing** doesn't block other requests
- **Streaming responses** for large data operations
- **Connection pooling** for database connections (future)
- **Memory management** with proper pandas operations
- **Request timeouts** for LLM API calls

### Data Processing Performance

**Decision:** In-memory processing with limits

**Current Approach:**
- **10MB file limit** keeps memory usage reasonable
- **Pandas operations** optimized for small to medium datasets
- **Preview limiting** (20 rows) for UI responsiveness
- **Chart data limiting** (1000 points) for rendering performance

**Scaling Strategy:**
- **Streaming processing** for larger files
- **Database storage** for persistent data
- **Chunked processing** for memory efficiency
- **Caching layer** for repeated operations

---

## Error Handling & User Experience

### Error Handling Strategy

**Decision:** Comprehensive error handling with user-friendly messages

**Implementation Layers:**
1. **Client-side validation** with immediate feedback
2. **Global error interceptors** for API communication
3. **Structured server errors** with actionable messages
4. **LLM error recovery** with clarification prompts
5. **Fallback mechanisms** for degraded functionality

**Error Categories:**
```typescript
interface ApiError {
  message: string;     // User-friendly message
  type: string;        // Error classification
  details?: object;    // Technical details for debugging
}
```

### User Experience Decisions

**Decision:** Progressive disclosure with clear feedback

**UX Patterns:**
- **Step-by-step workflow** (Upload → Analyze)
- **Progress indicators** for async operations
- **Contextual help** with suggested questions
- **Error recovery** with retry mechanisms
- **Loading states** for all async operations

**Accessibility Considerations:**
- **Keyboard navigation** support
- **Screen reader compatibility** with proper ARIA labels
- **Color contrast** meeting WCAG guidelines
- **Focus management** for modal interactions

---

## Testing Strategy Decisions

### Testing Approach

**Decision:** Focused testing for critical paths given time constraints

**Testing Priorities:**
1. **API contract testing** with Pydantic validation
2. **CSV processing edge cases** (empty files, malformed data)
3. **LLM response parsing** with mock data
4. **Chart generation validation** with known datasets
5. **Error handling scenarios** for robustness

**Testing Tools:**
- **Backend:** pytest with async support, mock LLM responses
- **Frontend:** Jest/React Testing Library for components
- **Integration:** End-to-end tests for critical workflows
- **Manual testing:** Various CSV formats and edge cases

**Test Data Strategy:**
```
sample_datasets/
├── sales_data.csv          # Standard business data
├── time_series.csv         # Date/time handling
├── mixed_types.csv         # Type inference testing
├── edge_cases.csv          # Null values, special chars
└── large_dataset.csv       # Performance testing
```

---

## Deployment & DevOps Decisions

### Development Environment

**Decision:** Container-based development for consistency

**Implementation:**
```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - ENVIRONMENT=development
  
  frontend:
    build: ./frontend  
    ports: ["5173:5173"]
    depends_on: [backend]
```

**Benefits:**
- **Environment consistency** across development machines
- **Easy onboarding** for new developers
- **Production parity** with containerized deployment
- **Isolated dependencies** prevent version conflicts

### Configuration Management

**Decision:** Environment-based configuration with sensible defaults

**Implementation:**
```python
# Pydantic Settings for type-safe configuration
class Settings(BaseSettings):
    environment: str = "development"
    openai_api_key: str = ""
    max_file_size_mb: int = 10
    
    class Config:
        env_file = ".env"
```

**Configuration Hierarchy:**
1. **Environment variables** (highest priority)
2. **.env files** for local development
3. **Default values** for development setup
4. **Validation** with Pydantic for type safety

---

## Documentation Strategy

### Code Documentation

**Decision:** Self-documenting code with strategic comments

**Approach:**
- **TypeScript interfaces** serve as living documentation
- **Pydantic models** with field descriptions
- **FastAPI automatic docs** at `/docs` endpoint
- **Inline comments** for business logic explanations
- **README files** for setup and usage

### Decision Documentation

**Decision:** Architecture Decision Records (this document)

**Structure:**
- **Context** explaining the problem
- **Decision** with clear rationale
- **Trade-offs** acknowledging limitations
- **Future considerations** for evolution

---

## Known Limitations & Technical Debt

### Current Limitations

**Data Scale:**
- **10MB file limit** constrains dataset size
- **In-memory processing** doesn't scale to GB files
- **Single-threaded** pandas operations for safety

**Chart Capabilities:**
- **Limited chart types** (4 basic types)
- **No multi-series** complex visualizations
- **Basic styling** without customization options

**LLM Integration:**
- **Single model** (OpenAI GPT-3.5) dependency
- **No conversation memory** beyond context window
- **Prompt engineering** needs refinement for complex queries

### Technical Debt Inventory

**High Priority:**
1. **Error handling** needs more granular categories
2. **LLM prompt engineering** requires more sophisticated templates
3. **Chart validation** should provide better error messages
4. **File cleanup** needs automated background jobs

**Medium Priority:**
1. **Caching layer** for repeated LLM queries
2. **Database persistence** for chat history
3. **User authentication** for multi-user scenarios
4. **Advanced chart options** (colors, styling, labels)

**Low Priority:**
1. **Performance monitoring** with metrics
2. **Internationalization** for multi-language support
3. **Advanced data transformations** (joins, calculations)
4. **Export capabilities** (PDF, PNG chart downloads)

---

## Future Enhancement Roadmap

### Phase 2: Enhanced Capabilities (Next 2 weeks)

**Data Processing:**
- **Streaming file processing** for larger datasets
- **Multiple file support** with join operations
- **Advanced data transformations** (calculated columns)
- **Data quality assessment** and recommendations

**Chart Enhancements:**
- **Interactive charts** with drill-down capabilities
- **Custom styling** and branding options
- **Chart templates** for common business scenarios
- **Export functionality** (PNG, PDF, data downloads)

**User Experience:**
- **Chart comparison** side-by-side views
- **Dashboard creation** with multiple charts
- **Saved queries** and chart favorites
- **Collaborative features** for team analysis

### Phase 3: Enterprise Features (1-2 months)

**Authentication & Authorization:**
- **User management** with role-based access
- **Organization support** with data isolation
- **SSO integration** for enterprise environments
- **Audit logging** for compliance requirements

**Data Sources:**
- **Database connectors** (PostgreSQL, MySQL, SQL Server)
- **API integrations** for live data feeds
- **Cloud storage** (S3, Azure Blob, Google Cloud)
- **Data warehouses** (Snowflake, BigQuery, Redshift)

**Advanced Analytics:**
- **Statistical analysis** integration (R, Python)
- **Machine learning** model predictions
- **Time series forecasting** capabilities
- **Advanced aggregations** and calculations

### Phase 4: Scale & Performance (2-3 months)

**Architecture Evolution:**
- **Microservices** architecture for component scaling
- **Message queues** for async processing
- **Distributed caching** with Redis
- **Load balancing** for high availability

**Performance Optimization:**
- **Columnar storage** for analytical workloads
- **Query optimization** with indexing strategies
- **CDN integration** for global performance
- **Progressive web app** features for mobile

---

## Lessons Learned & Retrospective

### What Worked Well

**Technology Choices:**
- **FastAPI + Pydantic** provided excellent developer experience
- **React + TypeScript** enabled rapid UI development
- **Recharts** met visualization needs with minimal complexity
- **Clean architecture** patterns scaled well despite time pressure

**Development Process:**
- **Iterative approach** with working features at each step
- **Type-first development** caught errors early
- **Component composition** enabled rapid UI assembly
- **Error-first design** created robust user experience

### What Could Be Improved

**Time Management:**
- **LLM integration** took longer than expected (prompt engineering complexity)
- **Error handling** implementation was rushed in some areas
- **Testing** was deprioritized due to time constraints
- **Documentation** was written post-implementation instead of during

**Technical Decisions:**
- **Pandas warnings** should have been addressed earlier
- **Chart validation** could be more sophisticated
- **State management** might benefit from Redux for complex scenarios
- **API design** could include more pagination and filtering

### Key Insights

**Full-Stack Development:**
- **Type safety** across boundaries significantly improves development speed
- **Error handling** is critical for LLM-powered applications
- **User feedback** mechanisms are essential for AI interactions
- **Fallback strategies** make applications more resilient

**AI Integration:**
- **Structured prompts** are crucial for reliable LLM outputs
- **Validation layers** prevent malformed AI responses from breaking UX
- **Context management** significantly improves response quality
- **Error recovery** patterns are different from traditional applications

---

## Conclusion

This take-home project successfully demonstrates full-stack development capabilities while implementing a complex AI-powered data visualization system. The architecture decisions prioritize rapid development while maintaining code quality, type safety, and user experience.

The chosen technology stack (FastAPI + React + TypeScript) proved effective for the requirements, enabling both rapid prototyping and production-ready patterns. The clean architecture approach facilitated testing and will support future enhancements.

Key achievements:
- ✅ **Complete end-to-end workflow** from CSV upload to chart generation
- ✅ **Type-safe implementation** across frontend and backend
- ✅ **Robust error handling** with graceful degradation
- ✅ **Clean architecture** following established patterns
- ✅ **AI integration** with fallback mechanisms
- ✅ **Production-ready** code organization and documentation

The application serves as a solid foundation for a production data visualization platform, with clear paths for enhancement and scaling outlined in the roadmap.

**Time Investment:** ~4 hours (as requested for take-home assignment)  
**Lines of Code:** ~3,500 (Backend: ~2,000, Frontend: ~1,500)  
**Test Coverage:** Basic validation and error handling tests included

---

*This document serves as both a technical reference and a demonstration of architectural thinking and decision-making processes in full-stack development.*