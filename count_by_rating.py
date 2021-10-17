from collections import defaultdict
import fileinput
import re
import subprocess

instance_re = re.compile(r"\* (\d+)")
ratings_uniques = defaultdict(int)
ratings_instances = defaultdict(int)

for line in fileinput.input("-"):
    (rating, remainder) = line.split("\t")
    if rating.startswith("TF"):
        # Collapse all non-English languages for statistical purposes
        rating = "TF"
    instances = instance_re.match(remainder).group(1)

    ratings_uniques[rating] += 1
    ratings_instances[rating] += int(instances)

total_uniques = 0
total_instances = 0
sorted_tuples = sorted(ratings_uniques.items())
for (rating, uniques) in sorted_tuples:
    instances = ratings_instances[rating]
    print("%s %s/%s" % (rating, instances, uniques))
    total_uniques += uniques
    total_instances += instances
print("TOTAL %s/%s" % (total_instances, total_uniques))

print("|-")
print("INSTANCES ALL IN ONE LINE:")

ratings_sorted = [rating for (rating, uniques) in sorted_tuples]
print("! Dump (moss version) || Parse failures (articles + articles with [[MOS:STRAIGHT]] violations) || TOTAL (instances) || " + " || ".join(ratings_sorted))

print("|-")

instances_sorted = [str(ratings_instances[rating]) for (rating, uniques) in sorted_tuples]
fails_output = subprocess.run(["wc", "-l", "post-parse-failures.txt"], capture_output=True)
(num_failed_articles, _filename) = fails_output.stdout.decode("utf-8").split(" ")
mos_straight_fails_output = subprocess.run(["wc", "-l", "jwb-straight-quotes-unbalanced.txt"], capture_output=True)
(num_mos_straight_failed, _filename) = mos_straight_fails_output.stdout.decode("utf-8").split(" ")
print(f"| DUMP# || {num_failed_articles} + {num_mos_straight_failed} || {total_instances} || " + " || ".join(instances_sorted))
