import asyncio
import glob
import os
import datetime
import threading
from copy import deepcopy
from os.path import isfile, join
from pathlib import Path
from time import sleep
from typing import List, Dict

from nn.main import run_nn_on_image
from nn.model import NN

n = NN()


def parse_all_images_in_folder_recursivily(input_path_str: str) -> Dict[str, dict]:
    all_files: Dict[str, dict] = dict()
    path = Path.cwd() / input_path_str
    onlyfiles_names: List[str] = list()
    for file in glob.iglob(str(path.absolute()) + "/**", recursive=True):
        if isfile(join(path.absolute(), file)):
            onlyfiles_names.append(file)

    png_files: List[str] = [str((path / name).absolute()) for name in onlyfiles_names if name.endswith('.png')]
    unchecked_jpg_files: List[str] = [str((path / name).absolute()) for name in onlyfiles_names if
                                      name.endswith('.jpg')]
    for png_file in png_files:
        cur_file = Path(png_file)
        if not cur_file.exists():
            print(f"Изображение {cur_file.absolute()} не найдено!")
            continue

        find_suffix = '.jpg'

        need_file = cur_file.with_suffix(find_suffix)

        if not need_file.exists():
            print(f"Маска {need_file.absolute()} для изображения {cur_file} не найдена!")
            continue

        frame = dict()
        all_files[str(cur_file.absolute())] = frame
        frame['image'] = str(cur_file.absolute())
        frame['mask'] = str(need_file.absolute())
        frame['group_id'] = run_nn_on_image(n, str(cur_file.absolute()), str(need_file.absolute()))
        frame['timestamp'] = int(datetime.datetime.now().timestamp() * 1000)
        with lock:
            new_parsed_images.append(frame)
    return all_files


new_parsed_images: List[Dict[str, str | int]] = list()
new_stats: Dict[str, Dict] = dict()


def parse_inner_folders_as_groups(input_path_str: str) -> Dict[str, dict]:
    print("inner folders")
    all_folders: Dict[str, dict] = dict()
    path = Path.cwd() / input_path_str
    onlyfiles_names: List[str] = list()
    for folder in os.listdir(str(path.absolute())):
        if not isfile(join(path.absolute(), folder)):
            folder_path = path / folder
            parsed_folder = parse_all_images_in_folder_recursivily(str(folder_path.absolute()))
            all_folders[str(folder_path.absolute())] = parsed_folder
    return all_folders


last_get_new_parsed_images_timestamp: datetime.datetime | None = None
lock = threading.Lock()


def get_new_parsed_images() -> List[Dict]:
    global last_get_new_parsed_images_timestamp
    last_get_new_parsed_images_timestamp = datetime.datetime.now()
    last_time = 1
    with lock:
        global new_parsed_images
        frames = deepcopy(new_parsed_images)
        returning = deepcopy(frames)
        new_parsed_images.clear()
        return returning
    pass


def frame_get_folder(frame: Dict) -> str:
    p = Path(frame.get('image', '')).parent
    if not p.exists():
        raise Exception(f"{p} is not exists!")
    if not p.is_dir():
        raise Exception(f"{p} is not folder!")
    return str(p.absolute())


def get_only_stats_from_new_parsed_images() -> Dict:
    """
    :return: {FOLDER1:{0: 99, 1: 1}, FOLDER2:{1:99, 2:1, 0:1}}
    """
    stats = {}
    frames = get_new_parsed_images()
    for frame in frames:
        folder = frame_get_folder(frame)
        group_id = frame.get('group_id', 0)
        folder_stats = stats.get(folder, None)
        if folder_stats is None:
            folder_stats = dict()
            stats[folder] = folder_stats
        group_count = folder_stats.get(group_id, 0)
        folder_stats[group_id] = group_count + 1
    return stats
