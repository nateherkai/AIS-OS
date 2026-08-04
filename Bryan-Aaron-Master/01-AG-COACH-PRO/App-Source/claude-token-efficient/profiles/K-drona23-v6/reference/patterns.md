# Patterns

## Avoid
- Writing code before reading the test file
- Incremental coding (write partial, test, add more, test again)
- Re-reading files already read
- Over-engineering or adding features beyond test requirements
- Using pub/sub or channel patterns for WebSocket broadcast. Use manual client tracking with a Set instead

## Do
- Read test file first to understand success criteria
- Write complete solution in one pass
- Use relative paths
- Handle edge cases: nulls, empty strings, type mismatches
- For WebSocket: track clients in a Set, send to sender first, broadcast to others with setTimeout(0)
