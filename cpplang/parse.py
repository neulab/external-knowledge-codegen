import sys

from .parser import Parser
from .tokenizer import tokenize


def parse(s):
    parser = Parser(s)
    return parser.parse()


def parse_member_declaration(s):
    tokens = tokenize(s)
    parser = Parser(tokens)
    return parser.parse_member_declaration()
