from collections import defaultdict
import fileinput
import re


instance_re = re.compile(r"\* (\d+)")
ratings_uniques = defaultdict(int)
ratings_instances = defaultdict(int)

for line in fileinput.input("-"):
    (rating, remainder) = line.split("\t")
    instances = instance_re.match(remainder).group(1)

    ratings_uniques[rating] += 1
    ratings_instances[rating] += int(instances)

total_uniques = 0
total_instances = 0
for (rating, uniques) in sorted(ratings_uniques.items()):
    instances = ratings_instances[rating]
    print("%s %s/%s" % (rating, instances, uniques))
    total_uniques += uniques
    total_instances += instances
print("TOTAL %s/%s" % (total_instances, total_uniques))
