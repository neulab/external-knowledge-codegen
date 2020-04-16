import string
import keyword
import json
import sys


def tokenize_libs():
    all_names = []
    with open('python-docs.jsonl', encoding='utf-8') as docs_file:
        for line in docs_file:
            name = json.loads(line)['snippet']
            all_names += (name.split('(')[0].split('.'))
    return set(all_names)

def parse(tokens, lib_names):
    tags = ['NAME'] * len(tokens)
    string_stack = []
    for i, c in enumerate(tokens):
        if c == '`' and not string_stack:
            string_stack.append(i)
            tags[i] = 'PUNCT'
        elif c == '`' and string_stack:
            start = string_stack.pop()
            tags[i] = 'PUNCT'
            for idx in range(start + 1, i):
                tags[idx] = "STR"
        elif c.isnumeric():
            tags[i] = 'NUM'
        elif c in string.punctuation:
            tags[i] = 'PUNCT'
        elif keyword.iskeyword(c):
            tags[i] = 'KEYWORD'
        elif c in lib_names:
            tags[i] = 'LIB'
        else:
            tags[i]= 'NAME'
    return tags

if __name__ == '__main__':
    lib_names = tokenize_libs()
    file_path = sys.argv[1]
    with open(file_path, encoding='utf-8') as ref_file, \
        open(file_path + '.tag', 'w', encoding='utf-8') as tag_file:
        for line in ref_file:
            tokens = line.strip().split()
            tag_file.write(' '.join(parse(tokens, lib_names)) + '\n')
