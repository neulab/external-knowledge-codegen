from bs4 import BeautifulSoup
import json
import os
import re
import sys


def collect_files(dir: str = ".") -> int:
    for subdir, _, files in os.walk(dir):
        for filename in files:
            filepath = os.path.join(subdir, filename)
            if filepath.endswith(".html"):
                yield filepath


id = 0
for file in collect_files():
    with open(file) as fp:
        try:
            soup = BeautifulSoup(fp, 'html.parser')
        except UnicodeDecodeError as e:
            print(f"Error reading {file}: {e}", file=sys.stderr)
            continue

    members = soup.find("table",
                        class_="memberSummary",
                        summary=re.compile("Constructor Summary"))

    if members:
        tds = members.find_all("td", class_="colOne")
        for td in tds:
            if td.code and td.div:
                method = ' '.join(td.code.stripped_strings).replace("\n", "")
                comment = ' '.join(td.div.stripped_strings).replace("\n", "")
                id += 1
                example = {"snippet": method,
                           "intent": comment,
                           "question_id": id}
                print(json.dumps(example))

    members = soup.find("table",
                        class_="memberSummary",
                        summary=re.compile("Method Summary"))
    if members:
        for tr in members.find_all("tr"):
            if tr.find("td"):
                colFirst = tr.find("td", class_="colFirst")
                ret_type = ' '.join(
                    colFirst.code.stripped_strings).replace("\n", "")
                colLast = tr.find("td", class_="colLast")
                if colLast and colLast.code and colLast.div:
                    method = (ret_type + " "
                              + ' '.join(
                                  colLast.code.stripped_strings).replace(
                                      "\n", ""))
                    comment = ' '.join(
                        colLast.div.stripped_strings).replace("\n", "")
                    id += 1
                    example = {"snippet": method,
                               "intent": comment,
                               "question_id": id}
                    print(json.dumps(example))

