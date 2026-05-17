---
name: error-handling-patterns
description: Master error handling patterns across languages including exceptions, Result types, error propagation, and graceful degradation to build resilient applications. Use when implementing error handling, designing APIs, or improving application reliability.
---

# Error Handling Patterns

Build resilient applications with robust error handling strategies that gracefully handle failures and provide excellent debugging experiences.

## When to Use This Skill

- Implementing error handling in new features
- Designing error-resilient APIs
- Debugging production issues
- Improving application reliability
- Creating better error messages for users and developers
- Implementing retry and circuit breaker patterns
- Handling async/concurrent errors
- Building fault-tolerant distributed systems

## Core Concepts

### 1. Error Handling Philosophies

**Exceptions vs Result Types:**

- **Exceptions**: Traditional try-catch, disrupts control flow
- **Result Types**: Explicit success/failure, functional approach
- **Error Codes**: C-style, requires discipline
- **Option/Maybe Types**: For nullable values

**When to Use Each:**

- Exceptions: Unexpected errors, exceptional conditions
- Result Types: Expected errors, validation failures
- Panics/Crashes: Unrecoverable errors, programming bugs

### 2. Error Categories

**Recoverable Errors:**

- Network timeouts
- Missing files
- Invalid user input
- API rate limits

**Unrecoverable Errors:**

- Out of memory
- Stack overflow
- Programming bugs (null pointer, etc.)

## Language-Specific Patterns

### Python Error Handling
See [python.md](resources/python.md) for custom exception hierarchies, context managers, and retry decorators.

### TypeScript/JavaScript Error Handling
See [typescript.md](resources/typescript.md) for custom error classes, Result types, and async error handling patterns.

### Rust Error Handling
See [rust.md](resources/rust.md) for Result/Option types and propagation patterns.

### Go Error Handling
See [go.md](resources/go.md) for explicit error returns and wrapping.

## Universal Patterns

### Pattern 1: Circuit Breaker
Prevent cascading failures in distributed systems. See [circuit-breaker.md](resources/circuit-breaker.md).

### Pattern 2: Error Aggregation
Collect multiple errors instead of failing on first error. See [aggregation.md](resources/aggregation.md).

### Pattern 3: Graceful Degradation
Provide fallback functionality when errors occur. See [degradation.md](resources/degradation.md).

## Best Practices

1. **Fail Fast**: Validate input early, fail quickly
2. **Preserve Context**: Include stack traces, metadata, timestamps
3. **Meaningful Messages**: Explain what happened and how to fix it
4. **Log Appropriately**: Error = log, expected failure = don't spam logs
5. **Handle at Right Level**: Catch where you can meaningfully handle
6. **Clean Up Resources**: Use try-finally, context managers, defer
7. **Don't Swallow Errors**: Log or re-throw, don't silently ignore
8. **Type-Safe Errors**: Use typed errors when possible

## Common Pitfalls

- **Catching Too Broadly**: `except Exception` hides bugs
- **Empty Catch Blocks**: Silently swallowing errors
- **Logging and Re-throwing**: Creates duplicate log entries
- **Not Cleaning Up**: Forgetting to close files, connections
- **Poor Error Messages**: "Error occurred" is not helpful
- **Returning Error Codes**: Use exceptions or Result types
- **Ignoring Async Errors**: Unhandled promise rejections

## Resources

- [Exception Hierarchy Design](resources/exception-hierarchy-design.md)
- [Error Recovery Strategies](resources/error-recovery-strategies.md)
- [Async Error Handling](resources/async-error-handling.md)
- [Error Handling Checklist](resources/error-handling-checklist.md)
- [Error Message Guide](resources/error-message-guide.md)
- [Error Analyzer Script](scripts/error-analyzer.py)
