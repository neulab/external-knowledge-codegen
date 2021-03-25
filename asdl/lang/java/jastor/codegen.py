# -*- coding: utf-8 -*-
"""
Part of the jastor library for Java AST manipulation.

Jastor is a port to Java of the astor library for Python AST manipulation.

License: 3-clause BSD

For Jastor
Copyright 2021 (c) CEA LIST (Gaël de Chalendar)

"""

import warnings

from .code_gen import *  # NOQA


warnings.warn(
    'jastor.codegen module is deprecated. Please import '
    'jastor.code_gen module instead.',
    DeprecationWarning,
    stacklevel=2
)
