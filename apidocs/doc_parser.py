import itertools
import os
import json

import nltk
import inflection
import random
from bs4 import BeautifulSoup
from bs4 import element
random.seed(1)

def parenthetic_contents(string):
    """Generate parenthesized contents in string as pairs (level, contents)."""
    stack = []
    for i, c in enumerate(string):
        if c == '[':
            stack.append(i)
        elif c == ']' and stack:
            start = stack.pop()
            yield (len(stack), string[start + 1: i])

def get_func_signatures(nodes):
    sigs = []
    for node in nodes:
        text = ""
        for n in node.children:
            if isinstance(n, element.Tag):
                if 'property' not in n['class'] and n.name != 'a':
                    text += n.text
            elif isinstance(n, element.NavigableString):
                text += n
        sigs.append(text.strip())
    return sigs

def get_class_name(sig):
    return sig.split('(')[0].split('.')[-1]

def parse_optional_args(sig):
    if '(' in sig and ')' in sig:
        lidx = sig.find('(')
        ridx = sig.rfind(')')
        head = sig[:lidx]
        arg_str = sig[lidx + 1:ridx]
        num_posoptarags = len(list(parenthetic_contents(arg_str)))
        arg_str_list = arg_str.replace('[', '').replace(']', '').split(', ')
        pos_args = []
        kwargs = []
        all_keywords = []
        for arg in arg_str_list:
            if arg in ('*', '...'):
                continue
            elif '=' in arg:
                kwargs.append(arg)
                all_keywords.append(arg.split('=')[0])
            else:
                pos_args.append(arg)
                all_keywords.append(arg)
        pos_arg_combinations = [pos_args]
        for i in range(num_posoptarags):
            pos_arg_combinations.append(pos_args[:-i-1])
        kwargs_combinations = []
        for k in range(len(kwargs) + 1):
            kwargs_combinations += itertools.combinations(kwargs, k)
        if len(kwargs_combinations) > 10:
            # kwargs_combinations = random.sample(kwargs_combinations, k=10)
            kwargs_combinations = kwargs_combinations[:10]
        return head, [x+list(y) for x in pos_arg_combinations for y in kwargs_combinations], all_keywords
    else:
        return None, None, None

def match_doc_sents(kws, sents):
    k_s = dict.fromkeys(kws)
    toked_sents = [nltk.word_tokenize(sent) for sent in sents]
    for k in k_s:
        for idx, tokens in enumerate(toked_sents):
            if k in tokens:
                token_idx = tokens.index(k)
                quoted_token = '`' + k + '`'
                toked_sents[idx][token_idx] = quoted_token
                k_s[k] = idx
                break
    quoted_sents = [" ".join(toks) for toks in toked_sents]
    return k_s, quoted_sents

def make_doc(args, ks, sents):
    ids = [0]
    args_not_mentioned = []
    for arg in args:
        if '=' in arg:
            arg = arg.split('=')[0]
        sent_id = ks[arg]
        if sent_id and sent_id not in ids:
            ids.append(sent_id)
        elif sent_id is None:
            args_not_mentioned.append(arg)
    ret_sents = [sents[idx] for idx in ids]
    if args_not_mentioned and args_not_mentioned != ['']:
        for i in range(len(args_not_mentioned)):
            args_not_mentioned[i] = '`' + args_not_mentioned[i] + '`'
        ret_sents.append("With arguments " + ', '.join(args_not_mentioned) + '.')
    return " ".join(ret_sents)

if __name__ == '__main__':
    fd = open('python-docs.jsonl', 'w', encoding='utf-8')
    counter = 0
    module_counter = {}
    for root, dirs, files in os.walk("Python-3.7.5/Doc/build/html/library"):
        for file in files:
            if file.endswith('.html'):
                input_filename = os.path.join(root, file)
                module_count = 0
                with open(input_filename, encoding='utf-8') as html_file:
                    soup = BeautifulSoup(html_file.read(), 'html.parser')
                    all_sections = soup.find('div', 'body').find_all('dl')
                    current_class_name = None
                    for section in all_sections:
                        section_class_attrs = section.get('class')
                        if section_class_attrs is None:
                            continue
                        sig_type = section_class_attrs[0]
                        if sig_type not in ('function', 'class', 'method', 'attribute', 'describe', 'data', 'exception'):
                            continue
                        doc_paragraphs = section.find('dd').find_all('p', recursive=False)
                        doc_sents = []
                        for para in doc_paragraphs:
                            doc_sents += nltk.sent_tokenize(para.text.strip().replace('\n', ' '))
                        if not doc_sents:
                            continue
                        func_sigs = get_func_signatures(section.find_all('dt', recursive=False))
                        if sig_type == 'class':
                            current_class_name = get_class_name(func_sigs[0])
                            current_class_prefix = inflection.underscore(current_class_name)

                        for func_sig in func_sigs:
                            module_count += 1
                            if sig_type in ('method', 'attribute') and '.' not in func_sig.split('(')[0]:
                                # special case of classmethod
                                if sig_type == 'method' and '(' not in func_sig:
                                    pass
                                else:
                                    func_sig = current_class_prefix + '.' + func_sig
                            func_head, combinations, keywords = parse_optional_args(func_sig)
                            if combinations is not None:
                                arg_sent_id, quoted_doc_sents = match_doc_sents(keywords, doc_sents)
                                for combination in combinations:
                                    doc = make_doc(combination, arg_sent_id, quoted_doc_sents)
                                    example = {
                                        'snippet': func_head + '(' + ", ".join(combination) + ')',
                                        'intent': doc,
                                        'question_id': counter
                                    }
                                    counter += 1
                                    fd.write(json.dumps(example) + '\n')
                            else:
                                example = {
                                    'snippet': func_sig,
                                    'intent': doc_sents[0],
                                    'question_id': counter
                                }
                                counter += 1
                                fd.write(json.dumps(example) + '\n')
                module_counter[input_filename] = module_count
    sorted_counter = sorted(module_counter.items(), key=lambda kv: kv[1])
    for item in sorted_counter:
        print(item)