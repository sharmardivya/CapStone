# General Instructions

[This document contains implementation guidelines, technology stack requirements, coding standards, and development constraints for building the agentic solution.]

> **Note:** This document specifies the **HOW TO BUILD** (technology stack, frameworks, coding standards). For problem specification, see **UserSystemInteraction.md**. For solution architecture, see **AgentSpecificationDocument.md**.

# Technology Stack

## Programming Language

[Specify the programming language and version requirements]

- **Language:** [e.g., Python 3.8+, JavaScript/TypeScript, etc.]
- **Version Requirements:** [Minimum and/or maximum versions if applicable]

## Core Frameworks

[Specify the main frameworks and libraries to be used]

- **[Framework 1]:** [Version] - [Purpose, e.g., LangGraph 0.0.20+ for agent orchestration]
- **[Framework 2]:** [Version] - [Purpose, e.g., LangChain 0.1.0+ for state management]
- **[Framework 3]:** [Version] - [Purpose]

## AI/ML Services

[Specify AI services, APIs, and models to be used]

- **LLM Provider:** [e.g., Groq API, OpenAI, Anthropic, etc.]
- **Primary Model:** [e.g., "meta-llama/llama-4-maverick-17b-128e-instruct" for multimodal tasks]
- **Secondary Model (if applicable):** [e.g., "llama-3.3-70b-versatile" for code generation]
- **API Configuration:** [Any specific API settings, rate limits, etc.]

## External Libraries

[Specify other required libraries and their purposes]

- **[Library 1]:** [Version] - [Purpose, e.g., Pillow 10.0.0+ for image processing]
- **[Library 2]:** [Version] - [Purpose]
- **[Library 3]:** [Version] - [Purpose]

## Development Tools

[Specify development and build tools]

- **Package Manager:** [e.g., pip, npm, poetry, etc.]
- **Environment Management:** [e.g., venv, conda, etc.]
- **Code Quality Tools:** [e.g., linters, formatters, type checkers]
- **Testing Framework:** [e.g., pytest, unittest, jest, etc.]

# Implementation Guidelines

## Code Structure

[Specify the expected code organization and file structure]

**Project Structure:**
```
[project_name]/
├── [main_entry_point].[ext]          # Entry point
├── workflow.[ext]                     # Orchestration logic
├── agents/                            # Agent implementations
│   ├── __init__.[ext]
│   ├── state.[ext]                   # State definitions
│   ├── [agent1].[ext]
│   ├── [agent2].[ext]
│   └── ...
├── config/                            # Configuration files
│   ├── .env.example
│   └── ...
├── requirements.txt                   # Dependencies
└── output/                            # Output directory
```

**Naming Conventions:**
- [Convention 1: e.g., Use snake_case for Python files]
- [Convention 2: e.g., Use PascalCase for class names]
- [Convention 3: e.g., Use descriptive names for agents]

## Framework-Specific Guidelines

[Specify how to use the chosen frameworks]

### [Framework Name] Guidelines

- [Guideline 1: e.g., Use LangGraph StateGraph for workflow definition]
- [Guideline 2: e.g., Use TypedDict for state definitions]
- [Guideline 3: e.g., Implement agents as classes with specific methods]

## API Usage Guidelines

[Specify how to interact with external APIs]

- **API Client Setup:** [How to initialize API clients]
- **Authentication:** [How to handle API keys, e.g., use environment variables]
- **Error Handling:** [How to handle API errors]
- **Rate Limiting:** [How to handle rate limits if applicable]
- **Retry Logic:** [Retry strategies for API calls]

## State Management

[Specify how state should be managed]

- **State Structure:** [How to define state, e.g., TypedDict, Pydantic models, etc.]
- **State Flow:** [How state flows between agents]
- **State Validation:** [How to validate state at different stages]

## Error Handling

[Specify error handling patterns]

- **Error Types:** [What types of errors to handle]
- **Error Propagation:** [How errors should propagate through the system]
- **Logging:** [How to log errors, e.g., use Python logging module]
- **User-Facing Errors:** [How to present errors to users]

## Code Quality Standards

[Specify coding standards and best practices]

- **Code Style:** [e.g., Follow PEP 8 for Python]
- **Documentation:** [e.g., Use docstrings for all functions and classes]
- **Type Hints:** [e.g., Use type hints for all function signatures]
- **Comments:** [When and how to add comments]

## Testing Requirements

[Specify testing approach]

- **Unit Tests:** [What should be unit tested]
- **Integration Tests:** [How to test agent interactions]
- **Test Coverage:** [Minimum coverage requirements if any]

# Constraints and Restrictions

## What NOT to Use

[Specify technologies, libraries, or approaches that should NOT be used]

- [Restriction 1: e.g., Do NOT use OCR libraries like pytesseract]
- [Restriction 2: e.g., Do NOT use hardcoded API keys]
- [Restriction 3: e.g., Do NOT use synchronous blocking calls in async contexts]

## What to Avoid

[Specify practices to avoid]

- [Avoidance 1: e.g., Avoid tight coupling between agents]
- [Avoidance 2: e.g., Avoid global state mutations]
- [Avoidance 3: e.g., Avoid blocking operations in workflow]

# Environment Setup

## Environment Variables

[Specify required environment variables]

**Required Variables:**
- `[VAR_NAME]`: [Description, e.g., GROQ_API_KEY - API key for Groq service]

**Optional Variables:**
- `[VAR_NAME]`: [Description and default value if applicable]

**Configuration File:**
- [How to set up .env file, e.g., Copy .env.example to .env and fill in values]

## Dependencies Installation

[Specify how to install dependencies]

```bash
[Command to install dependencies, e.g., pip install -r requirements.txt]
```

## Development Environment

[Specify development environment setup]

- **Virtual Environment:** [How to set up virtual environment]
- **IDE Recommendations:** [Recommended IDEs or editors]
- **Extensions/Plugins:** [Recommended IDE extensions]

# Output Requirements

## Output Format

[Specify output format and location]

- **Output Directory:** [Where outputs should be saved]
- **Output Format:** [Format of outputs, e.g., JSON, HTML, files, etc.]
- **Naming Convention:** [How to name output files]

## File Organization

[Specify how output files should be organized]

- [Organization rule 1]
- [Organization rule 2]

# Performance Considerations

## Optimization Guidelines

[Specify performance optimization requirements]

- [Guideline 1: e.g., Minimize API calls where possible]
- [Guideline 2: e.g., Use caching for expensive operations]
- [Guideline 3: e.g., Optimize image processing operations]

## Resource Limits

[Specify resource constraints]

- **Memory:** [Memory constraints if any]
- **Execution Time:** [Timeout requirements]
- **API Rate Limits:** [Rate limit considerations]

# Security Guidelines

## Security Best Practices

[Specify security requirements]

- [Practice 1: e.g., Never commit API keys to version control]
- [Practice 2: e.g., Use environment variables for sensitive data]
- [Practice 3: e.g., Validate all user inputs]

## Data Handling

[Specify how to handle sensitive data]

- [Guideline 1: e.g., Don't log sensitive information]
- [Guideline 2: e.g., Clean up temporary files containing sensitive data]

# Additional Notes

[Any other important implementation notes, special considerations, or guidelines]

- [Note 1]
- [Note 2]
- [Note 3]
