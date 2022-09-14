from .parser import Parser


def parse(s, debug=False):
    parser = Parser(s)
    parser.set_debug(debug)
    return parser.parse()


def parse_member_declaration(s, debug=False):
    parser = Parser(s)
    parser.set_debug(debug)
    return parser.parse_member_declaration()
