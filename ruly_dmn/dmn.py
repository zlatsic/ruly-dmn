from frozendict import frozendict
import json
import xml.etree.ElementTree
import uuid

import ruly


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


def parse(dmn_path, dump_path=None):
    dmn_tree = DMN()

    dmn_tree._xml_element_tree = xml.etree.ElementTree.parse(dmn_path)
    dmn_tree._parse_dmn()
    dmn_tree._dump_path = dump_path

    return dmn_tree


class DMN:

    @property
    def inputs(self):
        return self._knowledge_base.input_variables

    def decide(self, inputs, decision):
        rules = list(self._knowledge_base.rules)

        def post_eval_cb(state, output_name, fired_rules, missing_inputs):
            outputs = [output_names for output_names in self._deps
                       if output_name in output_names][0]
            if _show_rule_prompt(fired_rules, state, self._deps[outputs]):
                input_values = {name: value for name, value in state.items()
                                if name in self._deps[outputs]}
                new_rule = _create_rule_prompt(state, outputs, input_values)
                if new_rule is not None:
                    if len(fired_rules) == 0:
                        rules.append(new_rule)
                    else:
                        rules.insert(rules.index(fired_rules[0]), new_rule)
                    raise _CancelEvaluationException()
            else:
                state = dict(state, **fired_rules[0].consequent)
            return state

        state = None
        rule_count = len(rules)
        rules_changed = False
        while state is None:
            try:
                state = ruly.backward_chain(self._knowledge_base, decision,
                                            post_eval_cb=post_eval_cb,
                                            **inputs)
            except _CancelEvaluationException:
                if len(rules) == rule_count:
                    break
                else:
                    rules_changed = True
                    self._knowledge_base = ruly.KnowledgeBase(*rules)

        if rules_changed:
            self._update_dmn()

        return state[decision]

    def _parse_dmn(self):
        root = self._xml_element_tree.getroot()
        rules = []
        deps = {}
        rule_ids = {}
        for decision in root.findall(_tags['decision']):
            table = decision.find(_tags['decisionTable'])
            inputs = [e.find(_tags['inputExpression']).find(_tags['text']).text
                      for e in table.findall(_tags['input'])]
            outputs = [e.get('name') for e in table.findall(_tags['output'])]
            deps[tuple(outputs)] = inputs
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
        self._deps = deps
        self._knowledge_base = ruly.KnowledgeBase(*rules)
        self._rule_ids = rule_ids

    def _update_dmn(self):
        root = self._xml_element_tree.getroot()
        for decision in root.findall(_tags['decision']):
            table = decision.find(_tags['decisionTable'])
            inputs = [e.find(_tags['inputExpression']).find(_tags['text']).text
                      for e in table.findall(_tags['input'])]
            outputs = [e.get('name') for e in table.findall(_tags['output'])]
            rules = [rule for rule in self._knowledge_base.rules
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
                if elem is None:
                    table.append(rule_element)
                else:
                    table.insert(elem[0], rule_element)
        if self._dump_path is not None:
            self._xml_element_tree.write(self._dump_path)


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


class _CancelEvaluationException(Exception):
    pass


def _show_rule_prompt(fired_rules, state, dependencies):
    available_deps = {d for d in dependencies if state[d] is not None}
    for rule in fired_rules:
        rule_deps = set(ruly.get_rule_depending_variables(rule))
        if (rule_deps & available_deps) == available_deps:
            return False
    return True


def _create_rule_prompt(state, output_names, input_values):
    answer = input(f'Unable to decide {output_names} for inputs '
                   f'{input_values}, generate new rule? (Y/n)').lower()
    answer = answer or 'y'
    while answer not in ('y', 'n'):
        answer = input('Please type y or n.').lower()
    if answer == 'n':
        return None
    antecedent = ruly.Expression(
        ruly.Operator.AND, tuple(ruly.EqualsCondition(name, value)
                                 for name, value in input_values.items()
                                 if value is not None))
    print('Please type the expected output value (JSON)')
    print(f'IF {antecedent} THEN')
    assignments = {}
    for output_name in output_names:
        value = None
        while value is None:
            value_json = input(f'{output_name} = ')
            try:
                value = json.loads(value_json)
            except json.JSONDecodeError:
                print('Invalid JSON string, please try again')
        assignments[output_name] = value
    return ruly.Rule(antecedent, frozendict(assignments))
