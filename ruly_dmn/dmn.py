import itertools
import json
import ruly

from ruly_dmn import common


class DMN:
    """Class that contains the DMN implementation.

    Args:
        handler (ruly_dmn.ModelHandler): model handler
        rule_factory_cb (Optional[Callable]): function that creates a rule
            factory - if None, a factory that uses console is used. Signature
            should match the signature of :func:`ruly_dmn.rule_factory_cb`"""

    def __init__(self, handler, rule_factory_cb=None):
        self._handler = handler
        self._knowledge_base = ruly.KnowledgeBase(*handler.rules)
        self._factory_cb = rule_factory_cb

        all_outputs = set(itertools.chain(*handler.dependencies.keys()))
        all_inputs = set(itertools.chain(*handler.dependencies.values()))
        self._inputs = all_inputs - all_outputs

    @property
    def inputs(self):
        """List[str]: input variables for all available decisions"""
        return self._inputs

    def decide(self, inputs, decision):
        """Attempts to solve for decision based on given inputs. May create
        new rules if the factory creates them.

        Args:
            inputs (Dict[str, Any]): name-value pairs of all inputs
            decision (str): name of the decision that should be resolved

        Returns:
            Any: calculated decision

        Raises:
            ruly_dmn.HitPolicyViolation: raised if hit policy violation is
            detected"""
        rules = list(self._knowledge_base.rules)
        if self._factory_cb is None:
            rule_factory = _ConsoleRuleFactory(self._handler)
        else:
            rule_factory = self._factory_cb(self._handler)

        def post_eval_cb(state, output_name, fired_rules):
            fired_rules = _resolve_hit_policy(
                fired_rules, self._handler.hit_policies[output_name])
            new_rule = rule_factory.create_rule(state, fired_rules,
                                                output_name)
            if new_rule is not None and new_rule not in rules:
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


def rule_factory_cb(handler):
    """Placeholder function containing the signature for rule factory callbacks

    Args:
        handler (ruly_dmn.ModelHandler): model handler

    Returns:
        ruly_dmn.RuleFactory: rule factory"""


class HitPolicyViolation(Exception):
    """Exception raised when a hit policy is violated"""


class _ConsoleRuleFactory(common.RuleFactory):

    def __init__(self, handler):
        self._rejections = []
        self._handler = handler

    def create_rule(self, state, fired_rules, output_name):
        input_names = self._handler.dependencies[output_name]
        input_values = {name: state[name] for name in input_names
                        if state[name] is not None}
        if (input_values, output_name) in self._rejections:
            return None
        if not self._show_prompts(fired_rules, state, input_names):
            return None
        if len(fired_rules) == 0:
            question = (f'Unable to decide {output_name} for inputs '
                        f'{input_values}, generate new rule?')
        else:
            question = (f'Fired rules for {output_name} did not use all '
                        f'available input decisions - {input_values}, would '
                        f'you like to create a new rule that does?')
        if not self._confirm_creation(question):
            self._rejections.append((input_values, output_name))
            return None

        rule = self._create_prompt(input_values, output_name)
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

    def _create_prompt(self, input_values, output_name):
        antecedent = ruly.Expression(
            ruly.Operator.AND, tuple(ruly.EqualsCondition(name, value)
                                     for name, value in input_values.items()
                                     if value is not None))
        print('Please type the expected output values (JSON)')
        print(f'IF {antecedent} THEN')
        assignments = {}
        value = None
        while value is None:
            value_json = input(f'{output_name} = ')
            try:
                value = json.loads(value_json)
            except json.JSONDecodeError:
                answer = input(f'JSON parsing failed, is the expected value '
                               f'string "{value_json}"? (Y/n)') or 'y'
                if answer == 'n':
                    continue
                else:
                    value = value_json
                    break
        assignments[output_name] = value
        return ruly.Rule(antecedent, assignments)


class _CancelEvaluationException(Exception):
    pass


def _resolve_hit_policy(fired_rules, hit_policy):
    if hit_policy == common.HitPolicy.UNIQUE:
        if len(fired_rules) > 1:
            raise HitPolicyViolation(f'multiple rules fired for a decision '
                                     f'with unique hit policy: {fired_rules}')
        return fired_rules
    if hit_policy == common.HitPolicy.FIRST:
        return [fired_rules[0]] if len(fired_rules) > 0 else []
    if hit_policy == common.HitPolicy.ANY:
        if not all(r.consequent == fired_rules[0].consequent
                   for r in fired_rules):
            raise HitPolicyViolation(f'rules with different outputs '
                                     f'satisfied, while hit policy is any: '
                                     f'{fired_rules}')
        return [fired_rules[0]]
