import fileinput
import re
import sys


MAX_SIZE = 50
MIN_SIZE = 15
MAX_KEY_LENGTH = 5


def get_word(line):
    match_result = re.search(r"\[\[(.*?)\]\]",
                             line)
    if not match_result or not match_result.group(1):
        print("Word not found in line: '%s'" % line,
              file=sys.stderr)
        return None
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
    previous_key = ""
    for (group_key, line_list) in sorted(grouped_lines.items()):

        # Strong preference for splitting on first letter (since these
        # are often posted to different pages) unless entire first
        # letters fit per section.
        ok_to_join = True
        if len(previous_key) == 0:
            pass
        else:
            if "-" in previous_key:
                (_last_left_side, last_right_side) = previous_key.split("-", 1)
            else:
                last_right_side = previous_key

            if len(last_right_side) == 1 and len(group_key) > 1:
                ok_to_join = False
            elif len(last_right_side) > 1 and len(group_key) == 1:
                ok_to_join = False
            elif len(last_right_side) > 1 and len(group_key) > 1 and last_right_side[0] != group_key[0]:
                ok_to_join = False

        if previous_key:
            previous_size = len(new_hash[previous_key])
        else:
            previous_size = 999999

        current_size = len(line_list)
        if (current_size < MIN_SIZE or previous_size < MIN_SIZE) and previous_key and ok_to_join:
            if previous_size + current_size < MAX_SIZE:
                tmp_list = new_hash[previous_key]
                tmp_list.extend(line_list)
                del new_hash[previous_key]
                key_parts = []
                if previous_key.startswith("-"):
                    key_parts = ["-", previous_key.lstrip("-")]
                else:
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


def group_lines(list_of_lines):
    grouped_lines = {}
    for line in list_of_lines:
        line = line.strip()
        word = get_word(line)
        if not word:
            continue
        # Group by initial character
        lines = grouped_lines.get(word[0], [])
        lines.append(line)
        grouped_lines[word[0]] = lines
    return grouped_lines


def sectionalize_lines(list_of_lines):
    grouped_lines = group_lines(list_of_lines)
    grouped_lines = split_big_sections(grouped_lines)
    grouped_lines = merge_small_sections(grouped_lines)
    output_string = ""
    for (group_key, line_list) in sorted(grouped_lines.items()):
        output_string += (f"==== {group_key} ====\n")
        for line in sorted(line_list, key=lambda line: get_word(line)):
            output_string += f"{line}\n"
    return output_string


if __name__ == '__main__':
    print(sectionalize_lines(fileinput.input("-")))
