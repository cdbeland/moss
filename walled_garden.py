from collections import defaultdict
import datetime
import itertools
import mysql.connector
from os.path import exists
from pprint import pprint


mysql_connection = mysql.connector.connect(user='beland',
                                           host='127.0.0.1',
                                           database='enwiki')
TMP_FILENAME = "/tmp/walled_garden_checkpoint.py"
dead_end_pages = []
loop_map = dict()
loops = dict()
# loop_map["ginger"] = "ginger"
# loops["ginger"] = set("ginger", "spice")


# -- SEEDING IMPLEMENTATION --


# Run time:
def find_reachable(start_node, direction):
    reachable_set = set()
    search_queue = [start_node]
    count = 0
    neighbor_count = 0
    while search_queue:
        debug_string = f"{datetime.datetime.now().isoformat()} "
        debug_string += f" queue: {len(search_queue)}"
        debug_string += f" reachable: {len(reachable_set)}"
        if count:
            debug_string += f" avg_branching_factor: {int(neighbor_count / count)}"
        print(debug_string)

        # All these are not in reachable_set or they would not have
        # been added to search_queue.
        reachable_set.update(search_queue)

        # Do DB lookup all at once so we minimize de-duping; all these
        # lookups are necessary because they have not been looked up
        # before.
        neighbor_list = []
        for page in search_queue:
            neighbor_pages = get_neighbors(page, direction)
            neighbor_count += len(neighbor_pages)
            neighbor_list.extend(neighbor_pages)

            count += 1
            if count % 10000 == 0:
                print(f"{datetime.datetime.now().isoformat()}  checked: {count}")
            if count % 1000000 == 0:
                # Letting neighbor_list grow too long can easily cause
                # an out-of-memory error, so we have to occasionally
                # eat the cost of an otherwise unnecessary de-duping.
                # This will probably take 1-2 min, at least the first
                # time it's run.
                print(f"{datetime.datetime.now().isoformat()}  Intermediate deduping...")
                neighbor_list = list(set(neighbor_list))

        print(f"{datetime.datetime.now().isoformat()}  Deduping...")
        neighbors_dedup = set(neighbor_list)
        search_queue = neighbors_dedup - reachable_set

    return reachable_set


def get_neighbors(page_title, direction):
    cursor = mysql_connection.cursor()
    if direction == "forward":
        cursor.execute('SELECT pl_to, pl_from FROM named_page_links WHERE pl_from=%s AND pl_from != pl_to', [page_title])
    elif direction == "backward":
        cursor.execute('SELECT pl_from, pl_to FROM named_page_links WHERE pl_to=%s AND pl_from != pl_to', [page_title])
    else:
        raise Exception(f"Invalid direction {direction}")

    # Decoding and force case-sensitive (WHERE BINARY doesn't use index)
    links = [result[0].decode("utf8") for result in cursor if result[1].decode("utf8") == page_title]
    cursor.close()
    return links


# -- SEEDING MAIN --

articles_inbound = None
articles_outbound = None
if exists(TMP_FILENAME):
    with open(TMP_FILENAME, "r") as tmp_file:
        print("Reading checkpoint data...")
        exec(tmp_file.read())


# "SELECT pl_from, COUNT(pl_to) FROM named_page_links GROUP BY pl_from HAVING COUNT(pl_to) > 1000 ORDER BY COUNT(pl_to);"
# (takes ~1h to run)
# points to "Index_", "List_", and "YEAR_in_X" articles as having the
# highest branching factor
START_NODE = "List_of_lists_of_lists"

if not articles_inbound:
    print("Finding articles via inbound links...")
    articles_inbound = find_reachable(START_NODE, "backward")
    with open(TMP_FILENAME, "a") as tmp_file:
        print("articles_inbound = ", end="", file=tmp_file)
        print(articles_inbound, file=tmp_file)

if not articles_outbound:
    print("Finding articles via outbound links...")
    articles_outbound = find_reachable(START_NODE, "forward")
    with open(TMP_FILENAME, "a") as tmp_file:
        print("articles_outbound = ", end="", file=tmp_file)
        print(articles_outbound, file=tmp_file)

if not loops.get(START_NODE):
    print("Calculating loop boundaries...")
    loops[START_NODE] = articles_outbound.intersection(articles_inbound)
    for page in loops[START_NODE]:
        loop_map[page] = START_NODE
    with open(TMP_FILENAME, "a") as tmp_file:
        print(f'loops["{START_NODE}"] = ', end="", file=tmp_file)
        print(loops[START_NODE], file=tmp_file)

