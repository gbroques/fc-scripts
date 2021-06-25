#!/usr/bin/env /home/g/Desktop/squashfs-root/usr/bin/python
"""
Takes screenshots of leaf nodes in an assembly.
"""
import sys
FREECAD_LIB = '/home/g/Desktop/squashfs-root/usr/lib/'

sys.path.append(FREECAD_LIB)

from typing import Any, Callable, List
import subprocess
import argparse

from pathlib import Path

import FreeCAD as App


__all__ = ['traverse']

ASSEMBLY_TYPE_IDS = {'App::Part', 'App::Link'}


def traverse(objects: List[object],
             visit: Callable[[object, list], Any],
             path: list = []) -> None:
    for obj in objects:
        visit(obj, path)
        if obj.TypeId in ASSEMBLY_TYPE_IDS:
            args = _get_resolve_objects_args(obj, visit, path)
            traverse(*args)


def _get_resolve_objects_args(obj, visit, path):
    path_with_obj = path + [obj]
    if obj.TypeId == 'App::Part':
        return [
            obj.Group,
            visit,
            path_with_obj
        ]
    elif obj.TypeId == 'App::Link':
        return [
            [obj.LinkedObject],
            visit,
            path_with_obj
        ]

# def is_leaf_part(obj):
#     return obj.TypeId not in ASSEMBLY_TYPE_IDS and obj.isDerivedFrom('Part::Feature')

def traverse_document_tree(obj: object, path: list) -> None:
    # if is_leaf_part(obj):
    parent = None if len(path) == 0 else path[-1]
    current_document = obj.Document.Name
    previous_document = None if not parent else parent.Document.Name
    did_document_change = current_document != previous_document
    
    if parent:
        if did_document_change:
            print('Screenshotting ' + obj.Label + ' ' + obj.TypeId)
            screenshot(obj)
    else:
        print('Screenshotting ' + obj.Label + ' ' + obj.TypeId)
        screenshot(obj)

    # print('Screenshotting ' + obj.Document.Name)
    # document_path = obj.Document.FileName

    # screenshot_path = str(Path(__file__).parent.resolve().joinpath('screenshot.py'))
    # subprocess.run([screenshot_path, '--size', '1000', '--screenshot-path', './screenshot', document_path])


def screenshot(obj):
    document_path = obj.Document.FileName

    screenshot_path = str(Path(__file__).parent.resolve().joinpath('screenshot.py'))
    subprocess.run([screenshot_path, '--size', '1000', '--screenshot-path', './screenshot', document_path])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Screenshot leaf documents of an assembly.')
    parser.add_argument('document_path', help='Path to FreeCAD document.')
    args = parser.parse_args()
    document = App.openDocument(args.document_path)
    root_objects = [obj for obj in document.Objects if obj.Label == document.Name]
    if len(root_objects) > 0:
        root_object = root_objects[0]
        traverse([root_object], traverse_document_tree)
    exit(0)
