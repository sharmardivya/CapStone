# Goal

[Define the overall objective. What agents, tools, and workflow are needed to solve this problem?]

> **Note:** This document focuses on the **WHAT** (agents, responsibilities, workflow) and **HOW** (architecture, interactions). For implementation guidelines, technology stack, and coding standards, refer to **General_Instructions.md**.

# System Architecture Overview

[Provide a high-level overview of the agentic system architecture. How do agents interact? What is the overall flow?]

**Architecture Pattern:** [e.g., Sequential pipeline, Hierarchical, Parallel processing, etc.]
**State Management:** [How is state shared between agents? e.g., Shared state object, message passing, etc.]
**Orchestration:** [How are agents coordinated? e.g., Workflow engine, orchestrator agent, etc.]

# Agents

## [AgentName1]

### Goal

[What is the specific goal of this agent? What problem does it solve?]

### Responsibilities

* [Responsibility 1: What is this agent responsible for?]
* [Responsibility 2: Another key responsibility]
* [Responsibility 3: Additional responsibilities as needed]

### Input (if applicable)

[Describe what input this agent expects, if any. Include format, data types, structure, and any required fields.]

**Format:** [e.g., JSON object, image file, string, array, etc.]
**Source:** [Where does the input come from? e.g., User input, previous agent, shared state, etc.]
**Required Fields:** [List required fields/parameters]
**Optional Fields:** [List optional fields/parameters if any]
**Validation:** [What validation is performed on the input?]
**Example:**
```
[Provide an example of the expected input format]
```

### Output (if applicable)

[Describe what output this agent produces, if any. Include format, data types, structure, and what information is returned.]

**Format:** [e.g., JSON object, image file, string, array, etc.]
**Destination:** [Where does the output go? e.g., Next agent, shared state, user, etc.]
**Fields:** [List output fields/parameters]
**Validation:** [What validation is performed on the output?]
**Example:**
```
[Provide an example of the expected output format]
```

### Dependencies

[What does this agent depend on? Which agents must run before this one? What data must be available?]

**Prerequisites:**
- [Prerequisite 1: e.g., Agent X must complete successfully]
- [Prerequisite 2: e.g., Data field Y must be present in state]

