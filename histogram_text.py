import fileinput
import math
import re


number_re = re.compile("\* (\d+)")
count_by_number_of_things = {}


def dump_output(hash_to_dump):
    # for key in sorted(hash_to_dump.keys()):
        # print("%s:%s" % (key, hash_to_dump[key]))
    bucketed_hash = {}
    for key in hash_to_dump.keys():
        order_of_magnitude = int(math.log10(key))
        # first_digit = int(key / 10 ** order_of_magnitude)
        bucket_lower = key * 10 ** order_of_magnitude
        bucket_upper = ((key + 1) * 10 ** order_of_magnitude) - 1
        bucket = "%s-%s" % (bucket_lower, bucket_upper)
        new_count = bucketed_hash.get(bucket, 0)
        bucketed_hash[bucket] = new_count


for line in fileinput.input():
    match_result = number_re.match(line)

    if not match_result:
        print("Broken line:", line)
        exit(22)

    number_of_things = int(match_result.group(1))

    new_count = count_by_number_of_things.get(number_of_things, 0) + 1
    count_by_number_of_things[number_of_things] = new_count


dump_output(count_by_number_of_things)
