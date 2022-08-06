from collections import defaultdict
import itertools
import mysql.connector
from pprint import pprint


dead_end_pages = []
loop_map = dict()
loops = dict()
# loop_map["ginger"] = "ginger"
# loops["ginger"] = set("ginger", "spice")


def load_sql_data():
    print("Loading data...")
    global dead_end_pages
    chains_by_head = defaultdict(list)

    mysql_connection = mysql.connector.connect(user='beland',
                                               host='127.0.0.1',
                                               database='enwiki')
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT page_title FROM page LIMIT 100000")  ###
    page_titles = [page[0].decode("utf8") for page in cursor]
    cursor.close()

    for page in page_titles:
        cursor = mysql_connection.cursor()
        # "WHERE BINARY" would do a case-sensitive match, but ignores
        # the indexes, so that's way too slow.

        cursor.execute('SELECT pl_from, pl_to FROM named_page_links WHERE pl_from=%s AND pl_from != pl_to', [page])
        links_out = list(cursor)
        links_out = [result[1].decode("utf8") for result in links_out if result[0].decode("utf8") == page]
        cursor.close()
        if not links_out:
            dead_end_pages.append(page)
        for link_out in links_out:
            chains_by_head[page].append([page, link_out])
    mysql_connection.close()
    print("Done loading.")
    return chains_by_head


def dedup_list_of_chains(list_of_chains):
    chain_strings = [">".join(chain) for chain in list_of_chains]
    chain_strings = set(chain_strings)
    return [chain_string.split(">") for chain_string in chain_strings]


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


# This constructs chains of articles, from left to right, and detects
# and streamlines loops along the way.
def iterate_stitching(chains_by_head, dead_end_chains):
    live_chains = []
    breadth_limit = 1000
    chain_count = 0
    for (chain_head, chains) in chains_by_head.items():
        for chain in chains:
            if chain_count >= breadth_limit:
                live_chains.append(chain)
                continue
            extension_chains = chains_by_head.get(chain[-1], [])
            if extension_chains:
                chain_count += 1
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


def print_stats(chains_by_head, dead_end_chains, and_results=False):
    print()
    print("*****")
    """
    print()
    print("DEAD-END CHAINS")
    pprint(dead_end_chains)
    print()
    print("DEAD-END PAGES")
    pprint(dead_end_pages)
    print()
    print("LM:")
    pprint(loop_map)
    """

    max_len = max([max([len(chain) for chain in chain_list]) for chain_list in chains_by_head.values()])
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
    test_chains_by_head["bellpepper"] = [["bellpepper", "pepper"]]  # THIS SHOULD NOT BE IN THE COCONUT LOOP
    test_chains_by_head["coconut"] = [["coconut", "ginger"]]
    test_chains_by_head["Jupiter"] = [["Jupiter", "Solar system"]]
    run_walled_garden_check(test_chains_by_head)


# test_walled_garden_check(test_chains_by_head)
run_walled_garden_check(load_sql_data())
