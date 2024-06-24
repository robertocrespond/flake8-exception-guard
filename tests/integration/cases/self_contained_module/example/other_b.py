from .other_a import raises_io_error
from .other_c import raise_attribute_error


def raises_io_error_indirectly():
    return raises_io_error()


def raises_io_error_and_attribute_error_indirectly():
    raise_attribute_error()
    return raises_io_error()
