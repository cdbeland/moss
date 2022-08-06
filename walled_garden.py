from collections import defaultdict
import mysql.connector
from pprint import pprint


dead_end_pages = []
dead_end_chains = list()
loop_map = dict()
loops = dict()
# loop_map["ginger"] = "ginger"
# loops["ginger"] = set("ginger", "spice")
chains_by_head = defaultdict(list)


def load_sql_data():
    mysql_connection = mysql.connector.connect(user='beland',
                                               host='127.0.0.1',
                                               database='enwiki')
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT page_title FROM page LIMIT 100")  ###
    page_titles = [page[0].decode("utf8") for page in cursor]
    cursor.close()

    for page in page_titles:
        cursor = mysql_connection.cursor()
        # "WHERE BINARY" would do a case-sensitive match, but ignores
        # the indexes, so that's way too slow.

        cursor.execute('SELECT pl_from, pl_to FROM named_page_links WHERE pl_from=%s', [page])
        links_out = list(cursor)
        links_out = [result[1].decode("utf8") for result in links_out if result[0].decode("utf8") == page]
        cursor.close()
        if not links_out:
            dead_end_pages.append(page)
        for link_out in links_out:
            chains_by_head[page].append([page, link_out])
    mysql_connection.close()


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
                # Obsolete loop name
                old_loop_name = title.replace("#LOOP#", "")
                if old_loop_name not in loops:
                    new_loop_title = loop_map[old_loop_name]
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
def iterate_stitching(chains_by_head):
    new_chains_by_head = defaultdict(list)
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
                            _ = convert_chain_to_loop(old_chain, new_loop_name)
                            new_chain = [f"#LOOP#{new_loop_name}"] + extension_chain[i + 1:]
                            break
                    if not loop_detected:
                        new_chain = chain + extension_chain[1:]
                    new_chains_by_head[chain[0]].append(new_chain)
            elif chain[-1].startswith("#LOOP#"):
                new_chains_by_head[chain[0]].append(chain)
            else:
                dead_end_chains.append(chain)
    return new_chains_by_head


def run_walled_garden_check(chains_by_head):
    global dead_end_chains

    load_sql_data()

    for loop_number in range(0, 10):
        new_chains_by_head = iterate_stitching(chains_by_head)
        chains_by_head = defaultdict(list)
        for head in new_chains_by_head.keys():
            chains_by_head[head] = update_list_of_chains(new_chains_by_head[head])
        dead_end_chains = update_list_of_chains(dead_end_chains)

        """
        print("LM:")
        pprint(loop_map)
        print("LOOPS:")
        pprint(loops)
        print("CBH")
        pprint(chains_by_head)
        print("DEC")
        pprint(dead_end_chains)
        """

    all_looped_chains = []
    for list_of_chains in chains_by_head.values():
        all_looped_chains.extend(list_of_chains)
    all_looped_chains = dedup_list_of_chains(all_looped_chains)

    print()
    print("*****")
    """
    print()
    print("DEAD-END CHAINS")
    pprint(dead_end_chains)
    print()
    print("DEAD-END PAGES")
    pprint(dead_end_pages)
    """
    print()
    print("ALL LOOP-ENDED CHAINS")
    pprint(all_looped_chains)
    print()
    print("--")
    print()
    print(f"DEAD-END CHAINS: {len(dead_end_chains)}")
    print(f"DEAD-END PAGES: {len(dead_end_pages)}")
    print(f"LOOP-ENDED CHAINS: {len(all_looped_chains)}")

    print("LOOPS:")
    for (loop_name, loop_members) in loops.items():
        print(f"{loop_name}: {len(loop_members)} articles - {list(loop_members)[:5]}")

    # TODO: Prune chains that begin with redirects or disambiguation pages


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


# test_walled_garden_check()
run_walled_garden_check(chains_by_head)