**Dependent Agents:** [List agents that depend on this agent's output]

### Tools

* [Tool 1: What tools, libraries, or technologies does this agent use?]
* [Tool 2: Additional tools or specifications]
* [Tool 3: More tool details if needed]

**Tool Configuration:**
- [Configuration details if needed, e.g., API keys, model names, parameters]

### Preconditions

[What conditions must be true before this agent can execute?]

- [Precondition 1: e.g., Input data must be validated]
- [Precondition 2: e.g., Required resources must be available]

### Postconditions

[What conditions will be true after this agent completes successfully?]

- [Postcondition 1: e.g., Output data will be in shared state]
- [Postcondition 2: e.g., Specific flags will be set]

### Error Handling

[How does this agent handle errors? What exceptions can occur?]

**Possible Errors:**
- [Error 1: Description and handling strategy]
- [Error 2: Description and handling strategy]

**Error Recovery:**
- [Recovery strategy 1: e.g., Retry logic, fallback behavior]
- [Recovery strategy 2: e.g., Error propagation, graceful degradation]

**Error Output:**
- [How are errors communicated? e.g., Error messages in state, exceptions, etc.]

### Retry Logic (if applicable)

[Does this agent retry on failure? If so, under what conditions?]

- **Max Retries:** [Maximum number of retry attempts]
- **Retry Conditions:** [When should retries occur?]
- **Backoff Strategy:** [How are retries spaced? e.g., exponential backoff]

### Performance Considerations

[Any performance-related constraints or optimizations for this agent?]

- **Expected Execution Time:** [Typical time for this agent to complete]
- **Timeout:** [Maximum time before timeout]
- **Resource Usage:** [CPU, memory, API rate limits, etc.]

### Side Effects

[Does this agent modify shared state, files, or external systems?]

- [Side effect 1: Description]
- [Side effect 2: Description]

## [AgentName2]

### Goal

[What is the specific goal of this agent?]

### Responsibilities

* [Responsibility 1: What is this agent responsible for?]
* [Responsibility 2: Another key responsibility]
* [Responsibility 3: Additional responsibilities as needed]

### Input (if applicable)

[Describe what input this agent expects, if any. Include format, data types, structure, and any required fields.]

**Format:** [e.g., JSON object, image file, string, array, etc.]
**Source:** [Where does the input come from? e.g., User input, previous agent, shared state, etc.]
**Required Fields:** [List required fields/parameters]
**Optional Fields:** [List optional fields/parameters if any]
**Validation:** [What validation is performed on the input?]
**Example:**
```
[Provide an example of the expected input format]
```

### Output (if applicable)

[Describe what output this agent produces, if any. Include format, data types, structure, and what information is returned.]

**Format:** [e.g., JSON object, image file, string, array, etc.]
**Destination:** [Where does the output go? e.g., Next agent, shared state, user, etc.]
**Fields:** [List output fields/parameters]
**Validation:** [What validation is performed on the output?]
**Example:**
```
[Provide an example of the expected output format]
```

### Dependencies

[What does this agent depend on? Which agents must run before this one? What data must be available?]

**Prerequisites:**
- [Prerequisite 1: e.g., Agent X must complete successfully]
- [Prerequisite 2: e.g., Data field Y must be present in state]

**Dependent Agents:** [List agents that depend on this agent's output]

### Tools

* [Tool 1: What tools, libraries, or technologies does this agent use?]
* [Tool 2: Additional tools or specifications]
* [Tool 3: More tool details if needed]

**Tool Configuration:**
- [Configuration details if needed, e.g., API keys, model names, parameters]

### Preconditions

[What conditions must be true before this agent can execute?]

- [Precondition 1: e.g., Input data must be validated]
- [Precondition 2: e.g., Required resources must be available]

### Postconditions

[What conditions will be true after this agent completes successfully?]

- [Postcondition 1: e.g., Output data will be in shared state]
- [Postcondition 2: e.g., Specific flags will be set]

### Error Handling

[How does this agent handle errors? What exceptions can occur?]

**Possible Errors:**
- [Error 1: Description and handling strategy]
- [Error 2: Description and handling strategy]

**Error Recovery:**
- [Recovery strategy 1: e.g., Retry logic, fallback behavior]
- [Recovery strategy 2: e.g., Error propagation, graceful degradation]

**Error Output:**
- [How are errors communicated? e.g., Error messages in state, exceptions, etc.]

### Retry Logic (if applicable)

[Does this agent retry on failure? If so, under what conditions?]

- **Max Retries:** [Maximum number of retry attempts]
- **Retry Conditions:** [When should retries occur?]
- **Backoff Strategy:** [How are retries spaced? e.g., exponential backoff]

### Performance Considerations

[Any performance-related constraints or optimizations for this agent?]

- **Expected Execution Time:** [Typical time for this agent to complete]
- **Timeout:** [Maximum time before timeout]
- **Resource Usage:** [CPU, memory, API rate limits, etc.]

### Side Effects

[Does this agent modify shared state, files, or external systems?]

- [Side effect 1: Description]
- [Side effect 2: Description]

[Add more agents as needed following the same structure]

# Workflow/Orchestration

[Describe how agents are orchestrated. What is the execution flow?]

## Workflow Diagram

[Provide a visual or textual representation of the workflow. Show agent execution order, conditional branches, and data flow.]

```
[Example workflow representation:
Entry Point → Agent1 → [Condition] → Agent2 → Agent3 → End
                      ↓ (if condition fails)
                   Error Handler → End
]

```

## Execution Flow

1. **[Step 1]:** [Description of first step in workflow]
   - **Agent:** [Which agent executes?]
   - **Condition:** [Any conditions for this step?]
   - **Next Step:** [What happens next?]

2. **[Step 2]:** [Description of next step]
   - **Agent:** [Which agent executes?]
   - **Condition:** [Any conditions for this step?]
   - **Next Step:** [What happens next?]

[Continue for all workflow steps]

## Conditional Logic

[Describe any conditional branches in the workflow. When does the flow diverge?]

- **[Condition 1]:** [Description] → [Path A] or [Path B]
- **[Condition 2]:** [Description] → [Path A] or [Path B]

## Parallel Execution (if applicable)

[If agents can run in parallel, describe which agents and under what conditions]

- **Parallel Group 1:** [List agents that can run in parallel]
- **Parallel Group 2:** [List agents that can run in parallel]

# State Management

[Describe how state is managed across agents. What data structure is used?]

## State Structure

[Describe the shared state object/data structure]

**State Fields:**
- `[field1]`: [Type] - [Description]
- `[field2]`: [Type] - [Description]
- `[field3]`: [Type] - [Description]

## State Flow

[How does state flow between agents? Which agents read/write which fields?]

- **[Agent1]** reads: `[field1]`, writes: `[field2]`
- **[Agent2]** reads: `[field2]`, writes: `[field3]`

## State Validation

[How is state validated at different stages?]

- [Validation point 1: When and what is validated?]
- [Validation point 2: When and what is validated?]

# Error Handling Strategy

[Describe the overall error handling strategy for the system]

## Error Propagation

[How are errors propagated through the system?]

- [Error propagation mechanism 1]
- [Error propagation mechanism 2]

## Global Error Handler

[Is there a global error handler? What does it do?]

- [Global error handling strategy]

## Recovery Mechanisms

[What recovery mechanisms exist at the system level?]

- [Recovery mechanism 1]
- [Recovery mechanism 2]

# Testing Considerations

[Guidance on testing the agentic system]

## Unit Testing

[What should be unit tested for each agent?]

- [Testing consideration 1]
- [Testing consideration 2]

## Integration Testing

[How should agents be tested together?]

- [Integration testing approach 1]
- [Integration testing approach 2]

## End-to-End Testing

[How should the complete workflow be tested?]

- [E2E testing scenario 1]
- [E2E testing scenario 2]
