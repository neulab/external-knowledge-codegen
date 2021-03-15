import warnings

from .code_gen import *  # NOQA


warnings.warn(
    'jastor.codegen module is deprecated. Please import '
    'jastor.code_gen module instead.',
    DeprecationWarning,
    stacklevel=2
)
