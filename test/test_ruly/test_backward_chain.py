from bc_dmn import ruly


def test_backward_chain():
    kb = ruly.knowledge_base.create([
        ruly.Rule(
            antecedent=ruly.Expression(
                operator=ruly.Operator.AND,
                children=[
                    ruly.EqualsCondition(name='sound', value='croak'),
                    ruly.EqualsCondition(name='behavior', value='eats flies')
                ]),
            consequent=ruly.Assignment(name='animal', value='frog')),
        ruly.Rule(
            antecedent=ruly.Expression(
                operator=ruly.Operator.AND,
                children=[
                    ruly.EqualsCondition(name='sound', value='chirp'),
                    ruly.EqualsCondition(name='behavior', value='sings')
                ]),
            consequent=ruly.Assignment(name='animal', value='canary')),
        ruly.Rule(antecedent=ruly.EqualsCondition(name='animal', value='frog'),
                  consequent=ruly.Assignment(name='color', value='green')),
        ruly.Rule(
            antecedent=ruly.EqualsCondition(name='animal', value='canary'),
            consequent=ruly.Assignment(name='color', value='yellow'))])

    color = ruly.backward_chain(kb, 'color', sound='croak',
                                behavior='eats flies')
    assert color == 'green'

    color = ruly.backward_chain(kb, 'color', sound='chirp', behavior='sings')
    assert color == 'yellow'
