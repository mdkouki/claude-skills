# Falcon — Framework Reference

Full language → test framework mapping with import boilerplate and file conventions.

---

## JavaScript / TypeScript

### Jest (most common, React/Node projects)
```typescript
// <module>.test.ts
import { myFunction } from '../src/myModule';

describe('myFunction', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return expected value when given valid input', () => {
    // Arrange
    const input = 'valid';

    // Act
    const result = myFunction(input);

    // Assert
    expect(result).toBe('expected');
  });

  it('should throw when input is null', () => {
    expect(() => myFunction(null)).toThrow(TypeError);
  });
});

// Mocking a module
jest.mock('../src/emailService');
const mockSend = jest.mocked(emailService.send);
mockSend.mockResolvedValue({ success: true });
```

Detection: `jest` in `package.json` devDependencies, or `jest.config.*` present.

### Vitest (Vite projects)
```typescript
// <module>.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { myFunction } from '../src/myModule';

describe('myFunction', () => {
  it('should return expected value', () => {
    const result = myFunction('input');
    expect(result).toBe('expected');
  });
});

// Mocking
vi.mock('../src/service', () => ({ send: vi.fn() }));
```

Detection: `vitest` in devDependencies, or `vite.config.*` present.

### Mocha + Chai
```javascript
// test/<module>.spec.js
const { expect } = require('chai');
const sinon = require('sinon');
const { myFunction } = require('../src/myModule');

describe('myFunction', () => {
  let sandbox;
  beforeEach(() => { sandbox = sinon.createSandbox(); });
  afterEach(() => sandbox.restore());

  it('should return expected value', () => {
    expect(myFunction('input')).to.equal('expected');
  });
});
```

---

## Python

### pytest (preferred)
```python
# test_<module>.py  OR  <module>_test.py
import pytest
from unittest.mock import MagicMock, patch
from src.my_module import my_function


class TestMyFunction:
    def test_returns_expected_when_valid_input(self):
        # Arrange
        input_val = "valid"

        # Act
        result = my_function(input_val)

        # Assert
        assert result == "expected"

    def test_raises_value_error_when_input_is_none(self):
        with pytest.raises(ValueError, match="Input cannot be None"):
            my_function(None)

    def test_handles_empty_string(self):
        result = my_function("")
        assert result == ""  # or whatever the contract is

    @patch("src.my_module.external_service")
    def test_calls_external_service_with_correct_args(self, mock_service):
        mock_service.send.return_value = {"status": "ok"}
        my_function("input")
        mock_service.send.assert_called_once_with("input")


# Parametrize for boundary/matrix testing
@pytest.mark.parametrize("value,expected", [
    (0, 0),
    (1, 1),
    (-1, -1),
    (None, None),
])
def test_edge_cases(value, expected):
    assert my_function(value) == expected
```

Detection: `pytest` in requirements, `pyproject.toml` with `[tool.pytest]`, or `conftest.py` present.

### unittest (built-in fallback)
```python
import unittest
from unittest.mock import patch, MagicMock

class TestMyFunction(unittest.TestCase):
    def setUp(self):
        self.fixture = "shared setup"

    def test_returns_expected(self):
        self.assertEqual(my_function("input"), "expected")

    def test_raises_on_none(self):
        with self.assertRaises(ValueError):
            my_function(None)

if __name__ == "__main__":
    unittest.main()
```

---

## Java

### JUnit 5 + Mockito (standard)
```java
// src/test/java/<package>/<ClassName>Test.java
import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.mockito.Mock;
import org.mockito.MockitoExtension;
import org.junit.jupiter.api.extension.ExtendWith;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class MyServiceTest {

    @Mock
    private ExternalRepository repository;

    private MyService sut; // system under test

    @BeforeEach
    void setUp() {
        sut = new MyService(repository);
    }

    @Test
    @DisplayName("should return user when valid ID provided")
    void shouldReturnUser_whenValidIdProvided() {
        // Arrange
        when(repository.findById(1L)).thenReturn(Optional.of(new User(1L, "Alice")));

        // Act
        User result = sut.getUser(1L);

        // Assert
        assertNotNull(result);
        assertEquals("Alice", result.getName());
        verify(repository).findById(1L);
    }

    @Test
    void shouldThrowNotFoundException_whenUserDoesNotExist() {
        when(repository.findById(99L)).thenReturn(Optional.empty());
        assertThrows(UserNotFoundException.class, () -> sut.getUser(99L));
    }

    @ParameterizedTest
    @ValueSource(longs = {-1L, 0L})
    void shouldThrowIllegalArgument_whenIdIsNotPositive(long id) {
        assertThrows(IllegalArgumentException.class, () -> sut.getUser(id));
    }
}
```

