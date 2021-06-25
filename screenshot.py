#!/usr/bin/env /home/g/Desktop/squashfs-root/usr/bin/python
"""Utility script to create thumbnail screenshots of parts.
"""
import argparse
import os
import sys
FREECAD_LIB = '/home/g/Desktop/squashfs-root/usr/lib/'

sys.path.append(FREECAD_LIB)
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui


def screenshot(document_path: str,
               size: int,
               screenshot_base_path: str) -> None:
    # Setup Gui
    Gui.showMainWindow()
    main_window = Gui.getMainWindow()
    main_window.hide()

    document = App.openDocument(document_path)

    screenshot_path = Path(screenshot_base_path)
    screenshot_path.mkdir(parents=True, exist_ok=True)

    active_view = Gui.getDocument(document.Name).activeView()
    active_view.setCameraType('Orthographic')
    active_view.setAnimationEnabled(False)

    # It's important not to use Qt's QGLFramebufferObject because it crashes when no GUI is shown
    # but Qt's QGLPixelBuffer still works.
    parameter = App.ParamGet('User parameter:BaseApp')
    group = parameter.GetGroup('Preferences/Document')
    group.SetBool('DisablePBuffers', False)

    active_view.viewIsometric()
    active_view.fitAll()

    image_name = str(screenshot_path.joinpath('{}.png'.format(document.Name)))
    print('Saving image {}'.format(image_name))
    active_view.saveImage(image_name, size, size, 'Transparent')

    App.closeDocument(document.Name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Screenshot a FreeCAD document.')
    parser.add_argument('document_path', help='Path to FreeCAD document.')
    parser.add_argument('--size', type=int, default=150,
                        help='Size of image. Defaults to 150.')
    parser.add_argument('--screenshot-path', type=str, default=os.getcwd(),
                        help='Path to save screenshots. Defaults to current working directory.')
    args = parser.parse_args()
    screenshot(args.document_path,
               args.size,
               args.screenshot_path)
    exit(0)
