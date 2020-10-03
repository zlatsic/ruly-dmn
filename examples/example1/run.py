from ruly_dmn import dmn


d = dmn.parse('./diagram.dmn')
inputs = {'Season': 'new season'}

try:
    print(d.decide(inputs, 'Beverage'))
except Exception as e:
    import pdb; pdb.post_mortem()
    breakpoint()
    pass
