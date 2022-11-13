from unittest import TestCase
from qtpure.backend import *


class Test(TestCase):
    def test_parse_all_images_in_folder_recursivily(self):
        res = parse_all_images_in_folder_recursivily("A")
        print(res)
        self.assertIsNotNone(res)
        self.assertEqual(545, len(res.keys()))

    def test_parse_inner_folders_as_groups(self):
        res = parse_inner_folders_as_groups("A")
        print(res)
        self.assertIsNotNone(res)
        self.assertEqual(2, len(res.keys()))
        c = 0
        for folders_pack in res.values():
            c += len(folders_pack)
        self.assertEqual(545, c)

    def test_get_new_parsed_images(self):
        t = threading.Thread(target=parse_all_images_in_folder_recursivily, args=("A",), daemon=True)
        t.start()
        start_timestamp = datetime.datetime.now()
        parsed = list()
        while True:
            t.join(0.001)
            new_parsed = get_new_parsed_images()
            if len(new_parsed) > 0:
                parsed += new_parsed
                print(new_parsed)
            if t.is_alive():
                continue
            break
        self.assertEqual(545, len(parsed))

    def test_get_only_stats_from_new_parsed_images(self):
        t = threading.Thread(target=parse_inner_folders_as_groups, args=("A",), daemon=True)
        t.start()
        start_timestamp = datetime.datetime.now()
        parsed = list()
        last_pass = False
        c = 0
        while True:
            t.join(1)
            new_parsed: Dict[str, Dict[int, int]] = get_only_stats_from_new_parsed_images()
            if len(new_parsed) > 0:
                for folder_stats in new_parsed.values():
                    for count in folder_stats.values():
                        c += count
                parsed += new_parsed
                print(new_parsed)
            if t.is_alive():
                continue
            if last_pass:
                break
            last_pass = True
        self.assertEqual(545, c)
