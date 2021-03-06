#!/usr/bin/env /home/g/Desktop/squashfs-root/usr/bin/python
import argparse
import os
import sys
FREECAD_LIB = '/home/g/Desktop/squashfs-root/usr/lib/'

sys.path.append(FREECAD_LIB)
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui

from typing import Any, Callable, List

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


def create_traverse_document_tree(on_document_change: Callable) -> Callable:
    def traverse_document_tree(obj: object, path: list) -> None:
        parent = None if len(path) == 0 else path[-1]
        current_document = obj.Document.Name
        previous_document = None if not parent else parent.Document.Name
        did_document_change = current_document != previous_document
        if parent and did_document_change:
            on_document_change(parent.Document, obj.Document)
    return traverse_document_tree


def print_document_tree(obj: object) -> None:
    lines = set()
    def handle_document_change(parent_document, current_document):
        lines.add(parent_document.Name + ' -> ' + current_document.Name)
    traverse_document_tree = create_traverse_document_tree(handle_document_change)
    traverse([obj], traverse_document_tree)
    spacing = '    '
    head = 'digraph DocumentTree {\n' + \
    spacing + 'rankdir=LR;\n' + \
    spacing + 'labelloc=b;\n' + \
    spacing + 'fontsize=32;\n' + \
    spacing + 'label="Document Tree";\n'
    body = spacing + ('\n' + spacing).join(lines)
    tail = '\n}\n'
    print(head + body + tail)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Print Graphviz tree diagram of assembly.')
    parser.add_argument('document_path', help='Path to FreeCAD document.')
    args = parser.parse_args()
    document = App.openDocument(args.document_path)
    root_objects = [obj for obj in document.Objects if obj.Label == document.Name]
    if len(root_objects) > 0:
        root_object = root_objects[0]
        print_document_tree(root_object)
    exit(0)
