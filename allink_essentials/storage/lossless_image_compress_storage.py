import os
import unicodedata
import subprocess

from django.core.files.storage import FileSystemStorage


class LosslessImageCompressStorage(FileSystemStorage):
    """
    Applies lossless image compression to jpeg, gif and png images
    """
    def get_valid_name(self, name):
        if not isinstance(name, unicode):
            name = unicode(name)
        name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore')
        return super(LosslessImageCompressStorage, self).get_valid_name(name)

    def save(self, name, content):
        path = super(LosslessImageCompressStorage, self).save(name, content)
        full_path = self.path(path)
        extension = os.path.splitext(path)[1].lower()
        if extension in ('.jpeg', '.jpg'):
            # handle jpeg files
            subprocess.call(['jpegtran', '-copy', 'all', '-optimize', '-progressive', '-outfile', full_path, full_path])
        elif extension == '.png':
            # handle png files
            subprocess.call(['optipng', '-o2', full_path, full_path])
        elif extension == '.gif':
            # handle gif files
            subprocess.call(['gifsicle', '-b', '-O3', '--careful', full_path])
        return path
