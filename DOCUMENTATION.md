# Documentation Sources for Chart Service Implementation

## Core Python Libraries

### Pandas Documentation
- **Official Docs**: https://pandas.pydata.org/docs/
- **Key Sections**:
  - DataFrame operations: https://pandas.pydata.org/docs/reference/frame.html
  - Groupby operations: https://pandas.pydata.org/docs/user_guide/groupby.html
  - Time series: https://pandas.pydata.org/docs/user_guide/timeseries.html
  - Data types: https://pandas.pydata.org/docs/user_guide/basics.html#dtypes

### NumPy Documentation
- **Official Docs**: https://numpy.org/doc/stable/
- **Key Sections**:
  - Data types: https://numpy.org/doc/stable/user/basics.types.html
  - Array scalars: https://numpy.org/doc/stable/reference/arrays.scalars.html

## Design Patterns & Architecture

### Pipeline Pattern
- **Martin Fowler's Enterprise Patterns**: https://martinfowler.com/articles/collection-pipeline/
- **Python Implementation**: https://github.com/ericmjl/pypeline

### Service Layer Pattern
- **Fowler's PoEAA**: https://martinfowler.com/eaaCatalog/serviceLayer.html
- **Clean Architecture**: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html

### Strategy Pattern
- **Gang of Four**: https://refactoring.guru/design-patterns/strategy
- **Python Implementation**: https://refactoring.guru/design-patterns/strategy/python/example

### Repository Pattern
- **Martin Fowler**: https://martinfowler.com/eaaCatalog/repository.html
- **Python Example**: https://github.com/cosmicpython/book

## Python Type Hints & Data Models

### Pydantic Documentation
- **Official Docs**: https://docs.pydantic.dev/latest/
- **Models**: https://docs.pydantic.dev/latest/concepts/models/
- **Validation**: https://docs.pydantic.dev/latest/concepts/validators/

### Python Type Hints
- **Official Typing Module**: https://docs.python.org/3/library/typing.html
- **PEP 484**: https://peps.python.org/pep-0484/
- **mypy Documentation**: https://mypy.readthedocs.io/

## Error Handling & Logging

### Python Exception Handling
- **Official Docs**: https://docs.python.org/3/tutorial/errors.html
- **Best Practices**: https://realpython.com/python-exceptions/

### Python Logging
- **Official Docs**: https://docs.python.org/3/library/logging.html
- **Logging Cookbook**: https://docs.python.org/3/howto/logging-cookbook.html

## Async Programming

### Python Asyncio
- **Official Docs**: https://docs.python.org/3/library/asyncio.html
- **Real Python Guide**: https://realpython.com/async-io-python/

## Data Processing Concepts

### Time Series Processing
- **Pandas Time Series**: https://pandas.pydata.org/docs/user_guide/timeseries.html
- **Period Objects**: https://pandas.pydata.org/docs/reference/arrays.html#period

### Data Aggregation
- **Pandas Groupby**: https://pandas.pydata.org/docs/user_guide/groupby.html
- **SQL to Pandas**: https://pandas.pydata.org/docs/getting_started/comparison/comparison_with_sql.html

## Testing & Quality

### Pytest Documentation
- **Official Docs**: https://docs.pytest.org/
- **Fixtures**: https://docs.pytest.org/en/latest/explanation/fixtures.html
- **Parametrize**: https://docs.pytest.org/en/latest/how-to/parametrize.html

### Python Testing Best Practices
- **Real Python**: https://realpython.com/python-testing/
- **Test Driven Development**: https://testdriven.io/test-driven-development/

## Performance & Optimization

### Pandas Performance
- **Enhancing Performance**: https://pandas.pydata.org/docs/user_guide/enhancingperf.html
- **Large Datasets**: https://pandas.pydata.org/docs/user_guide/scale.html

### Memory Management
- **Python Memory Management**: https://realpython.com/python-memory-management/

## Specific Techniques Used in Your Code

