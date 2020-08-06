from bc_dmn.ruly import common


def create(rules):
    """Creates a knowledge base

    Args:
        rules (List[ruly.Rule): initial rules of which the knowledge base
            consists

    Returns:
        KnowledgeBase"""  # NOQA

    base = KnowledgeBase()
    base._rules = []
    base._input_variables = set()
    base._derived_variables = set()

    for rule in rules:
        base.add_rule(rule)

    return base


class KnowledgeBase:

    @property
    def rules(self):
        """Rules

        Returns:
            List[ruly.Rule]"""
        return self._rules

    @property
    def input_variables(self):
        """Names of variables that are never contained within a rule's
        antecedent

        Returns:
            Set[str]"""
        return self._input_variables

    @property
    def derived_variables(self):
        """Names of variables contained within at least one rule's antecedent

        Returns:
            Set[str]"""
        return self._derived_variables

    def add_rule(self, rule):
        """Add a new rule to the knowledge base. This can change which variables
        are considered input or derived"""
        self._rules.append(rule)
        self._input_variables.update(common.get_rule_input_variables(rule))
        self._derived_variables.add(rule.consequent.name)
        self._input_variables -= self._derived_variables
