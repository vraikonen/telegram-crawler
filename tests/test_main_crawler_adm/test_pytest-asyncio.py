import pytest
import asyncio

# The function we want to test
async def async_add_numbers(a, b):
    await asyncio.sleep(2)  # Simulate an asynchronous operation
    return a + b

# The test function
@pytest.mark.asyncio
async def test_async_add_numbers():
    result = await async_add_numbers(2, 3)
    assert result == 5

    result = await async_add_numbers(10, -5)
    assert result == 5

    result = await async_add_numbers(0, 0)
    assert result == 0

    result = await async_add_numbers(-1, -1)
    assert result == -2