### Defensive Programming
```python
# Example from your code
df['units_sold'] = pd.to_numeric(df['units_sold'], errors='coerce')
```
- **Resources**: 
  - https://en.wikipedia.org/wiki/Defensive_programming
  - https://realpython.com/python-debugging-pdb/

### Method Chaining & Fluent Interface
```python
# Example pattern
df.groupby(group_cols)[chart_spec.y].agg(agg_func).reset_index()
```
- **Resources**:
  - https://pandas.pydata.org/docs/user_guide/style.html#method-chaining
  - https://en.wikipedia.org/wiki/Fluent_interface

### Tuple Unpacking for Multiple Returns
```python
# Your pattern
df, transformations = self._apply_filters(df, chart_spec.filters)
```
- **Resources**:
  - https://docs.python.org/3/tutorial/datastructures.html#tuples-and-sequences
  - https://realpython.com/python-return-statement/#returning-multiple-values

## Books & Comprehensive Resources

### Essential Books
1. **"Effective Python" by Brett Slatkin**
   - Items on defensive programming, type hints, and performance

2. **"Python Tricks" by Dan Bader**
   - Clean code practices and Pythonic patterns

3. **"Architecture Patterns with Python" by Harry Percival & Bob Gregory**
   - Service layers, repository pattern, clean architecture

4. **"Clean Code" by Robert Martin**
   - General programming principles used throughout your code

### Online Courses & Tutorials

#### Data Processing with Pandas
- **Kaggle Learn**: https://www.kaggle.com/learn/pandas
- **DataCamp Pandas Course**: https://www.datacamp.com/courses/data-manipulation-with-pandas

#### Python Design Patterns
- **Real Python**: https://realpython.com/python-design-patterns/
- **Python Design Patterns Course**: https://python-patterns.guide/

## Advanced Topics Documentation

### JSON Serialization
- **Python JSON**: https://docs.python.org/3/library/json.html
- **Pydantic JSON**: https://docs.pydantic.dev/latest/concepts/json/

### Data Validation
- **Cerberus**: https://docs.python-cerberus.org/
- **Marshmallow**: https://marshmallow.readthedocs.io/

### Configuration Management
- **Python ConfigParser**: https://docs.python.org/3/library/configparser.html
- **Pydantic Settings**: https://docs.pydantic.dev/latest/concepts/pydantic_settings/

## Specific Code Patterns in Your Implementation

### 1. Pipeline Pattern Implementation
```python
# Your pipeline steps
df = dataframe.copy()
df, time_transformations = self._extract_month_from_date(df)
df, calc_transformations = self._calculate_revenue_if_possible(df)
df, filter_transformations = self._apply_filters(df, chart_spec.filters)
```
**Study**: https://martinfowler.com/articles/collection-pipeline/

### 2. Error Handling with Fallbacks
```python
try:
    # Main operation
    pass
except Exception as e:
    logger.error(f"Operation failed: {str(e)}")
    # Fallback behavior
```
**Study**: https://realpython.com/python-exceptions/

### 3. Type-Safe Data Transformation
```python
def _format_value_for_json(self, value: Any) -> Any:
    if pd.isna(value):
        return None
    elif isinstance(value, (np.integer, np.int64)):
        return int(value)
```
**Study**: https://docs.pydantic.dev/latest/concepts/types/

### 4. Builder Pattern for Complex Objects
```python
return ChartData(
    chart_spec=chart_spec,
    data=chart_data,
    summary_stats=summary_stats,
    data_transformations=transformations
)
```
**Study**: https://refactoring.guru/design-patterns/builder

## Tools for Code Quality

### Static Analysis
- **mypy**: https://mypy.readthedocs.io/
- **pylint**: https://pylint.pycqa.org/
- **black**: https://black.readthedocs.io/

### Documentation Tools
- **Sphinx**: https://www.sphinx-doc.org/
- **pydocstyle**: http://www.pydocstyle.org/

This comprehensive list covers all the concepts, patterns, and techniques used in your chart service implementation. Each resource will help you understand not just the "how" but also the "why" behind the implementation choices.