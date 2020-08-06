from bc_dmn.ruly import common


def backward_chain(knowledge_base, output_name,
                   conflict_resolver=common.fire_first, **kwargs):
    """Evaulates the output using backward chaining

    Args:
        knowledge_base (bc_dmn.ruly.KnowledgeBase): knowledge base
        output_name (str): name of the output variable
        conflict_resolver (Callable[List[bc_dmn.ruly.Rule], Any]): function
            used to determine how value is calculated if multiple rules should
            fire at same variable
        kwargs: names and values of input variables

    Returns:
        Dict[str, Any]: evaluator state, keys are variable names and values are
            their values"""
    state = {
        name: kwargs.get(name)
        for name in knowledge_base.input_variables.union(
            knowledge_base.derived_variables)}
    fired_rules = []
    for rule in knowledge_base.rules:
        if rule.consequent.name != output_name:
            continue
        for variable in common.get_rule_input_variables(rule):
            if state[variable] is None:
                if variable in knowledge_base.input_variables:
                    # TODO handle missing inputs
                    break
                state = backward_chain(knowledge_base, variable, **state)
                if state[variable] is None:
                    # TODO derived variable not calculated, handle this
                    break
        if evaluate(state, rule.antecedent):
            fired_rules.append(rule)

    if fired_rules:
        state[output_name] = conflict_resolver(fired_rules)
    return state


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
