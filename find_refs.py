import argparse
import glob
import re
import zipfile
from typing import Callable, Dict, List
from xml.etree import ElementTree
from xml.etree.ElementTree import Element


class Reference:
    """Represents a reference to an alias of a spreadsheet in another document."""

    def __init__(self,
                 document: str,
                 spreadsheet: str,
                 alias: str) -> None:
        self.document = document
        self.spreadsheet = spreadsheet
        self.alias = alias

    def __str__(self):
        return self._to_string()

    def __repr__(self):
        return self._to_string()

    def _to_string(self):
        return '{}#{}.{}'.format(self.document, self.spreadsheet, self.alias)


class Match:
    """Represents a match to a reference."""

    def __init__(self,
                 document: str,
                 object_name: str,
                 property_name: str,
                 location: str) -> None:
        self.document = document
        self.object_name = object_name
        self.property_name = property_name
        self.location = location

    def __str__(self):
        return self._to_string()

    def __repr__(self):
        return self._to_string()

    def _to_string(self):
        return '{}#{}.{} {}'.format(self.document, self.object_name, self.property_name, self.location)


def parse_document_xml(document: str) -> Element:
    archive = zipfile.ZipFile(document, 'r')
    document_xml = archive.read('Document.xml')
    return ElementTree.fromstring(document_xml)


def find_root_by_document() -> Dict[str, Element]:
    """Returns a dictionary where keys are document names,
    and values are document xml root elements.
    """
    root_by_document = {}
    documents = glob.glob('*.FCStd')
    for document in documents:
        root = parse_document_xml(document)
        root_by_document[document] = root
    return root_by_document


def make_find_references_in_property(child_element_name: str,
                                     reference_attribute: str,
                                     location_attribute: str,
                                     reference: Reference) -> Callable[[Element], List[str]]:
    """
    XML Examples::

       <Cell address="B1" content="=Main#Spreadsheet.Value" alias="Value1" />
       <Expression path="Radius" expression="Main#Spreadsheet.Value"/>

    +--------------------+---------------------+--------------------+
    | child_element_name | reference_attribute | location_attribute |
    +====================+=====================+====================+
    | Cell               | content             | address            |
    +--------------------+---------------------+--------------------+
    | Expression         | expression          | path               |
    +--------------------+---------------------+--------------------+
    """
    def find_references_in_property(property: Element) -> List[str]:
        locations = []
        for child_element in property.findall(child_element_name):
            content = child_element.attrib[reference_attribute]
            pattern = re.compile(str(reference))
            match = pattern.search(content)
            if match:
                locations.append(child_element.attrib[location_attribute])
        return locations
    return find_references_in_property


def make_find_references_in_cells(reference: Reference) -> Callable[[Element], List[str]]:
    return make_find_references_in_property('Cell',
                                            'content',
                                            'address',
                                            reference)


def make_find_references_in_expression_engine(reference: Reference) -> Callable[[Element], List[str]]:
    return make_find_references_in_property('Expression',
                                            'expression',
                                            'path',
                                            reference)


def find_references_in_root(document: str, root: Element, reference: Reference) -> List[Match]:
    matches = []
    object_data = root.find('ObjectData')
    for object in object_data:
        properties = object.find('Properties')
        object_name = object.attrib['name']

        for property in properties.findall('Property'):
            property_name = property.attrib['name']
            find_locations = make_find_locations(property)
            locations = find_locations(reference)
            for location in locations:
                matches.append(
                    Match(document, object_name, property_name, location))
    return matches


class Property:
    """Represents a property with a potential reference."""

    def __init__(self,
                 property_element: Element,
                 nested_element_name: str,
                 make_find_references: Callable[[Reference], Callable[[Element], List[str]]]) -> None:
        self.property_element = property_element
        self.nested_element_name = nested_element_name
        self.make_find_references = make_find_references

    def find_locations(self, reference: Reference) -> List[str]:
        find_references = self.make_find_references(reference)
        nested_element = self.property_element.find(self.nested_element_name)
        return find_references(nested_element)


def make_find_locations(property_element: Element) -> Callable[[Reference], List[str]]:
    def find_locations(reference: Reference) -> List[str]:
        property_name = property_element.attrib['name']
        properties_with_references = {'cells', 'ExpressionEngine'}
        if property_name in properties_with_references:
            property = create_property(property_element)
            return property.find_locations(reference)
        else:
            return []
    return find_locations


def create_property(property_element: Element) -> Property:
    """
    XML Examples::

        <Property name="cells" type="Spreadsheet::PropertySheet" status="67108864">
            <Cells Count="4" xlink="1">
                ...
            </Cells>
        </Property>
        <Property name="ExpressionEngine" type="App::PropertyExpressionEngine" status="67108864">
            <ExpressionEngine count="2" xlink="1">
                ...
            </ExpressionEngine>
        </Property>

    +--------------------+---------------------+
    | property_name      | nested_element_name |
    +====================+=====================+
    | cells              | Cells               |
    +--------------------+---------------------+
    | ExpressionEngine   | ExpressionEngine    |
    +--------------------+---------------------+
    """
    property_name = property_element.attrib['name']
    if property_name == 'cells':
        return Property(property_element, 'Cells', make_find_references_in_cells)
    elif property_name == 'ExpressionEngine':
        return Property(property_element, 'ExpressionEngine', make_find_references_in_expression_engine)
    return None


def find_refs(document: str, spreadsheet: str, alias: str) -> List[Match]:
    matches = []
    root_by_document = find_root_by_document()
    for document_name, root in root_by_document.items():
        ref = Reference(document, spreadsheet, alias)
        matches_in_doc = find_references_in_root(document_name, root, ref)
        matches.extend(matches_in_doc)
    return matches


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Find cross-document spreadsheet references.')
    parser.add_argument(
        'document', help='Document where spreadsheet is located.')
    parser.add_argument('spreadsheet', help='Spreadsheet name or label.')
    parser.add_argument('alias', help='Alias name.')
    args = parser.parse_args()
    matches = find_refs(args.document, args.spreadsheet, args.alias)
    print('\n'.join(map(str, matches)))
