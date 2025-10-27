import warnings
from functools import wraps

def deprecated(reason=None):
    """
    标记函数、方法或类为过期。
    :param reason: 过期原因和建议的替代方案。
    """
    def decorator(obj):
        is_class = isinstance(obj, type)
        message = reason or f"{obj.__name__} is deprecated."

        if is_class:
            # 如果是类，我们包装其所有直接的方法（包括类方法、静态方法和实例方法）
            class DeprecatedClass(obj):
                def __init__(self, *args, **kwargs):
                    warnings.warn(message, DeprecationWarning, stacklevel=2)
                    super().__init__(*args, **kwargs)

                # 注意：这里我们尝试包装类方法和静态方法，但可能会遇到一些边界情况。
                # 为了简单，我们只覆盖实例方法。如果需要覆盖类方法和静态方法，需要更复杂的处理。
            return DeprecatedClass

        else:
            # 如果是函数或方法
            @wraps(obj)
            def wrapper(*args, **kwargs):
                warnings.warn(message, DeprecationWarning, stacklevel=2)
                return obj(*args, **kwargs)
            return wrapper

    return decorator