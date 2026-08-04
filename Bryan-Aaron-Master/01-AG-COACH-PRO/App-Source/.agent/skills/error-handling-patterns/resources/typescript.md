### TypeScript/JavaScript Error Handling

**Custom Error Classes:**

```typescript
// Custom error classes
class ApplicationError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500,
    public details?: Record<string, any>,
  ) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace(this, this.constructor);
  }
}

class ValidationError extends ApplicationError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, "VALIDATION_ERROR", 400, details);
  }
}

class NotFoundError extends ApplicationError {
  constructor(resource: string, id: string) {
    super(`${resource} not found`, "NOT_FOUND", 404, { resource, id });
  }
}

// Usage
function getUser(id: string): User {
  const user = users.find((u) => u.id === id);
  if (!user) {
    throw new NotFoundError("User", id);
  }
  return user;
}
```

**Result Type Pattern:**

```typescript
// Result type for explicit error handling
type Result<T, E = Error> = { ok: true; value: T } | { ok: false; error: E };

// Helper functions
function Ok<T>(value: T): Result<T, never> {
  return { ok: true, value };
}

function Err<E>(error: E): Result<never, E> {
  return { ok: false, error };
}

// Usage
function parseJSON<T>(json: string): Result<T, SyntaxError> {
  try {
    const value = JSON.parse(json) as T;
    return Ok(value);
  } catch (error) {
    return Err(error as SyntaxError);
  }
}

// Consuming Result
const result = parseJSON<User>(userJson);
if (result.ok) {
  console.log(result.value.name);
} else {
  console.error("Parse failed:", result.error.message);
}

// Chaining Results
function chain<T, U, E>(
  result: Result<T, E>,
  fn: (value: T) => Result<U, E>,
): Result<U, E> {
  return result.ok ? fn(result.value) : result;
}
```

**Async Error Handling:**

```typescript
// Async/await with proper error handling
async function fetchUserOrders(userId: string): Promise<Order[]> {
  try {
    const user = await getUser(userId);
    const orders = await getOrders(user.id);
    return orders;
  } catch (error) {
    if (error instanceof NotFoundError) {
      return []; // Return empty array for not found
    }
    if (error instanceof NetworkError) {
      // Retry logic
      return retryFetchOrders(userId);
    }
    // Re-throw unexpected errors
    throw error;
  }
}

// Promise error handling
function fetchData(url: string): Promise<Data> {
  return fetch(url)
    .then((response) => {
      if (!response.ok) {
        throw new NetworkError(`HTTP ${response.status}`);
      }
      return response.json();
    })
    .catch((error) => {
      console.error("Fetch failed:", error);
      throw error;
    });
}
```
