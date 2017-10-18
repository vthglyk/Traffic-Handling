import argparse
import time
import logging
from server_info import ServerInfo


def parse_logs(log_file, last_pos, max_rules):
    tcp_hit = "TCP_HIT"
    tcp_miss = "TCP_MISS"

    with open(log_file, 'r') as f:
        f.seek(last_pos)
        new_data = f.readlines()
        last_pos = f.tell()

        banned_servers = {}
        whitelist = []

        for i in new_data:
            parts = i.split()

            server_id = parts[1]
            server_ip = parts[2]
            request_result = parts[3]

            if server_id in whitelist:
                continue

            if tcp_hit in request_result:
                whitelist.append(server_id)
                if server_id in banned_servers:
                    del banned_servers[server_id]
            elif tcp_miss in request_result:
                if server_id not in banned_servers:
                    server_info = ServerInfo(server_id, server_ip, 1)
                    banned_servers[server_id] = server_info
                else:
                    banned_servers[server_id].increase_misses(1)

    blacklist = sorted(banned_servers.values(), key=lambda x: x.no_misses, reverse=True)

    if max_rules:
        blacklist = blacklist[0:max_rules]

    # Return the result in a sorted list along with the last_pos
    return [blacklist, last_pos]


def construct_messages(old_blacklist, new_blacklist):
    rules_to_delete = []


    for i in old_blacklist:
        if i not in new_blacklist:
            rules_to_delete.append(i)
        else:
            new_blacklist.remove(i)

    rules_to_add = new_blacklist
    return [rules_to_add, rules_to_delete]


def send_opf_rules(rules_to_add, rules_to_delete):
    pass


def main():

    description = ("Parses the squid access.log file in order to find candidate servers to "
                   "be blacklisted for the transparent cache.")
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--period', '-p', default=20, type=int,
                        help='the period in seconds (default: 20)')
    parser.add_argument('--file', '-f', default="/var/log/squid/access.log",
                        help='the squid access.log file (default: "/var/log/squid/access.log")')
    parser.add_argument('--maxrules', '-m', default=None, type=int,
                        help='the maximum number of rules to be installed (default: "No limit"')
    parser.add_argument('--loglevel', '-l', default="WARNING",
                        help='the maximum number of rules to be installed (default: "WARNING"')
    args = parser.parse_args()

    period = args.period
    log_file = args.file
    max_rules = args.maxrules
    log_level = args.loglevel

    log_level_numeric = getattr(logging, log_level.upper(), None)
    if not isinstance(log_level_numeric, int):
        raise ValueError('Invalid log level: %s' % log_level)
    logging.basicConfig(level=log_level_numeric)

    blacklist = []
    last_pos = 0

    while True:

        new_blacklist, last_pos = parse_logs(log_file, last_pos, max_rules)
        rules_to_add, rules_to_delete = construct_messages(blacklist, new_blacklist)
        logging.info("rules_to_add = " + str(map(lambda x: x.id, rules_to_add)))
        logging.info("rules_to_delete = " + str(map(lambda x: x.id, rules_to_delete)))
        send_opf_rules(rules_to_add, rules_to_delete)
        blacklist = new_blacklist
        time.sleep(period)


if __name__ == '__main__':
    # Start up the traffic handling module
    main()
