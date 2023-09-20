# from typing import Callable, Any
# import functools

# class FunctionException(Exception):
#     """Raise when the function is executed unsuccessfully \n
#     Input variables: \n
#     - func_name: name of the failed function
#     - err: the raised error"""
#
#     def __init__(self, func_name, err):
#         self.message = err
#         self.func_name = func_name
#         super().__init__(self.message)

# def with_exception_raise(func: Callable[..., Any]) -> Callable[..., Any]:
#     @functools.wraps(func)
#     def wrapper(*args: Any, **kwargs: Any) -> Any:
#         try:
#             value = func(*args, **kwargs)
#         except Exception as e:
#             raise FunctionException(func.__name__, e)
#         return value
#
#     return wrapper
