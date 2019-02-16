import os


def create_folder(path):
    folder = os.path.dirname(path)
    if not os.path.exists(folder):
        print(folder)
        os.makedirs(folder)
