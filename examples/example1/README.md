# Example 1

This example contains a DMN file that describes the decision-making process for
deciding which dish and beverage to serve, depending on season and whether
guests are vegetarians or have children. The file can be viewed with the
[Camunda modeler](https://camunda.com/download/modeler/). After installing
ruly-dmn, this model may be ran by calling:

```bash
ruly-dmn diagram.dmn Beverage Season="Spring"
```

The program should output `Beverage = Pinot Noir`.

If inputs are unrecognized or the fired rules don't use all inputs of their
depending subdecisions, rule creation prompt is displayed to the user. For
instance, if the model is ran by calling:

```bash
ruly-dmn diagram.dmn Beverage Season="fifth season"
```

The program will first warn that the season "fifth season" is not defined in
any of the rules and ask whether user wants to create a new rule with it. If
yes, the program will first ask which dish should be decided (since that is a
dependency of the Beverage decision), and then, again, if user inputed a
previously unseen dish, another question will be asked, which beverage should
be served with that dish.

The prompt also activates in cases where the program recognizes that rules have
fired for a decision, but none of them utilize all the available inputs. For
instance, Dish decision depends on Season and Vegetarian Guests, but all rules
either use only Season or Vegetarian Guests variables, none of them use both.
So if the following command is called:

```bash
ruly-dmn diagram.dmn Dish Season=Summer "Vegetarian Guests"=true
```

The program will warn the user that no Dish rule has used all inputs and ask
whether they would like to create a new rule when Season=Summer AND "Vegetarian
Guests"=true.

Lastly, the previous two examples have both generated new rules, but these
rules would never be reflected in the `diagram.dmn` file, because the command
line tool will not overwrite it, unless explicitly specified. To save the new
rules, `-o <path>` or `--output-file <path>`, should be used.