# To free memory
articles_inbound = None
articles_outbound = None


# -- BIRDIRECTIONAL MAIN HELPERS --


def load_sql_data():
    print(datetime.datetime.now().isoformat())
    print("Loading all page titles...")
    global dead_end_pages
    chains_by_head = defaultdict(list)

    cursor = mysql_connection.cursor()
    cursor.execute("SELECT page_title FROM page")
    page_titles = [page[0].decode("utf8") for page in cursor]
    print(f"Got {len(page_titles)} page titles")
    cursor.close()

    print(datetime.datetime.now().isoformat())
    print("Loading all chains...")

    i = 0
    for page in page_titles:
        cursor = mysql_connection.cursor()
        # "WHERE BINARY" would do a case-sensitive match, but ignores
        # the indexes, so that's way too slow.

        cursor.execute('SELECT pl_from, pl_to FROM named_page_links WHERE pl_from=%s AND pl_from != pl_to', [page])
        links_out = [result[1].decode("utf8") for result in cursor if result[0].decode("utf8") == page]
        cursor.close()
        if not links_out:
            dead_end_pages.append(page)
        home_loop = loop_map.get(page)
        for link_out in links_out:
            if home_loop and loop_map.get(link_out) == home_loop:
                # Save a lot of space not storing many chains, and
                # also after chains start getting combined, this will
                # separate redirects into the main loop from dead
                # end links out of the main loop.
                continue
            chains_by_head[page].append([page, link_out])
        i += 1
        if i % 10000 == 0:
            print_stats(chains_by_head, [], and_results=True)

    print(datetime.datetime.now().isoformat())
    print("Done loading.")
    print_stats(chains_by_head, [], and_results=True)
    return chains_by_head


def run_walled_garden_check(chains_by_head):
    # Unclear how many iterations are needed here
    dead_end_chains = []
    for loop_number in range(0, 100):
        print("Lengthening chains...")

        (live_chains, dead_end_chains) = iterate_stitching(chains_by_head, dead_end_chains)

        print("Consolidating and de-duping...")
        live_chains = update_list_of_chains(live_chains)
        dead_end_chains = update_list_of_chains(dead_end_chains)

        print("Re-indexing...")
        chains_by_head = defaultdict(list)
        for chain in live_chains:
            chains_by_head[chain[0]].append(chain)

        print_stats(chains_by_head, dead_end_chains, and_results=True)

    # TODO: Prune chains that begin with redirects or disambiguation pages

    print_stats(chains_by_head, dead_end_chains, and_results=True)


def test_walled_garden_check():
    test_chains_by_head = defaultdict(list)
    test_chains_by_head["ginger"] = [
        ["ginger", "spice"],
        ["ginger", "coconut"],
        ["ginger", "pepper"],
        ["ginger", "redhead"],
    ]
    test_chains_by_head["spice"] = [["spice", "ginger"]]
    test_chains_by_head["pepper"] = [["pepper", "spice"]]
    test_chains_by_head["bellpepper"] = [["bellpepper", "pepper"]]  # This should not be in the coconut loop.
    test_chains_by_head["coconut"] = [["coconut", "ginger"]]
    test_chains_by_head["Jupiter"] = [["Jupiter", "Solar system"]]
    run_walled_garden_check(test_chains_by_head)


# -- BIDIRECTIONAL EXPANSION --


# This constructs chains of articles, from left to right, and detects
# and streamlines loops along the way.
def iterate_stitching(chains_by_head, dead_end_chains):
    live_chains = []
    for (chain_head, chains) in chains_by_head.items():
        for chain in chains:
            extension_chains = chains_by_head.get(chain[-1], [])
            if extension_chains:
                for extension_chain in extension_chains:
                    loop_detected = False
                    for i in range(1, len(extension_chain)):
                        if extension_chain[i] == chain[0]:
                            loop_detected = True
                            new_loop_name = chain[0]
                            if new_loop_name.startswith("#LOOP#"):
                                new_loop_name = new_loop_name.replace("#LOOP#", "")
                            old_chain = chain + extension_chain[0:i]
                            convert_chain_to_loop(old_chain, new_loop_name)
                            new_chain = [f"#LOOP#{new_loop_name}"] + extension_chain[i + 1:]
                            break
                    if not loop_detected:
                        new_chain = chain + extension_chain[1:]
                    live_chains.append(new_chain)
            elif chain[-1].startswith("#LOOP#"):
                live_chains.append(chain)
            else:
                dead_end_chains.append(chain)
    return (live_chains, dead_end_chains)