Detection: `pom.xml` or `build.gradle` with junit dependency.

---

## C# / .NET

### NUnit (common)
```csharp
// Tests/<ClassName>Tests.cs
using NUnit.Framework;
using Moq;

[TestFixture]
public class MyServiceTests
{
    private Mock<IRepository> _repositoryMock;
    private MyService _sut;

    [SetUp]
    public void SetUp()
    {
        _repositoryMock = new Mock<IRepository>();
        _sut = new MyService(_repositoryMock.Object);
    }

    [Test]
    public void GetUser_WithValidId_ReturnsUser()
    {
        // Arrange
        _repositoryMock.Setup(r => r.FindById(1)).Returns(new User { Id = 1, Name = "Alice" });

        // Act
        var result = _sut.GetUser(1);

        // Assert
        Assert.That(result, Is.Not.Null);
        Assert.That(result.Name, Is.EqualTo("Alice"));
    }

    [Test]
    public void GetUser_WithInvalidId_ThrowsNotFoundException()
    {
        _repositoryMock.Setup(r => r.FindById(It.IsAny<int>())).Returns((User)null);
        Assert.Throws<NotFoundException>(() => _sut.GetUser(99));
    }

    [TestCase(-1)]
    [TestCase(0)]
    public void GetUser_WithNonPositiveId_ThrowsArgumentException(int id)
    {
        Assert.Throws<ArgumentException>(() => _sut.GetUser(id));
    }
}
```

### xUnit
```csharp
using Xunit;
using Moq;

public class MyServiceTests
{
    private readonly Mock<IRepository> _repositoryMock = new();
    private readonly MyService _sut;

    public MyServiceTests() => _sut = new MyService(_repositoryMock.Object);

    [Fact]
    public void GetUser_WithValidId_ReturnsUser() { /* ... */ }

    [Theory]
    [InlineData(-1)]
    [InlineData(0)]
    public void GetUser_WithNonPositiveId_Throws(int id) { /* ... */ }
}
```

Detection: `*.csproj` — check for `NUnit`, `xunit`, or `MSTest.TestFramework` package references.

---

## Go

### go test + testify
```go
// <file>_test.go  (same package)
package mypackage_test

import (
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
)

func TestMyFunction_ReturnsExpected_WhenValidInput(t *testing.T) {
    // Arrange
    input := "valid"

    // Act
    result, err := MyFunction(input)

    // Assert
    assert.NoError(t, err)
    assert.Equal(t, "expected", result)
}

func TestMyFunction_ReturnsError_WhenInputIsEmpty(t *testing.T) {
    _, err := MyFunction("")
    assert.ErrorIs(t, err, ErrEmptyInput)
}

// Table-driven tests (Go idiom)
func TestMyFunction_EdgeCases(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        want    string
        wantErr bool
    }{
        {"empty string", "", "", true},
        {"single char", "a", "a", false},
        {"valid input", "hello", "hello", false},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := MyFunction(tt.input)
            if tt.wantErr {
                assert.Error(t, err)
                return
            }
            assert.NoError(t, err)
            assert.Equal(t, tt.want, got)
        })
    }
}
```

Detection: `go.mod` present.

---

## Ruby

### RSpec (preferred)
```ruby
# spec/<module>_spec.rb
require 'spec_helper'
require_relative '../lib/my_module'

RSpec.describe MyClass do
  subject(:my_object) { described_class.new(dependency: mock_dep) }

  let(:mock_dep) { instance_double(Dependency) }

  describe '#my_method' do
    context 'when given valid input' do
      before { allow(mock_dep).to receive(:call).and_return('ok') }

      it 'returns the expected result' do
        expect(my_object.my_method('valid')).to eq('expected')
      end

      it 'calls the dependency with the input' do
        my_object.my_method('valid')
        expect(mock_dep).to have_received(:call).with('valid')
      end
    end

    context 'when input is nil' do
      it 'raises ArgumentError' do
        expect { my_object.my_method(nil) }.to raise_error(ArgumentError)
      end
    end
  end
end
```

Detection: `Gemfile` with `rspec` gem, or `spec/` directory present.

---

## Swift / iOS

