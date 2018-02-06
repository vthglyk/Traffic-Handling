"""
Executed with:
celery -A traffic_handling worker -B --loglevel=info --file=tests/resources/test_access.log
"""

import logging
import redis
import json

from celery import Celery
from celery import bootsteps
from server_info import ServerInfo
from server_info import ServerInfoEncoder

args = dict()
app = Celery(__name__)

period = 10.0
r = redis.StrictRedis(host='localhost', port=6379, db=0)
r.delete("last_pos")
r.delete("blacklist")
r.set("last_pos", 0)
r.set("blacklist", json.dumps([]))

rootLogger = logging.getLogger()

fileHandler = logging.FileHandler("logs/traffic_handling.log")
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
rootLogger.addHandler(consoleHandler)


def add_worker_arguments(parser):
    parser.add_argument('--period', '-p', default=2, type=int,
                        help='the period in seconds (default: 2)')
    parser.add_argument('--file', default="/var/log/squid/access.log",
                        help='the squid access.log file (default: "/var/log/squid/access.log")')
    parser.add_argument('--maxrules', '-m', default=None, type=int,
                        help='the maximum number of rules to be installed (default: "No limit"')


app.user_options['worker'].add(add_worker_arguments)


class MyBootstep(bootsteps.Step):

    def __init__(self, worker, period, file, maxrules, **options):
        self.period = period
        self.file = file
        self.maxrules = maxrules

        args["period"] = period
        args["file"] = file
        args["maxrules"] = maxrules


app.steps['worker'].add(MyBootstep)


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls extracting_rules() every 'period' seconds.
    sender.add_periodic_task(period, extracting_rules.s(), name='extract rules')
    # Todo: Check if the above can be configured as a command-line argument


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

            server_ip = (parts[6].split('//')[1].split('/')[0])
            server_id = server_ip

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


def json_string_to_blacklist(jsonstring):
    blacklist = []

    for i in jsonstring:
        logging.debug("ServerInfo(id, ip, no_misses = (" + i["id"] + ", " + i["ip"] + ", " + str(i["no_misses"]) + ")")
        blacklist.append(ServerInfo(i["id"], i["ip"], i["no_misses"]))

    return blacklist


@app.task
def extracting_rules():
    last_pos = int(r.get("last_pos"))
    blacklist_str = json.loads(r.get("blacklist"))
    log_file = args["file"]
    max_rules = int(args["maxrules"]) if args["maxrules"] is not None else None

    logging.debug("Extracting_rules")
    blacklist = json_string_to_blacklist(blacklist_str)

    logging.debug("last_post = " + str(last_pos))
    logging.debug("blacklist = " + str(blacklist))
    logging.debug("file = " + log_file)
    logging.debug("maxrules = " + ("None" if max_rules is not None else str(max_rules)))

    new_blacklist, last_pos = parse_logs(log_file, last_pos, max_rules)
    rules_to_add, rules_to_delete = construct_messages(blacklist, new_blacklist)

    logging.info("rules_to_add = " + str(map(lambda x: x.id, rules_to_add)))
    logging.info("rules_to_delete = " + str(map(lambda x: x.id, rules_to_delete)))

    send_opf_rules(rules_to_add, rules_to_delete)
    blacklist = new_blacklist

    r.set('last_pos', last_pos)
    r.set("blacklist", json.dumps(blacklist, cls=ServerInfoEncoder))

    rules = dict()
    rules["rules_to_add"] = map(lambda x: x.ip, rules_to_add)
    rules["rules_to_delete"] = map(lambda x: x.ip, rules_to_delete)
    r.set("rules", json.dumps(rules, cls=ServerInfoEncoder))
