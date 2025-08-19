DataSights/
├── README.md
├── DECISIONS.md
├── .gitignore
├── docker-compose.yml (optional)
├── frontend/                    # React TypeScript
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── features/           # Feature-specific modules
│   │   │   ├── upload/
│   │   │   ├── chat/
│   │   │   └── charts/
│   │   ├── services/           # API client, utilities
│   │   ├── types/              # TypeScript interfaces
│   │   └── App.tsx
│   └── public/
└── backend/                     # FastAPI Python
    ├── requirements.txt
    ├── app/
    │   ├── __init__.py
    │   ├── main.py             # FastAPI app entry
    │   ├── api/                # Route handlers
    │   ├── core/               # Config, security, dependencies
    │   ├── models/             # Pydantic models/schemas
    │   ├── services/           # Business logic
    │   │   ├── csv_service.py
    │   │   ├── llm_service.py
    │   │   └── chart_service.py
    │   └── utils/              # Helpers, validators
    └── tests/                # Unit tests
        ├── __init__.py
        ├── test_csv_service.py
        ├── test_llm_service.py
        └── test_chart_service.py