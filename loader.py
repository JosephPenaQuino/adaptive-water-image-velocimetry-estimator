'''Loader of videos of frames'''

import json
import os
import abc
import argparse
import cv2


FOLDER_PATH = '/home/joseph/Documents/Thesis/Dataset/config'


class Loader(metaclass=abc.ABCMeta):
    '''Abstract class of loader'''
    def __init__(self, offset: int):
        self._offset = offset
        self._index = 0

    @property
    def index(self):
        '''index getter'''
        return self._index

    @abc.abstractmethod
    def has_images(self):
        '''Check if the source contains one more frame'''

    @abc.abstractmethod
    def read(self):
        '''Read a new image from the source'''

    @abc.abstractmethod
    def end(self):
        '''Free all resources'''


class ImageLoader(Loader):
    '''Loader that loads images from a directory'''

    def __init__(self, config: dict):
        super().__init__(config['image_number_offset'])
        self._image_dataset = config['image_dataset']
        self._prefix = config['image_path_prefix']
        self._digits = config['image_path_digits']
        self._image_number = len(os.listdir(self._image_dataset))

    def has_images(self):
        return self._index < self._image_number

    def _path(self, i: int):
        i += self._offset
        if self._digits == 5:
            return f'{self._image_dataset}/{self._prefix}{i:05}.jpg'
        if self._digits == 3:
            return f'{self._image_dataset}/{self._prefix}{i:03}.jpg'
        return f'{self._image_dataset}/{self._prefix}{i:04}.jpg'

    def set_index(self, index: int):
        '''Set index of the loader to read any image from the folder'''
        self._index = index

    def read(self):
        self._index += 1
        return cv2.imread(self._path(self._index))

    def end(self):
        pass


class VideoLoader(Loader):
    '''Loader that loads from a video'''

    def __init__(self, config: dict):
        super().__init__(config['image_number_offset'])
        self._video_path = config['video_path']
        self._cap = cv2.VideoCapture(self._video_path)
        self._image = None # Current image
        self._image_read = False # Check if the current images was read

        # Get number of frames
        cap = cv2.VideoCapture(self._video_path)
        property_id = int(cv2.CAP_PROP_FRAME_COUNT)
        self.total_frames = int(cv2.VideoCapture.get(cap, property_id)) + 1

        # Skip offset
        for _ in range(self._offset+1):
            if self.has_images():
                self.read()

    def has_images(self):
        if not self._cap.isOpened():
            return False
        ret, self._image = self._cap.read()
        self._image_read = False
        return ret

    def read(self):
        self._index += 1
        if self._image_read:
            _, self._image = self._cap.read()
        self._image_read = True
        return self._image

    def end(self):
        self._cap.release()


def get_loader(config_path: str, video_identifier: str) -> Loader:
    '''Return a ImageLoader or VideoLoader class
    Read config path and if the image dataset folder is full the function
    returns a ImageLoader, if not, then returns a VideoLoader
    '''
    # check if in image folder there are located the extracted images
    with open(config_path) as json_file:
        config = json.load(json_file)[video_identifier]

    image_folder_path = config['image_dataset']
    if any(os.scandir(image_folder_path)):
        return ImageLoader(config)
    return VideoLoader(config)


def main(config_path: str, video_identifier: str, save_image: bool):
    '''Execute a basic example of loader'''
    loader = get_loader(config_path, video_identifier)
    image = loader.read()
    if save_image:
        cv2.imwrite('tmp.jpg', image)
    else:
        cv2.imshow('image', cv2.resize(image, (1000, 1000)))
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    loader.end()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "statio_name",
        help="Name of the station to be analyzed")
    parser.add_argument(
        "video_identifier",
        help="Index of the video of the json config file")
    parser.add_argument(
        '-s',
        '--save',
        help='Save images instead of showing',
        action='store_true')
    parser.add_argument(
        '-p',
        '--path',
        help='Path to the config folder',
        type=str,
        default=FOLDER_PATH)

    args = parser.parse_args()
    CONFIG_PATH = f'{args.path}/{args.statio_name}.json'
    main(config_path=CONFIG_PATH, video_identifier=args.video_identifier,
            save_image=args.save)
