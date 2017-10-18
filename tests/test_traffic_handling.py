import traffic_handling
import test_helpers
from unittest import TestCase
from server_info import ServerInfo


class TestTraicHandling(TestCase):
    def test_parse_logs(self):
        file_path = "resources/test_access.log"

        # 1st iteration
        server_info3 = ServerInfo(3, "192.168.10.3", 3)
        server_info4 = ServerInfo(4, "192.168.10.4", 1)

        test_helpers.create_log_file(file_path)

        blacklist, last_pos = traffic_handling.parse_logs(file_path, 0, None)
        self.assertEqual(2, len(blacklist))
        self.assertEqual(True, server_info3 == blacklist[0])
        self.assertEqual(True, server_info4 == blacklist[1])

        # 2nd iteration
        server_info3 = ServerInfo(3, "192.168.10.3", 1)
        server_info4 = ServerInfo(4, "192.168.10.4", 2)

        test_helpers.append_log_file(file_path)

        blacklist, last_pos = traffic_handling.parse_logs(file_path, last_pos, None)
        self.assertEqual(2, len(blacklist))
        self.assertEqual(True, server_info3 == blacklist[1])
        self.assertEqual(True, server_info4 == blacklist[0])

        # 3rd iteration, same with 2nd but with max_rules == 1
        test_helpers.append_log_file(file_path)

        blacklist, last_pos = traffic_handling.parse_logs(file_path, last_pos, 1)
        self.assertEqual(1, len(blacklist))
        self.assertEqual(True, server_info4 == blacklist[0])

    def test_construct_messages(self):

        # Test with empty old_blacklist and non-empty new_blacklist
        server_info3 = ServerInfo(3, "192.168.10.3", 3)
        server_info4 = ServerInfo(4, "192.168.10.4", 1)
        new_blacklist = [server_info3, server_info4]

        rules_to_add, rules_to_delete = traffic_handling.construct_messages([], new_blacklist)
        self.assertEqual(2, len(rules_to_add))
        self.assertEqual(True, rules_to_add[0] == server_info3)
        self.assertEqual(True, rules_to_add[1] == server_info4)
        self.assertEqual(0, len(rules_to_delete))

        # Test with non-empty old_blacklist and empty new_blacklist
        server_info3 = ServerInfo(3, "192.168.10.3", 3)
        server_info4 = ServerInfo(4, "192.168.10.4", 1)
        old_blacklist = [server_info3, server_info4]

        rules_to_add, rules_to_delete = traffic_handling.construct_messages(old_blacklist, [])
        self.assertEqual(0, len(rules_to_add))
        self.assertEqual(2, len(rules_to_delete))
        self.assertEqual(True, rules_to_delete[0] == server_info3)
        self.assertEqual(True, rules_to_delete[1] == server_info4)

        # Test with non-empty old_blacklist and non-empty new_blacklist
        server_info1 = ServerInfo(1, "192.168.10.1", 3)
        old_blacklist = [server_info1, server_info3]

        rules_to_add, rules_to_delete = traffic_handling.construct_messages(old_blacklist, new_blacklist)
        self.assertEqual(1, len(rules_to_add))
        self.assertEqual(True, rules_to_add[0] == server_info4)
        self.assertEqual(1, len(rules_to_delete))
        self.assertEqual(True, rules_to_delete[0] == server_info1)
