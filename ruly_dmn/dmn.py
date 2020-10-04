from frozendict import frozendict
import json
import ruly

from ruly_dmn import common


class DMN:
    """Class that contains the DMN implementation.

    Args:
        handler (ruly_dmn.common.ModelHandler): model handler
        rule_factory_cb (Optional[Callable[[ruly_dmn.common.ModelHandler],
                                           ruly_dmn.common.RuleFactory])]:
            function that creates a rule factory - if None, a factory that uses
            console is used"""

    def __init__(self, handler, rule_factory_cb=None):
        self._handler = handler
        self._knowledge_base = ruly.KnowledgeBase(*handler.rules)
        self._factory_cb = rule_factory_cb

    @property
    def inputs(self):
        """List[str]: input variables for all available decisions"""
        return self._knowledge_base.input_variables

    def decide(self, inputs, decision):
        """Attempts to solve for decision based on given inputs. In some cases
        it might create new rules.

        Args:
            inputs (Dict[str, Any]): name-value pairs of all inputs
            decision (str): name of the decision that should be resolved

        Returns:
            Any: calculated decision"""
        rules = list(self._knowledge_base.rules)
        if self._factory_cb is None:
            rule_factory = _ConsoleRuleFactory(self._handler)
        else:
            rule_factory = self._factory_cb(self._handler)

        def post_eval_cb(state, output_name, fired_rules):
            outputs = [output_names
                       for output_names in self._handler.dependencies
                       if output_name in output_names][0]

            new_rule = rule_factory.create_rule(state, fired_rules, outputs)
            if new_rule is not None:
                if len(fired_rules) == 0:
                    rules.append(new_rule)
                else:
                    rules.insert(rules.index(fired_rules[0]), new_rule)
                raise _CancelEvaluationException()
            elif len(fired_rules) > 0:
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
            self._handler.update(self._knowledge_base)

        return state[decision]


class _ConsoleRuleFactory(common.RuleFactory):

    def __init__(self, handler):
        self._rejections = []
        self._dependencies = handler.dependencies

    def create_rule(self, state, fired_rules, output_names):
        input_names = self._dependencies[output_names]
        input_values = {name: state[name] for name in input_names
                        if state[name] is not None}
        if (input_values, output_names) in self._rejections:
            return None
        if not self._show_prompts(fired_rules, state, input_names):
            return None
        if len(fired_rules) == 0:
            question = (f'Unable to decide {output_names} for inputs '
                        f'{input_values}, generate new rule?')
        else:
            question = (f'Fired rules for {output_names} did not use all '
                        f'available input decisions - {input_values}, would '
                        f'you like to create a new rule that does?')
        if not self._confirm_creation(question):
            self._rejections.append((input_values, output_names))
            return None

        rule = self._create_prompt(input_values, output_names)
        print('Created rule:', rule)
        return rule

    def _show_prompts(self, fired_rules, state, input_names):
        available_inputs = {name for name in input_names
                            if state[name] is not None}
        for rule in fired_rules:
            rule_deps = set(ruly.get_rule_depending_variables(rule))
            if (rule_deps & available_inputs) == available_inputs:
                return False
        return True

    def _confirm_creation(self, question):
        answer = input(f'{question} (Y/n) ').lower() or 'y'
        while answer not in ('y', 'n'):
            answer = input('Please type y or n. (Y/n)').lower() or 'y'
        if answer == 'n':
            return False
        return True

    def _create_prompt(self, input_values, output_names):
        antecedent = ruly.Expression(
            ruly.Operator.AND, tuple(ruly.EqualsCondition(name, value)
                                     for name, value in input_values.items()
                                     if value is not None))
        print('Please type the expected output values (JSON)')
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


class _CancelEvaluationException(Exception):
    pass
