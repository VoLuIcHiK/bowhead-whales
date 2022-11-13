import random
import sys
from time import sleep
from .model import NN

import contextlib


@contextlib.contextmanager
def redirect_argv(new_path):
    sys._argv = sys.argv[:]
    sys.argv = [str(new_path)]
    yield
    sys.argv = sys._argv



def run_nn_on_image(n: NN, path_to_png: str, path_to_jpg: str) -> int:
    # TODO
    with redirect_argv(__file__):
        x = n.get_result_of_image_by_path(path_to_png)
        if x is None:
            raise Exception(f"NN returned NONE on image {path_to_png}")
        return x
