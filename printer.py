#!/usr/bin/env python3

from PIL import Image

class DisplayPrinter:
    def __init__(self):
        pass

    def print_image(self, image, **kwargs):
        image.show()

    @property
    def dpi(self):
        return 300

    def padding(self):
        return (0, 0)

class RotatePrinter:
    def __init__(self, printer=None, rot=90):
        self.printer = printer
        self.rot = rot
        pass

    def print_image(self, image, **kwargs):
        image = image.transpose(Image.Transpose.ROTATE_90)
        self.printer.print_image(image, **kwargs)

    @property
    def dpi(self):
        return self.printer.dpi

    def padding(self):
        return self.printer.padding()
