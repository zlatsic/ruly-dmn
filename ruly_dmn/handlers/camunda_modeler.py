from frozendict import frozendict
import json
import ruly
import uuid
import xml.etree.ElementTree

from ruly_dmn import common


_tags = {
    'decision': '{https://www.omg.org/spec/DMN/20191111/MODEL/}decision',
    'decisionTable': '{https://www.omg.org/spec/DMN/20191111/MODEL/}'
                     'decisionTable',
    'input': '{https://www.omg.org/spec/DMN/20191111/MODEL/}input',
    'output': '{https://www.omg.org/spec/DMN/20191111/MODEL/}output',
    'rule': '{https://www.omg.org/spec/DMN/20191111/MODEL/}rule',
    'inputExpression': '{https://www.omg.org/spec/DMN/20191111/MODEL/}'
                       'inputExpression',
    'inputValues': '{https://www.omg.org/spec/DMN/20191111/MODEL/}inputValues',
    'text': '{https://www.omg.org/spec/DMN/20191111/MODEL/}text',
    'inputEntry': '{https://www.omg.org/spec/DMN/20191111/MODEL/}inputEntry',
    'outputEntry': '{https://www.omg.org/spec/DMN/20191111/MODEL/}outputEntry'}


class CamundaModelerHandler(common.ModelHandler):
    """Implementation of the handler that expects a Camunda Modeler DMN file

    Args:
        path (pathlib.Path): path to the DMN file
        dump_path (Optional[pathlib.Path]): path where updated DMN files will
            be dumped. Can be the same as path. If None, they aren't dumped
            anywhere"""

    def __init__(self, path, dump_path=None):
        self._dump_path = dump_path
        tree = xml.etree.ElementTree.parse(path)
        root = tree.getroot()
        rules = []
        dependencies = {}
        rule_ids = {}
        for decision in root.findall(_tags['decision']):
            table = decision.find(_tags['decisionTable'])
            inputs = [e.find(_tags['inputExpression']).find(_tags['text']).text
                      for e in table.findall(_tags['input'])]
            outputs = [e.get('name') for e in table.findall(_tags['output'])]
            dependencies[tuple(outputs)] = inputs
            for rule_element in table.findall(_tags['rule']):
                input_values = [
                    e.find(_tags['text']).text
                    for e in rule_element.findall(_tags['inputEntry'])]
                antecedent = ruly.Expression(
                    ruly.Operator.AND,
                    tuple(ruly.EqualsCondition(input_name, json.loads(value))
                          for input_name, value in zip(inputs, input_values)
                          if value is not None))

                output_values = [
                    json.loads(e.find(_tags['text']).text)
                    for e in rule_element.findall(_tags['outputEntry'])]
                rule = ruly.Rule(antecedent,
                                 frozendict({output: value for output, value
                                             in zip(outputs, output_values)}))
                rules.append(rule)
                rule_ids[rule] = rule_element.attrib['id']
        self._tree = tree
        self._dependencies = dependencies
        self._rule_ids = rule_ids
        self._rules = list(rule_ids)

    @property
    def dependencies(self):
        return self._dependencies

    @property
    def rules(self):
        return self._rules

    def update(self, knowledge_base):
        root = self._tree.getroot()
        for decision in root.findall(_tags['decision']):
            table = decision.find(_tags['decisionTable'])
            inputs = [e.find(_tags['inputExpression']).find(_tags['text']).text
                      for e in table.findall(_tags['input'])]
            outputs = [e.get('name') for e in table.findall(_tags['output'])]
            rules = [rule for rule in knowledge_base.rules
                     if set(rule.consequent) == set(outputs)]
            rule_index_elem_iter = ((i, el) for i, el in
                                    enumerate(table.getchildren())
                                    if el.tag == _tags['rule'])
            elem = None
            for rule in rules:
                if elem is None:
                    try:
                        elem = next(rule_index_elem_iter)
                    except StopIteration:
                        elem = None
                rule_id = self._rule_ids.get(rule)
                if rule_id is not None:
                    elem = None
                    continue
                rule_element = _rule_to_xml_element(rule, inputs, outputs)
                self._rule_ids[rule] = rule_element.attrib['id']
                if elem is None:
                    table.append(rule_element)
                else:
                    table.insert(elem[0], rule_element)
        if self._dump_path is not None:
            self._tree.write(self._dump_path)


def _rule_to_xml_element(rule, inputs, outputs):
    element = xml.etree.ElementTree.Element(
        _tags['rule'],
        attrib={'id': f'DecisionRule_{uuid.uuid1()}'})
    for input_name in inputs:
        condition = [c for c in rule.antecedent.children
                     if c.name == input_name]
        input_entry_element = xml.etree.ElementTree.Element(
            _tags['inputEntry'],
            attrib={'id': f'UnaryTests_{uuid.uuid1()}'})
        text_element = xml.etree.ElementTree.Element(_tags['text'])
        if len(condition) == 1:
            text_element.text = json.dumps(condition[0].value)
        input_entry_element.append(text_element)
        element.append(input_entry_element)
    for output_name in outputs:
        output_entry_element = xml.etree.ElementTree.Element(
            _tags['outputEntry'],
            attrib={'id': f'LiteralExpression_{uuid.uuid1()}'})
        text_element = xml.etree.ElementTree.Element(_tags['text'])
        text_element.text = json.dumps(rule.consequent[output_name])
        output_entry_element.append(text_element)
        element.append(output_entry_element)
    return element