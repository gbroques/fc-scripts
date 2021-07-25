import argparse
import glob
import re
import zipfile
from typing import Callable, Dict, List
from xml.etree import ElementTree
from xml.etree.ElementTree import Element


class Reference:
    """Represents a reference to the property of an object in another document."""

    def __init__(self,
                 document: str,
                 object_name: str,
                 property_name: str) -> None:
        self.document = document
        self.object_name = object_name
        self.property_name = property_name

    def __str__(self):
        return self._to_string()

    def __repr__(self):
        return self._to_string()

    def _to_string(self):
        return '{}#{}.{}'.format(self.document, self.object_name, self.property_name)


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
        return '{} {}.{} ({})'.format(
            self.document,
            self.object_name,
            self.location,
            self.property_name)


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

    FreeCAD Source:
    * `Property <https://github.com/FreeCAD/FreeCAD/blob/0.19.2/src/App/PropertyContainer.cpp#L221-L310>`_
    * `Cells <https://github.com/FreeCAD/FreeCAD/blob/0.19.2/src/Mod/Spreadsheet/App/PropertySheet.cpp#L277-L304>`_
    * `Expression Engine <https://github.com/FreeCAD/FreeCAD/blob/0.19.2/src/App/PropertyExpressionEngine.cpp#L163-L185>`_
    """
    property_name = property_element.attrib['name']
    if property_name == 'cells':
        return Property(property_element, 'Cells', make_find_references_in_cells)
    elif property_name == 'ExpressionEngine':
        return Property(property_element, 'ExpressionEngine', make_find_references_in_expression_engine)
    return None


def find_references(reference: Reference) -> List[Match]:
    matches = []
    root_by_document = find_root_by_document()
    for document, root in root_by_document.items():
        matches_in_document = find_references_in_root(document, root, reference)
        matches.extend(matches_in_document)
    return matches


def rename_references(from_reference: Reference,
                      to_reference: Reference) -> Dict[str, Element]:
    """
    TODO: 1) Find from document
             If not label (not surrounded by << >>),
               Find file named 'XXX.FCStd'.
             Else
               Go through every document looking for the one wit the label
          
          2) Then find object with name or label.

                <Object name="Spreadsheet">
                    <Properties Count="7" TransientCount="0">
                    <Property name="Label" type="App::PropertyString" status="134217728">
                        <String value="Spreadsheet"/>
                    </Property>
          
          3) Then find cell with alias.

                <Property name="cells" type="Spreadsheet::PropertySheet" status="67108864">
                    <Cells Count="2" xlink="1">
                        <XLinks count="0">
                        </XLinks>
                        <Cell address="A1" content="Test" />
                        <Cell address="B1" content="5" alias="Test" />
                    </Cells>
                </Property>
          
          4) Output new XML depending upon to_reference (change alias, spreadsheet name or label).
    """
    pass


def remove_external_links(document: str) -> Dict[str, Element]:
    """
    https://github.com/FreeCAD/FreeCAD/blob/0.19.2/src/App/PropertyLinks.cpp#L4473-L4510
    https://github.com/FreeCAD/FreeCAD/blob/0.19.2/src/App/PropertyLinks.cpp#L3155-L3249

    EMPTY
    =====
    <Cells Count="2" xlink="1">
        <XLinks count="0">
        </XLinks>
        <Cell address="A1" content="Test" />
        <Cell address="B1" content="5" alias="Test" />
    </Cells>
    <Property name="ExpressionEngine" type="App::PropertyExpressionEngine" status="67108864">
        <ExpressionEngine count="0">
        </ExpressionEngine>
    </Property>

    XLINKS
    ======
    <Cells Count="4" xlink="1">
        <XLinks count="1" docs="1">
            <DocMap name="Master" label="Master" index="0"/>
            <XLink file="Master.FCStd" stamp="2021-07-25T18:40:15Z" name="Spreadsheet"/>
        </XLinks>
        <Cell address="A1" content="Value" />
        <Cell address="B1" content="=Master#Spreadsheet.Value" alias="Value1" />
        <Cell address="D8" content="Value" />
        <Cell address="E8" content="=&lt;&lt;Master&gt;&gt;#&lt;&lt;Spreadsheet&gt;&gt;.Value" alias="Value2" />
    </Cells>
    <ExpressionEngine count="2" xlink="1">
        <XLinks count="2" docs="2">
            <DocMap name="Master" label="Master" index="1"/>
            <DocMap name="Cube" label="Cube" index="0"/>
            <XLink file="Cube.FCStd" stamp="2021-07-25T20:03:03Z" name="Box"/>
            <XLink file="Master.FCStd" stamp="2021-07-25T18:40:15Z" name="Spreadsheet"/>
        </XLinks>
        <Expression path="Height" expression="Cube#Box.Height"/>
        <Expression path="Radius" expression="Master#Spreadsheet.Value"/>
    </ExpressionEngine>
    """
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Find cross-document spreadsheet references.')
    parser.add_argument(
        'document', help='Document where spreadsheet is located.')
    parser.add_argument('spreadsheet', help='Spreadsheet name or label.')
    parser.add_argument('alias', help='Alias name.')
    args = parser.parse_args()
    ref = Reference(args.document, args.spreadsheet, args.alias)
    matches = find_references(ref)
    if matches:
        num_matches = len(matches)
        word = 'refrence' if num_matches == 1 else 'references'
        print('{} {} to {} found:'.format(num_matches, word, ref))
        print('  ' + '\n  '.join(map(str, matches)))
    else:
        print('No references to {} found.'.format(ref))
