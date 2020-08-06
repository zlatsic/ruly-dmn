import json
import xml.etree.ElementTree

from bc_dmn import ruly


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


def parse(dmn_path):
    dmn_tree = DMN()

    dmn_tree._xml_element_tree = xml.etree.ElementTree.parse(dmn_path)
    root = dmn_tree._xml_element_tree.getroot()
    dmn_tree._knowledge_base = _parse_knowledge_base(root)

    return dmn_tree


class DMN:

    @property
    def inputs(self):
        return self._knowledge_base.input_variables

    def decide(self, inputs, decision):
        return ruly.backward_chain(self._knowledge_base, decision, **inputs)


def _parse_knowledge_base(root):
    rules = []
    for decision in root.findall(_tags['decision']):
        table = decision.find(_tags['decisionTable'])
        inputs = [e.find(_tags['inputExpression']).find(_tags['text']).text
                  for e in table.findall(_tags['input'])]
        outputs = [e.get('name') for e in table.findall(_tags['output'])]
        for rule_element in table.findall(_tags['rule']):
            input_values = [
                e.find(_tags['text']).text
                for e in rule_element.findall(_tags['inputEntry'])]
            antecedent = ruly.Expression(
                ruly.Operator.AND,
                [ruly.EqualsCondition(input_name, json.loads(value))
                 for input_name, value in zip(inputs, input_values)
                 if value is not None])

            output_values = [
                json.loads(e.find(_tags['text']).text)
                for e in rule_element.findall(_tags['outputEntry'])]
            rules.extend([ruly.Rule(antecedent, ruly.Assignment(output, value))
                          for output, value in zip(outputs, output_values)])
    return ruly.knowledge_base.create(rules)
