from bc_dmn.ruly import common


def backward_chain(knowledge_base, output_name, **kwargs):
    """Evaulates the output using backward chaining

    Args:
        knowledge_base (bc_dmn.ruly.KnowledgeBase): knowledge base
        output_name (str): name of the output variable
        kwargs: names and values of input variables

    Returns:
        Any: evaluated value of the goal variable"""
    state = {
        name: kwargs.get(name)
        for name in knowledge_base.input_variables.union(
            knowledge_base.derived_variables)}
    for rule in knowledge_base.rules:
        if rule.consequent.name != output_name:
            continue
        for variable in common.get_rule_input_variables(rule):
            if state[variable] is None:
                if variable in knowledge_base.input_variables:
                    # TODO handle missing inputs
                    break
                state[variable] = backward_chain(knowledge_base, variable,
                                                 **state)
        if evaluate(state, rule.antecedent):
            return rule.consequent.value

    return None


def evaluate(inputs, antecedent):
    """Evaluates an antecedent

    Args:
        inputs (Dict[str, Any]): variable values
        antecedent (Union[bc_dmn.ruly.Expression, bc_dmn.ruly.Condition]): rule
            antecedent
    Returns:
        bool"""
    if isinstance(antecedent, common.Condition):
        return _evaluate_condition(antecedent, inputs[antecedent.name])
    elif isinstance(antecedent, common.Expression):
        return _evaluate_expression(antecedent, inputs)


def _evaluate_expression(expression, inputs):
    if expression.operator == common.Operator.AND:
        return all([evaluate(inputs, child) for child in expression.children])


def _evaluate_condition(condition, input_value):
    if isinstance(condition, common.EqualsCondition):
        return condition.value == input_value
