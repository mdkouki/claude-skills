# Falcon — Test Patterns & Mocking Idioms

Advanced patterns per language. Read this when you need guidance on mocking strategy,
async testing, time control, or complex test scenarios.

---

## General Patterns

### What to always mock
| Dependency type | Why mock it |
|----------------|-------------|
| HTTP / network calls | Flaky, slow, side-effectful |
| Database queries | Slow, requires setup/teardown |
| File system reads/writes | Environment-dependent |
| Time (`Date.now()`, `datetime.now()`) | Non-deterministic |
| Random number generators | Non-deterministic |
| Email / SMS / push notifications | Real side effects |
| External queues / event buses | Environment-dependent |

### What NOT to mock
- Pure functions with no I/O
- Value objects / DTOs
- Language standard library math/string utilities
- Your own internal domain logic (test it directly)

---

## Async / Promise Testing

### JavaScript (Jest/Vitest)
```typescript
// Async functions — use async/await
it('should resolve with user data', async () => {
  mockApi.getUser.mockResolvedValue({ id: 1, name: 'Alice' });
  const result = await userService.fetchUser(1);
  expect(result.name).toBe('Alice');
});

// Rejected promises
it('should throw on network error', async () => {
  mockApi.getUser.mockRejectedValue(new Error('Network error'));
  await expect(userService.fetchUser(1)).rejects.toThrow('Network error');
});

// Callbacks (wrap in Promise)
it('should call callback with result', (done) => {
  legacyService.getData((err, result) => {
    expect(err).toBeNull();
    expect(result).toBe('data');
    done();
  });
});
```

### Python (pytest-asyncio)
```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_fetch_user_returns_expected():
    mock_client = AsyncMock()
    mock_client.get.return_value = {"id": 1, "name": "Alice"}
    service = UserService(client=mock_client)

    result = await service.fetch_user(1)

    assert result["name"] == "Alice"
    mock_client.get.assert_awaited_once_with("/users/1")
```

### Go
```go
func TestMyHandler_ReturnsExpected(t *testing.T) {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    result, err := myHandler.Process(ctx, input)
    assert.NoError(t, err)
    assert.Equal(t, expected, result)
}
```

---

## Time Control

### JavaScript (Jest)
```typescript
beforeEach(() => {
  jest.useFakeTimers();
  jest.setSystemTime(new Date('2024-01-15T10:00:00Z'));
});

afterEach(() => {
  jest.useRealTimers();
});

it('should expire token after 1 hour', () => {
  const token = tokenService.generate();
  jest.advanceTimersByTime(3_600_001); // 1hr + 1ms
  expect(tokenService.isValid(token)).toBe(false);
});
```

### Python
```python
from unittest.mock import patch
from datetime import datetime

def test_token_expired_after_one_hour():
    with patch('mymodule.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2024, 1, 15, 10, 0, 0)
        token = token_service.generate()

        mock_dt.now.return_value = datetime(2024, 1, 15, 11, 0, 1)
        assert not token_service.is_valid(token)
```

### Java
```java
@Test
void shouldExpireToken_afterOneHour() {
    Clock fixedClock = Clock.fixed(Instant.parse("2024-01-15T10:00:00Z"), ZoneOffset.UTC);
    TokenService sut = new TokenService(fixedClock);
    String token = sut.generate();

    Clock oneHourLater = Clock.offset(fixedClock, Duration.ofHours(1).plusMillis(1));
    TokenService laterSut = new TokenService(oneHourLater);
    assertFalse(laterSut.isValid(token));
}
```

---

## HTTP / API Mocking

### JavaScript — MSW (Mock Service Worker) or jest.fn()
```typescript
// Unit level (mock the client directly)
const mockAxios = { get: jest.fn() };
mockAxios.get.mockResolvedValue({ data: { id: 1 } });
```

### Python — responses library or unittest.mock
```python
import responses

@responses.activate
def test_api_call():
    responses.add(responses.GET, 'https://api.example.com/users/1',
                  json={'id': 1, 'name': 'Alice'}, status=200)

    result = client.get_user(1)
    assert result['name'] == 'Alice'
```

### Go — httptest
```go
func TestAPIClient_GetUser(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
        json.NewEncoder(w).Encode(map[string]any{"id": 1, "name": "Alice"})
    }))
    defer server.Close()

    client := NewAPIClient(server.URL)
    user, err := client.GetUser(1)
    assert.NoError(t, err)
    assert.Equal(t, "Alice", user.Name)
}
```

---

## Database Mocking

### Prefer: inject a repository interface, mock the interface
Never spin up a real DB in a unit test. If you see real DB calls, mock at the repository layer.

```typescript
// TypeScript — mock the repo interface
const mockUserRepo: jest.Mocked<UserRepository> = {
  findById: jest.fn(),
  save: jest.fn(),
  delete: jest.fn(),
};
mockUserRepo.findById.mockResolvedValue({ id: 1, name: 'Alice' });

const service = new UserService(mockUserRepo);
```

```python
# Python — mock the repo
mock_repo = MagicMock(spec=UserRepository)
mock_repo.find_by_id.return_value = User(id=1, name="Alice")
service = UserService(repo=mock_repo)
```

---

## State Machine / Multi-step Flows

When testing methods with multiple state transitions, test each transition independently:

```typescript
describe('OrderStateMachine', () => {
  it('should transition from PENDING to CONFIRMED on confirm()', () => { ... });
  it('should transition from CONFIRMED to SHIPPED on ship()', () => { ... });
  it('should throw when calling ship() on PENDING order', () => { ... });
  it('should transition from any state to CANCELLED on cancel()', () => { ... });
});
```

---

## Error / Exception Coverage Checklist

For every function that can fail, cover:

- [ ] Expected error type is thrown (not just `Error`)
- [ ] Error message contains useful context
- [ ] Error is NOT thrown on valid input (verify the happy path still passes)
- [ ] Partial failure: what happens if only one of multiple operations fails?

---

## Naming Conventions Cheat Sheet

| Language | Test file name | Test function name |
|----------|---------------|-------------------|
| Python | `test_<module>.py` | `test_<action>_<scenario>` |
| JS/TS | `<module>.test.ts` or `<module>.spec.ts` | `it('should <expectation> when <condition>')` |
| Java | `<Class>Test.java` | `should<Expectation>_when<Condition>()` |
| C# | `<Class>Tests.cs` | `MethodName_Scenario_ExpectedBehavior()` |
| Go | `<file>_test.go` | `TestFunctionName_Scenario_Expected` |
| Ruby | `<module>_spec.rb` | `'<description>'` (RSpec DSL) |
| Swift | `<Module>Tests.swift` | `test_<method>_<scenario>_<expectation>` |
| Rust | same file | `fn <method>_<expectation>_when_<condition>` |
| PHP | `<Class>Test.php` | `test_<method>_with<Scenario>_<expectation>()` |

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Fix |
|---|---|---|
| Testing private methods directly | Brittle, couples to impl | Test via public API |
| Multiple unrelated asserts in one test | Hard to diagnose failures | Split into separate tests |
| Shared mutable state between tests | Order-dependent, flaky | Reset in `beforeEach` |
| Real HTTP/DB in unit tests | Slow, flaky, side-effectful | Mock at boundary |
| Magic numbers (`expect(result).toBe(42)`) | Unclear intent | Name constants |
| Testing framework internals | Tests what you didn't write | Only test your code |
| Ignoring error paths | Misses bugs | Always test error cases |
| Test names like `test1()` or `myTest()` | Impossible to diagnose failures | Use descriptive names |