### XCTest
```swift
// Tests/<Module>Tests.swift
import XCTest
@testable import MyModule

final class MyServiceTests: XCTestCase {

    var sut: MyService!
    var mockRepository: MockRepository!

    override func setUp() {
        super.setUp()
        mockRepository = MockRepository()
        sut = MyService(repository: mockRepository)
    }

    override func tearDown() {
        sut = nil
        mockRepository = nil
        super.tearDown()
    }

    func test_getUser_withValidId_returnsUser() {
        // Arrange
        mockRepository.stubbedUser = User(id: 1, name: "Alice")

        // Act
        let result = sut.getUser(id: 1)

        // Assert
        XCTAssertEqual(result?.name, "Alice")
    }

    func test_getUser_withInvalidId_returnsNil() {
        mockRepository.stubbedUser = nil
        XCTAssertNil(sut.getUser(id: 99))
    }

    func test_getUser_withNegativeId_throwsError() {
        XCTAssertThrowsError(try sut.getUser(id: -1)) { error in
            XCTAssertEqual(error as? ServiceError, .invalidId)
        }
    }
}
```

Detection: `Package.swift` or `*.xcodeproj` present.

---

## Rust

### Built-in `#[test]`
```rust
// In the same file as the module (bottom), or tests/<module>.rs
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn my_function_returns_expected_when_valid_input() {
        // Arrange
        let input = "valid";

        // Act
        let result = my_function(input);

        // Assert
        assert_eq!(result, "expected");
    }

    #[test]
    fn my_function_returns_error_when_input_empty() {
        let result = my_function("");
        assert!(result.is_err());
    }

    #[test]
    #[should_panic(expected = "overflow")]
    fn my_function_panics_on_overflow() {
        my_function(usize::MAX);
    }
}
```

Detection: `Cargo.toml` present.

---

## PHP

### PHPUnit
```php
// tests/<ClassName>Test.php
use PHPUnit\Framework\TestCase;

class MyServiceTest extends TestCase
{
    private MyService $sut;
    private MockObject $repositoryMock;

    protected function setUp(): void
    {
        $this->repositoryMock = $this->createMock(Repository::class);
        $this->sut = new MyService($this->repositoryMock);
    }

    public function test_getUser_withValidId_returnsUser(): void
    {
        // Arrange
        $this->repositoryMock->method('findById')->willReturn(new User(1, 'Alice'));

        // Act
        $result = $this->sut->getUser(1);

        // Assert
        $this->assertSame('Alice', $result->getName());
    }

    public function test_getUser_withInvalidId_throwsNotFoundException(): void
    {
        $this->repositoryMock->method('findById')->willReturn(null);
        $this->expectException(NotFoundException::class);
        $this->sut->getUser(99);
    }

    /** @dataProvider invalidIdProvider */
    public function test_getUser_withNonPositiveId_throwsInvalidArgument(int $id): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->sut->getUser($id);
    }

    public static function invalidIdProvider(): array
    {
        return [[-1], [0]];
    }
}
```

Detection: `composer.json` with `phpunit/phpunit`.

---

## Kotlin

### Kotest (idiomatic Kotlin)
```kotlin
// src/test/kotlin/<package>/<ClassName>Test.kt
import io.kotest.core.spec.style.BehaviorSpec
import io.kotest.matchers.shouldBe
import io.kotest.assertions.throwables.shouldThrow
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify

class MyServiceTest : BehaviorSpec({

    val repository = mockk<Repository>()
    val sut = MyService(repository)

    given("a valid user id") {
        every { repository.findById(1L) } returns User(1L, "Alice")

        `when`("getUser is called") {
            val result = sut.getUser(1L)

            then("it should return the user") {
                result.name shouldBe "Alice"
            }

            then("it should call the repository once") {
                verify(exactly = 1) { repository.findById(1L) }
            }
        }
    }

    given("an invalid user id") {
        every { repository.findById(99L) } returns null

        `when`("getUser is called") {
            then("it should throw UserNotFoundException") {
                shouldThrow<UserNotFoundException> { sut.getUser(99L) }
            }
        }
    }
})
```

Detection: `build.gradle.kts` or `pom.xml` with Kotlin + kotest/junit5.

---

## Dart / Flutter

### flutter_test / test
```dart
// test/<module>_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:my_app/src/my_service.dart';

class MockRepository extends Mock implements Repository {}

void main() {
  late MyService sut;
  late MockRepository mockRepository;

  setUp(() {
    mockRepository = MockRepository();
    sut = MyService(repository: mockRepository);
  });

  group('MyService.getUser', () {
    test('returns user when valid ID', () {
      when(mockRepository.findById(1)).thenReturn(User(id: 1, name: 'Alice'));
      final result = sut.getUser(1);
      expect(result?.name, equals('Alice'));
    });

    test('returns null when user not found', () {
      when(mockRepository.findById(99)).thenReturn(null);
      expect(sut.getUser(99), isNull);
    });

    test('throws on invalid ID', () {
      expect(() => sut.getUser(-1), throwsArgumentError);
    });
  });
}
```

Detection: `pubspec.yaml` present.
