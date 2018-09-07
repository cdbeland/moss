import fileinput
import re


MAX_SIZE = 50
MIN_SIZE = 15
MAX_KEY_LENGTH = 5


def get_word(line):
    match_result = re.search(r"\[\[(.*?)\]\]",
                             line)
    word = match_result.group(1)
    if word.startswith("wikt:"):
        word = word.replace("wikt:", "")
    return word


def split_big_sections(grouped_lines):
    changes_made = True
    while changes_made:
        changes_made = False
        new_hash = {}
        for (group_key, line_list) in grouped_lines.items():
            if len(line_list) > MAX_SIZE and len(group_key) < MAX_KEY_LENGTH:
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
    return new_hash


def merge_small_sections(grouped_lines):
    new_hash = {}
    previous_key = None
    for (group_key, line_list) in sorted(grouped_lines.items()):
        if len(line_list) < MIN_SIZE and previous_key:
            tmp_list = new_hash[previous_key]
            if len(tmp_list) < MAX_SIZE - MIN_SIZE:
                tmp_list.extend(line_list)
                del new_hash[previous_key]
                key_parts = previous_key.split("-")
                new_key = "%s-%s" % (key_parts[0], group_key)
                new_hash[new_key] = tmp_list
                previous_key = new_key
            else:
                new_hash[group_key] = line_list
                previous_key = group_key
        else:
            new_hash[group_key] = line_list
            previous_key = group_key
    return new_hash


if __name__ == '__main__':
    grouped_lines = {}
    for line in fileinput.input("-"):
        line = line.strip()
        word = get_word(line)
        # Group by initial character
        lines = grouped_lines.get(word[0], [])
        lines.append(line)
        grouped_lines[word[0]] = lines
    grouped_lines = split_big_sections(grouped_lines)
    grouped_lines = merge_small_sections(grouped_lines)
    for (group_key, line_list) in sorted(grouped_lines.items()):
        print("==== %s ====" % group_key)
        for line in sorted(line_list):
            print(line)
