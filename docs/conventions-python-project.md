# Python Coding Conventions and Best Practices

## Tools

- Use `uv` for package management
- Use `ruff` as the code formatter and linter
- Use `pytest` for testing

## Code Layout and Formatting

### Indentation and Line Length
- Use 4 spaces for indentation (never tabs)
- Limit all lines to a maximum of 79 characters for code
- Limit docstrings/comments to 72 characters
- Use line breaks between logical sections of code

### Imports
- Imports should be on separate lines
- Order imports in three groups, separated by a blank line:
    1. Standard library imports
    2. Third-party library imports
    3. Local application imports
- Use absolute imports over relative imports
- Avoid wildcard imports (`from module import *`)

```python
# Good
import os
import sys

import numpy as np
import pandas as pd

from mypackage import mymodule
```

## Naming Conventions

### General Rules
- Names should be descriptive and meaningful
- Avoid single-letter names except for counters or iterators
- Use English names for all identifiers

### Specific Conventions
- Functions: lowercase with underscores (`calculate_total`)
- Variables: lowercase with underscores (`user_input`)
- Classes: CapWords convention (`CustomerOrder`)
- Constants: uppercase with underscores (`MAX_CONNECTIONS`)
- Protected instance attributes: single leading underscore (`_internal_value`)
- Private instance attributes: double leading underscore (`__private_method`)
- Module names: short, lowercase (`util.py`)

## Function and Method Guidelines

### Function Design
- Functions should do one thing well
- Keep functions short and focused (typically under 20 lines)
- Use descriptive names that indicate what the function does
- Include type hints for parameters and return values

```python
def calculate_average(numbers: list[float]) -> float:
    """Calculate the average of a list of numbers."""
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)
```

### Documentation
- Use docstrings for all public modules, functions, classes, and methods
- Follow Google-style docstring format
- Include:
    - Brief description
    - Args/Parameters
    - Returns
    - Raises (if applicable)
    - Examples (when helpful)

## Class Guidelines

### Class Structure
- Use class attributes for class-wide constants
- Define `__init__` method first
- Group methods by functionality
- Use properties instead of getter/setter methods
- Implement special methods as needed (`__str__`, `__repr__`, etc.)

```python
from pydantic import BaseModel

class Person(BaseModel):
    """Represents a person with basic attributes."""
    
    name: str
    age: int

    def __str__(self) -> str:
        return f"{self.name} ({self.age})"
```

## Using Pydantic for Data Validation

Pydantic is a library for data validation and settings management using Python type annotations. It provides a way to define data models with built-in validation.

#### Benefits of Pydantic
- Automatic data validation and parsing
- Type-safe data models
- Easy integration with FastAPI and other frameworks

#### Example Usage

```python
from pydantic import BaseModel, ValidationError

class User(BaseModel):
    username: str
    email: str
    age: int

try:
    user = User(username='john_doe', email='john@example.com', age='25')
except ValidationError as e:
    print(e.json())
```

#### Integration with Existing Code

- Replace traditional class definitions with Pydantic models for data validation.
- Use Pydantic's `BaseModel` to define data structures with type annotations.
- Leverage Pydantic's validation features to ensure data integrity.

## Error Handling

### Best Practices
- Use try/except/finally blocks to handle specific exceptions
- Avoid bare except clauses
- Use context managers (with statements) when applicable
- Raise exceptions early, handle them late
- Create custom ecxeption classes
- Include error messages that are helpful for debugging

```python
def read_config(filename: str) -> dict:
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file '{filename}' not found")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")
```

## Testing

### Testing Guidelines
- Write tests for all new code
- Use pytest as the testing framework
- Follow the Arrange-Act-Assert pattern
- Test both success and failure cases
- Use meaningful test names that describe the scenario

```python
def test_calculate_average_with_valid_input():
    # Arrange
    numbers = [1, 2, 3, 4, 5]
    
    # Act
    result = calculate_average(numbers)
    
    # Assert
    assert result == 3.0
```

## Performance Considerations

### Optimization Guidelines
- Write for clarity first, optimize later if needed
- Use appropriate data structures (lists vs. sets vs. dictionaries)
- Avoid premature optimization
- Profile code before optimizing
- Use generator expressions for large datasets
- Consider using built-in functions and standard library tools

## Version Control

### Git Best Practices
- Write clear, descriptive commit messages
- Make small, focused commits
- Use feature branches for new development
- Keep the main/master branch stable
- Review code before merging

## Separation of Concerns

### Principles
- **Modularity**: Break down the code into distinct modules or components, each responsible for a specific part of the functionality.
- **Encapsulation**: Each module should encapsulate its data and behavior, exposing only what is necessary through well-defined interfaces.
- **Single Responsibility Principle**: Each class or function should have one reason to change, meaning it should only have one job or responsibility.
- **Layered Architecture**: Use a layered approach where each layer has a specific role, such as presentation, application, and data layers.
- **Use of Design Patterns**: Implement design patterns like MVC (Model-View-Controller) or MVVM (Model-View-ViewModel) to enforce separation of concerns.
- **Testing**: Separation of concerns facilitates testing by allowing you to test each part of the application independently.
- **Maintainability and Scalability**: By separating concerns, the codebase becomes easier to maintain and extend.
- Use type checking with mypy
- Format code with black
- Check style with flake8
- Sort imports with isort
- Use pylint for additional static analysis

### Detailed Instructions for Applying Separation of Concerns

1. **Identify Concerns**:
    - Start by identifying the different concerns or responsibilities in your application. Common concerns include user interface, business logic, data access, and error handling.
    - Example: In a web application, separate concerns might be handling HTTP requests, processing data, and interacting with a database.

2. **Design Modular Components**:
    - Break down your application into modules or components, each responsible for a specific concern.
    - Example: Create separate modules for user authentication, data processing, and reporting.

3. **Encapsulate Functionality**:
    - Ensure each module encapsulates its functionality and exposes only necessary interfaces. This reduces dependencies and makes the system more flexible.
    - Example: A data access module should provide methods to query and update the database but hide the underlying database connection details.

4. **Apply the Single Responsibility Principle**:
    - Design classes and functions to have a single responsibility. This makes them easier to understand, test, and maintain.
    - Example: A class `UserManager` should handle user-related operations, while a class `EmailService` should handle email sending.

5. **Use Layered Architecture**:
    - Organize your application into layers, such as presentation, business logic, and data access. Each layer should only interact with the layer directly below it.
    - Example: In a three-tier architecture, the presentation layer handles user input, the business logic layer processes data, and the data access layer interacts with the database.

6. **Implement Design Patterns**:
    - Use design patterns like MVC or MVVM to enforce separation of concerns. These patterns provide a structured way to separate different aspects of the application.
    - Example: In MVC, the Model handles data, the View handles the user interface, and the Controller manages input and updates the Model.

7. **Facilitate Testing**:
    - Design your modules to be independently testable. Write unit tests for each module to ensure it functions correctly in isolation.
    - Example: Test the data processing module with various input scenarios without requiring the user interface to be complete.

8. **Plan for Maintainability and Scalability**:
    - Design your system to be easily maintainable and scalable. By separating concerns, you can modify or extend one part of the system without affecting others.
    - Example: If you need to change the database technology, only the data access module should require modification.

9. **Use Tools and Practices**:
    - Utilize tools and practices that support separation of concerns, such as dependency injection, interface segregation, and modular programming.
    - Example: Use dependency injection to decouple components and make them easier to test and replace.

### Configuration
Include a `pyproject.toml` file to maintain consistent settings across the project.
