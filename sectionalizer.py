import fileinput
import re


def get_word(line):
    match_result = re.search(r"\[\[(.*?)\]\]",
                             line)
    return match_result.group(1)


grouped_lines = {}
for line in fileinput.input("-"):
    line = line.strip()
    word = get_word(line)
    # Group by initial character
    lines = grouped_lines.get(word[0], [])
    lines.append(line)
    grouped_lines[word[0]] = lines

changes_made = True
while changes_made:
    changes_made = False
    new_hash = {}
    for (group_key, line_list) in grouped_lines.items():
        if len(line_list) > 50 and len(group_key) < 5:
            changes_made = True
            for line in line_list:
                word = get_word(line)
                new_key = word[0:len(group_key) + 1]
                lines = new_hash.get(new_key, [])
                lines.append(line)
                new_hash[new_key] = lines
        else:
            new_hash[group_key] = line_list
    grouped_lines = new_hash

for (group_key, line_list) in sorted(grouped_lines.items()):
    print("==== %s ====" % group_key)
    for line in sorted(line_list):
        print(line)
