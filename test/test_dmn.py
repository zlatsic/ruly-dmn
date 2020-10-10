import pytest
import ruly

import ruly_dmn.common
import ruly_dmn.dmn


class MockModelHandler(ruly_dmn.common.ModelHandler):

    def __init__(self, dependencies={}, hit_policies={}, rules=[],
                 update_fn=None):
        self._dependencies = dependencies
        self._hit_policies = hit_policies
        self._rules = rules
        self._update_fn = update_fn

    @property
    def dependencies(self):
        return self._dependencies

    @property
    def hit_policies(self):
        return self._hit_policies

    @property
    def rules(self):
        return self._rules

    def update(self, knowledge_base):
        if self._update_fn is not None:
            return self._update_fn(knowledge_base)


class MockRuleFactory(ruly_dmn.common.RuleFactory):

    def __init__(self, create_rule_fn=None):
        self._create_rule_fn = create_rule_fn

    def create_rule(self, state, fired_rules, output_names):
        if self._create_rule_fn is not None:
            return self._create_rule_fn(state, fired_rules, output_names)


def test_inputs():
    handler = MockModelHandler({'a': ('c', 'd', 'e'),
                                'e': ('f', 'g')})
    dmn = ruly_dmn.dmn.DMN(handler)
    assert dmn.inputs == {'c', 'd', 'f', 'g'}


@pytest.mark.parametrize('rules,inputs,decision,expected', [
    ([ruly.Rule(ruly.EqualsCondition('x', 1), {'y': 2})], {'x': 1}, 'y', 2),
    ([ruly.Rule(ruly.EqualsCondition('x', 1), {'y': 2}),
      ruly.Rule(ruly.EqualsCondition('y', 2), {'z': 3})], {'x': 1}, 'z', 3),
])
def test_decide(rules, inputs, decision, expected):
    handler = MockModelHandler(hit_policies={k: ruly_dmn.common.HitPolicy.FIRST
                                             for k in ('y', 'z')},
                               rules=rules)
    dmn = ruly_dmn.dmn.DMN(handler, lambda _: MockRuleFactory())
    assert dmn.decide(inputs, decision) == expected


def test_factory_called():
    called = False
    create_args = {}

    new_rule = ruly.Rule(ruly.EqualsCondition('x', 2), {'y': 3})

    def factory_cb(*args):
        nonlocal called
        called = True
        return MockRuleFactory(create_rule_fn)

    def create_rule_fn(state, fired_rules, output_names):
        create_args['state'] = state
        create_args['fired_rules'] = fired_rules
        create_args['output_names'] = output_names
        return new_rule

    rules = [ruly.Rule(ruly.EqualsCondition('x', 1), {'y': 2})]
    dmn = ruly_dmn.dmn.DMN(
        MockModelHandler(rules=rules,
                         hit_policies={'y': ruly_dmn.common.HitPolicy.FIRST}),
        factory_cb)
    dmn.decide({'x': 1}, 'y')
    assert called
    assert create_args == {'state': {'x': 1, 'y': None},
                           'fired_rules': rules,
                           'output_names': 'y'}
    assert dmn._knowledge_base.rules == tuple([new_rule] + rules)
