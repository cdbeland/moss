import fileinput
import math
import re
import sys

number_re = re.compile("\* (\d+)")
count_by_number_of_things = {}


def chop_key(bucket_name):
    bucket_parts = bucket_name.split("-")
    return int(bucket_parts[0])


def dump_output(hash_to_dump):
    # Consolidate report into ranges (e.g. 741 articles have between 10
    # and 19 misspelled words)
    bucketed_hash = {}
    for key in hash_to_dump.keys():
        print("%s:%s" % (key, hash_to_dump[key]), file=sys.stderr)
        bucket = None
        if key == 0:
            bucket = "0"
        else:
            order_of_magnitude = int(math.log10(key))
            first_digit = int(key / 10 ** order_of_magnitude)
            bucket_lower = first_digit * 10 ** order_of_magnitude
            bucket_upper = ((first_digit + 1) * 10 ** order_of_magnitude) - 1

            if bucket_lower == bucket_upper:
                bucket = str(bucket_lower)
            else:
                bucket = "%s-%s" % (bucket_lower, bucket_upper)

        print("BUCKET: %s" % bucket, file=sys.stderr)
        bucketed_hash[bucket] = bucketed_hash.get(bucket, 0) + hash_to_dump[key]

    # Print out bucketed results
    for bucket_name in sorted(bucketed_hash.keys(), key=chop_key):
        print("%s:%s" % (bucket_name, bucketed_hash[bucket_name]))


# Consoldate individual counts into number of things with that count
# (e.g. how many articles have 1 misspelled word, 2 misspelled words,
# etc.)
for line in fileinput.input():
    match_result = number_re.match(line)

    if not match_result:
        print("Broken line:", line)
        exit(22)

    number_of_things = int(match_result.group(1))

    new_count = count_by_number_of_things.get(number_of_things, 0) + 1
    count_by_number_of_things[number_of_things] = new_count


dump_output(count_by_number_of_things)
