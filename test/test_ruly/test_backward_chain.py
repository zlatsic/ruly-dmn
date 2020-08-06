from bc_dmn import ruly


def test_backward_chain():
    kb = ruly.knowledge_base.create([
        ruly.Rule(
            ruly.Expression(
                operator=ruly.Operator.AND,
                children=[
                    ruly.EqualsCondition(name='sound', value='croak'),
                    ruly.EqualsCondition(name='behavior', value='eats flies')
                ]),
            ruly.Assignment(name='animal', value='frog')),
        ruly.Rule(
            ruly.Expression(
                operator=ruly.Operator.AND,
                children=[
                    ruly.EqualsCondition(name='sound', value='chirp'),
                    ruly.EqualsCondition(name='behavior', value='sings')
                ]),
            ruly.Assignment(name='animal', value='canary')),
        ruly.Rule(ruly.EqualsCondition(name='animal', value='frog'),
                  ruly.Assignment(name='color', value='green')),
        ruly.Rule(ruly.EqualsCondition(name='animal', value='canary'),
                  ruly.Assignment(name='color', value='yellow'))])

    state = ruly.backward_chain(kb, 'color', sound='croak',
                                behavior='eats flies')
    assert state['color'] == 'green'

    state = ruly.backward_chain(kb, 'color', sound='chirp', behavior='sings')
    assert state['color'] == 'yellow'
