from .parser import Parser


def parse(s, debug=False, filepath=None):
    parser = Parser(s, filepath)
    parser.set_debug(debug)
    return parser.parse()


def parse_member_declaration(s, debug=False, filepath=None):
    parser = Parser(s, filepath)
    parser.set_debug(debug)
    return parser.parse_member_declaration()