def convert_chain_to_loop(old_chain, new_loop_name):
    # The chain might contain pages and one or more existing loops.

    new_loop = list()
    sub_loops_to_process = list()
    for link in old_chain:
        if link.startswith("#LOOP#"):
            sub_loop_name = link.replace("#LOOP#", "")
            sub_loops_to_process.append(sub_loop_name)
        else:
            new_loop.append(link)

            # Check to see if this page is already a member of a loop
            # (and this chain hasn't been updated with that info)
            sub_loop_name = loop_map.get(link)
            if sub_loop_name:
                sub_loops_to_process.append(sub_loop_name)

    loops_to_delete = list()
    for sub_loop_name in set(sub_loops_to_process):
        # Loops are not allowed to contain other loops, so we don't
        # need recursion.  Processing each loop only once saves a lot
        # of work because there should be at least one enormous loop.

        if sub_loop_name not in loops:
            # Has already been consolidated with a different loop, so
            # recover by lookup up the current loop of the titular
            # article.
            sub_loop_name = loop_map[sub_loop_name]

        # Add pages from the other loop
        new_loop.extend(loops[sub_loop_name])
        loops_to_delete.append(sub_loop_name)

    # Saving for the end to avoid lookup failures in case of
    # overlapping membership
    for loop_name in set(loops_to_delete):
        if loop_name in loops:
            del loops[loop_name]

    new_loop = set(new_loop)
    loops[new_loop_name] = new_loop
    for loop_member in new_loop:
        loop_map[loop_member] = new_loop_name


# -- BIDIRECTIONAL REDUCING --


def update_list_of_chains(list_of_chains):
    new_list_of_chains = []
    for chain in list_of_chains:
        new_chain = []
        last_title = None
        for title in chain:
            if title.startswith("#LOOP#"):
                loop_name = title.replace("#LOOP#", "")
                if loop_name not in loops:
                    # Obsolete loop name
                    new_loop_title = loop_map[loop_name]
                    title = f"#LOOP#{new_loop_title}"
            elif title in loop_map:
                # Title is part of a loop
                loop_name = loop_map[title]
                title = f"#LOOP#{loop_name}"
            if title == last_title:
                continue
            else:
                new_chain.append(title)
                last_title = title
        new_list_of_chains.append(new_chain)

    return dedup_list_of_chains(new_list_of_chains)


def dedup_list_of_chains(list_of_chains):
    chain_strings = [">".join(chain) for chain in list_of_chains]
    chain_strings = set(chain_strings)
    return [chain_string.split(">") for chain_string in chain_strings]


# -- BIDIRECTIONAL REPORTING --

def print_stats(chains_by_head, dead_end_chains, and_results=False):
    print()
    print("*****")
    print()
    print(datetime.datetime.now().isoformat())
    """
    print("DEAD-END CHAINS")
    pprint(dead_end_chains)
    print()
    print("DEAD-END PAGES")
    pprint(dead_end_pages)
    print()
    print("LM:")
    pprint(loop_map)
    """

    try:
        max_len = max([max([len(chain) for chain in chain_list]) for chain_list in chains_by_head.values()])
    except ValueError:
        max_len = "ERR"
    print(f"MAX LENGTH OF CHAINS: {max_len}")
    print(f"HEADS: {len(chains_by_head)}")
    print(f"DEAD-END CHAINS AFTER DEDUP: {len(dead_end_chains)}")
    chain_count = sum(len(chain) for chain in chains_by_head.values())
    print(f"LIVE CHAINS AFTER DEDUP: {chain_count}")
    print()
    print("LOOPS:")
    for (loop_name, loop_members) in loops.items():
        print(f"{loop_name}: {len(loop_members)} articles - {list(loop_members)[:5]}")
    if and_results:
        print()
        print(f"DEAD-END PAGES: {len(dead_end_pages)}")
        print()
        print("CBH SAMPLE")
        first_heads_and_chains = itertools.islice(chains_by_head.items(), 5)
        for (head, chain) in first_heads_and_chains:
            print(head)
            pprint(chain[0:5])
        print()

    print()
    print("*****")
    print()


# -- MAIN --

# test_walled_garden_check(test_chains_by_head)
run_walled_garden_check(load_sql_data())

mysql_connection.close()
