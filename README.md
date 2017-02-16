# Seveci

## Blocs

*syntaxe*: `(code)` ou `(code; code2; codeN)`

*note*: `code` représente une expression simple. Pour écrire une suite d'expressions équivalente à ce code Python :

```python
a = 10
b = "hello"
```

On fera ainsi en Seveci :

```
a = 10
b = "hello"
```

*note 2*: on utilise l'écriture en blocs uniquement dans la rédaction du corps d'une fonction / boucle / condition

*note 3*: dans les blocs à base de `()` ayant plus qu'une instruction, chaque instruction se termine par un `;` **sauf** la dernière

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
X = function (void) (
    var = 12;
    print << var;
    Xprime = function(void) (var);
    print << (Xprime << 0);
    var
)
X << 0
print << var
```

L'exécution du script ci-dessus affichera succesivement :

* le `var` du scope **X** (12)

* le `var` du scope **X** (il existe dans le scope actuel, donc on n'a pas besoin d'aller le chercher au-dessus) (12)

* le `var` du scope **global** (10)

## Déclaration de fonctions

*syntaxe*:
```
nom-de-fonction = function (arg1 arg2) (
    reste-du-code
)
```

*note*: il est conseillé de toujours mettre au moins un argument, même si il ne sera pas utilisé auquel cas on le nommera par convention `nul` ou `void`

*note 2*: `reste-du-code` est soit un bloc simple, ou une suite de blocs qui seront dans l'ordre donné

*note 3*: la valeur résultant d'une expression dans le dernier bloc sera la valeur de retour. I.E. : `a-func = function (void) (2 * 3)` retournera 6 après avoir appelé `a-func`

*note 4*: il est possible de modifier la valeur d'un argument dans le scope même de la fonction. I.E. :

```
a-func = function (mon-argument) (
    mon-argument = 4;
    mon-argument
)
```

retournera 4 quelque soit la valeur passée en argument

*note 5*: il n'y a pas de *type checking* possible pour les fonctions ou leurs arguments

*note 6*: une fonction en général doit toujours renvoyer une valeur. Si une fonction vide est dans le code (ce qui peut parfois se passer en phase de développement), elle doit quand même renvoyer quelque chose, par convention 0

### Appel de fonctions

*syntaxe*: `nom-de-fonction << argument1 argument2 argumentN`

*note*: le nombre d'arguments doit être correct, auquel cas une erreur sera levée, pas de *partial evaluation* donc

## Boucle while

*syntaxe*: `while condition statements`

*note*: `condition` peut être `1` (pour faire une boucle infinie par exemple) ou une expression plus complexe, qui sera sous forme d'un simple bloc comme suit : `(valeur operateur valeur2)`. `operateur` peut être un opérateur booléan ou arithmétique. I.E. :

```
while ((10 * (15 + 212)) >= 15) (
    code
)
```

*note 2*: `statements` est un seul bloc

## Boucle for

Il n'y a en réalité pas de boucle `for`. Pour en simuler une (parcourant les éléments d'un tableau par exemple), on fera ainsi :

```
i = -1
while (i++ < (length << list)) (
    elem = list @ i
)
```

## Condition

*syntaxe*: `if condition then [else other-then]`

*note*: `condition`, et `then` peuvent être des blocs (un seul bloc) ou de simples expressions

*note 2*: uniquement **si** `condition` est vraie on que évaluera `then`

*note 3*: le `else` est optionnel. **si** `condition` est fausse et que `else` est spécifié, alors `other-then` sera évalué

*note 4*: `and` se traduit par `&` (qui est aussi un opérateur binaire), `or` par `|` (même remarque) et si on veut faire un `xor` on utilisera `^` (même remarque)

*note 5*: un `if-else` retourne la valeur de la dernière expression évaluée. Par exemple, ici `a` prendra la valeur 5 :

```
a = if (true) (
    5
) else (
    2
)
```

Qui au passage est strictement équivalent à :

`a = if true 5 else 2`

## Types

### Nombre

*syntaxe*: `1`, `42.0`, `1+12i`

### Chaine de caractères

*syntaxe*: `"ma chaine de caractères"`

*note*: pour écrire un `\n` on tapera `$10` (hors de la chaine)

*note 2*: pour écrire un `\t` on tapera `$9` (hors de la chaine)

*note 3*: pour écrire un `\r` on tapera `$13` (hors de la chaine)

### Tableau de valeurs

*syntaxe*: `[valeur1 valeur2 valeurN]`

*note*: un tableau peut contenir n'importe quel type de valeur et même d'autres tableaux

### Type personnalisé : struct

Créer une struct revient à créer ce que l'on appelle `class` dans d'autres langages.

*syntaxe*: ```
objet = struct (
    create = function (argument) (
        code
    );

    a-func = function(argument) (
        code
    )
)
```

*note*: le point d'entrée `create` est obligatoire car c'est lui qui permet d'initialiser une instance de `objet`

*note 2*: une `struct` a son propre environnement pointant vers celui du scope la contenant

*note 3*: chaque fonction dans une `struct` a aussi son propre environnement pointant vers l'environnement global de la `struct`

*note 4*: par convention, on laisse une ligne entre chaque déclaration de fonction. Les déclarations de variables doivent se faire au tout début de la `struct` pour éviter des erreurs. Les variables de `struct` sont préfixées de `_` par convention, et les variables de fonction de `struct` par `__` pour bien les différencier des variables de `struct`. Les noms de fonction de `struct` commencent par `$` par convention, pour les différencier des fonctions du scope supérieur.

*note 5*: toutes les variables déclarées dans une `struct` sont **et** resteront toujours privées, sans possibilité de changer ce comportement

#### Instancier une struct

*syntaxe*: `instance = objet << args`

*note*: cette syntaxe appelera le point d'entrée `create` de `objet` en lui donnant en argument `args`

#### Utiliser une struct

Après avoir instancié un objet que l'on a créé, on souhaite en utiliser ses méthodes.

*syntaxe*: `instance::a-func << args`

*note*: il faut que `instance` existe et soit une instance d'une `struct`, pas directement un objet !

## Importer un code Python

*syntaxe*: `include << "module-name"`

*note*: les guillemets sont obligatoires car `include` est une fonction

*note 2*: le module est inclus dans le scope dans lequel on appelle la fonction `include`. On peut donc inclure un module **X** dans un scope **SX** pour ainsi le rendre inaccessible au scope supérieur **global** (par exemple)

### Utiliser des fonctions d'un module Python importé

*syntaxe*: `module-name::fonction << arg1 arg2 argN`

*note*: le nombre d'arguments doit être respecté

*note 2*: l'usage de `<<` est obligatoire car `module-name::fonction` est considéré comme une fonction pour l'interpréteur

*note 3*: si la fonction ne prend pas d'arguments, ne pas lui en donner même si l'écriture `a-func = function (void) code` est à favoriser (pour raison de compatibilité avec les codes Python)