# Seventh-C

## Blocs

*syntaxe*: `(code)`

*note*: `code` représente une expression simple. Pour écrire une suite d'expressions équivalente à ce code Python :

```python
a = 10
b = "hello"
```

On fera ainsi en Seventh-C :

`(a = 10) (b = "hello")`

*note 2*: on utilise l'écriture en blocs uniquement dans la rédaction du corps d'une fonction / boucle / condition

## Déclaration de variables

*syntaxe*: `nom-de-variable = valeur`

*note*: la règle définissant le nommage des variables et la même que celle appliquée au nommage des fonctions, et est la suivante :

```python
r'[A-Za-z_$][A-Za-z0-9_\?-]*'
```

*note 2*: une valeur peut être de n'importe quel type (voir section `Types`), voir même une expression algébrique (chaque opérande doit néanmoins être entouré de parenthèses)

### Utilisation de la valeur d'une variable

*syntaxe*: `nom-de-variable`

*note*: supposons 3 scopes : un scope **global**, un scope **X** dans le scope **global**, et un scope **X'** dans le scope **X**. Nous avons dans le scope **global** et dans le scope **X** une variable nommée `var` (elle n'est pas crée dans le scope **X'**). Si l'on souhaite accéder à `var` depuis le scope **X'**, on obtiendra la valeur de `var` dans le scope directement supérieur, c'est à dire celle que `var` a dans le scope **X**. I.E. :

```
var = 10  # scope global
X = function (void) (var = 12) (Xprime = function(void) (var)) (Xprime << 0) (var)
var
```

L'exécution du script ici renverra succesivement :

* le `var` du scope **X** (12)

* le `var` du scope **X** (il existe dans le scope actuel, donc on n'a pas besoin d'aller le chercher au-dessus) (12)

* le `var` du scope **global** (10)

## Déclaration de fonctions

*syntaxe*: `nom-de-fonction = function (arg1 arg2) reste-du-code`

*note*: il est conseillé de toujours mettre au moins un argument, même si il ne sera pas utilisé auquel cas on le nommera par convention `nul` ou `void`

*note 2*: `reste-du-code` est soit un bloc simple, ou une suite de blocs qui seront dans l'ordre donné

*note 3*: la valeur résultant d'une expression dans le dernier bloc sera la valeur de retour. I.E. : `a-func = function (void) (2 * 3)` retournera 6 après avoir appelé `a-func`

*note 4*: il est possible de modifier la valeur d'un argument dans le scope même de la fonction. I.E. : `a-func = function (mon-argument) (mon-argument = 4) (mon-argument)` retournera 4 quelque soit la valeur passée en argument

*note 5*: il n'y a pas de *type checking* possible dans les fonctions

### Appel de fonctions

*syntaxe*: `nom-de-fonction << argument1 argument2 argumentN`

*note*: le nombre d'arguments doit être correct, auquel cas une erreur sera levée, pas de *partial evaluation* donc

## Boucle while

*syntaxe*: `while condition statements`

*note*: `condition` peut être `1` (pour faire une boucle infinie par exemple) ou une expression plus complexe, qui sera sous forme d'un simple bloc comme suit : `(valeur operateur valeur2)`. `operateur` peut être un opérateur booléan ou arithmétique. I.E. : `while ((10 * (15 + 212)) >= 15) code`

*note 2*: `statements` est un ou plusieurs blocs. S'il y a plusieurs blocs, ils seront exécutés dans l'ordre où ils apparaissent

## Condition

*syntaxe*: `if condition then otherwise`

*note*: `condition`, `then` et `otherwise` peuvent être des blocs (un seul bloc) ou de simples expressions

*note 2*: uniquement **si** `condition` est vrai on que évaluera `then`, dans le cas contraire on évaluera que `otherwise`

## Types

### Nombre

### Chaine de caractères

### Tableau de valeurs

## Continuation de ligne(s)

Devoir écrire une instruction comme une boucle de traitement dans un plus ou moins sur une seule ligne est extrêmement lourd :

`while (x != nb) (if (x < nb) (print << "C'est plus !") (print << "C'est moins")) (x = user << 0)`

C'est pourquoi, pour indiquer au parseur que la ligne n'est pas terminée, on peut placer '\' en fin de ligne pour alléger la syntaxe :

`while (x != nb) \
    (if (x < nb) \
        (print << "C'est plus !") \
        (print << "C'est moins")) \
    (x = user << 0)`

Ces deux codes sont strictement équivalent.

## Importer un code Python

*syntaxe*: `include << "module-name"`

*note*: les guillemets sont obligatoires car `include` est une fonction

*note 2*: le module est inclus dans le scope dans lequel on appelle la fonction `include`. On peut donc inclure un module **X** dans un scope **SX** pour ainsi le rendre inaccessible au scope supérieur **global** (par exemple)

### Utiliser des fonctions d'un module Python importé

*syntaxe*: `module-name::fonction << arg1 arg2 argN`

*note*: le nombre d'arguments doit être respecté

*note 2*: l'usage de `<<` est obligatoire car `module-name::fonction` est considéré comme une fonction pour l'interpréteur

*note 3*: si la fonction ne prend pas d'arguments, ne pas lui en donner même si l'écriture `a-func = function (void) code` est à favoriser (pour raison de compatibilité avec les codes Python)
