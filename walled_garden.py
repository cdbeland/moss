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
    cursor.execute("SELECT page_title FROM page")
    page_titles = list(cursor)
    cursor.close()

    for page in page_titles:
        cursor = mysql_connection.cursor()
        # "WHERE BINARY" for case-sensitive match

        cursor.execute("SELECT to FROM named_page_links WHERE BINARY from=%s", [page])
        links_out = list(cursor)
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


# This constructs chains of articles, from left to right, and detects
# and streamlines loops along the way.
def iterate_stitching(chains_by_head):
    new_chains_by_head = defaultdict(list)
    for (chain_head, chains) in chains_by_head.items():
        print("PROCESSING HEAD:")
        print(chain_head)
        for chain in chains:
            print("ATTACHING TO")
            print(chain[-1])
            extension_chains = chains_by_head.get(chain[-1], [])
            if extension_chains:
                for extension_chain in extension_chains:
                    loop_detected = False
                    for i in range(1, len(extension_chain)):
                        if extension_chain[i] == chain[0]:
                            loop_detected = True
                            new_loop = set()
                            new_loop_name = chain[0]
                            if new_loop_name.startswith("#LOOP#"):
                                new_loop_name = new_loop_name.replace("#LOOP#", "")
                                new_loop = loops[new_loop_name]  # Retain existing members
                            for loop_member in chain + extension_chain[0:i]:
                                if loop_member.startswith("#LOOP#"):
                                    continue
                                new_loop.add(loop_member)
                                old_loop_name = loop_map.get(loop_member)
                                if old_loop_name and old_loop_name != new_loop_name:
                                    # Consolidate with an existing loop
                                    for old_loop_member in loops[old_loop_name]:
                                        new_loop.add(old_loop_member)
                                        loop_map[old_loop_member] = new_loop_name
                                    del loops[old_loop_name]
                                else:
                                    loop_map[loop_member] = new_loop_name
                            loops[new_loop_name] = new_loop
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

    for loop_number in [1, 2]:
        new_chains_by_head = iterate_stitching(chains_by_head)
        chains_by_head = defaultdict(list)
        for head in new_chains_by_head.keys():
            chains_by_head[head] = update_list_of_chains(new_chains_by_head[head])
        dead_end_chains = update_list_of_chains(dead_end_chains)

        print("LM:")
        pprint(loop_map)
        print("LOOPS:")
        pprint(loops)
        print("CBH")
        pprint(chains_by_head)
        print("DEC")
        pprint(dead_end_chains)

    all_looped_chains = []
    for list_of_chains in chains_by_head.values():
        all_looped_chains.extend(list_of_chains)
    all_looped_chains = dedup_list_of_chains(all_looped_chains)

    print()
    print("*****")
    print()
    print("DEAD-END CHAINS")
    pprint(dead_end_chains)
    print()
    print("DEAD-END PAGES")
    pprint(dead_end_pages)
    print()
    print("ALL LOOP-ENDED CHAINS")
    pprint(all_looped_chains)
    print()
    print("LOOPS:")
    for (loop_name, loop_members) in loops.items():
        print(f"{loop_name}: {len(loop_members)} articles - {list(loop_members)[:5]}")

    # TODO: Prune chains that begin with redirects or disambiguation pages


# run_walled_garden_check(chains_by_head)

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
