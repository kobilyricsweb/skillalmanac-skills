# Python class diagram in Mermaid

## One line

Reads saved Python files with the ast module and prints a Mermaid classDiagram of their module-level classes, with inheritance and type-annotation relations.

## What it does

The script `scripts/py_classes.py` parses each input file as source text. It never imports the module, so top-level code, decorators with side effects, and import-time errors do not run. For every module-level class it records the base classes, the class-level attributes, the annotated attributes assigned to `self` inside methods, and the methods with their argument names and return annotations. Visibility follows the usual Python naming convention: double-underscore names get a minus sign, single-underscore names get a hash sign, and everything else gets a plus sign. Static and class methods carry a dollar marker, and abstract methods carry an asterisk.

Relations come from the code itself. An inheritance arrow links each base to its subclass. An annotation that names a class defined in the inputs produces a composition arrow when it is the whole type or an optional of it, and an aggregation arrow when the class appears inside a container such as a list or a dictionary. Files that fail to parse are reported as comment lines in the output, and the remaining files still produce a diagram. The summary line counts files, classes, attributes, methods, relations, and syntax errors, so a reader can check the diagram against the source.

## When to use

Use it when a developer hands over a few modules and asks for a class diagram, when a code review needs a quick picture of inheritance across two files, or when documentation needs a starting diagram that a person will then tidy up. It is most useful for small to medium modules where the class structure is hidden in the code.

## When not to use

Do not use it on languages other than Python, on live objects that exist only at runtime, or on code whose classes are built inside functions, `if` blocks, or metaclasses, because those classes are not listed. Do not use it for call-flow or sequence diagrams. Do not expect it to render the picture; it prints text for a Mermaid viewer.

## Requirements

Python 3.9 or newer, standard library only. No network access and no extra packages. The output needs a Mermaid renderer to become a picture, which is outside this skill.

## Example

Command run against the two shipped fixtures, `fixtures/geometry.py` and `fixtures/circle.py`:

```
python -I scripts/py_classes.py fixtures/geometry.py fixtures/circle.py
```

Output, pasted from the run:

```
classDiagram
% py_classes files=2 classes=3 attributes=6 methods=6 relations=4 syntax_errors=0
class Shape {
    +str name
    +str label
    +__init__(name) None
    +area()* float
    +unit()$ str
}
class Canvas {
    +List~Shape~ shapes
    #Optional~Shape~ _focus
    +add(shape) None
}
class Circle {
    +float radius
    -int __id
    +__init__(radius) None
    +area() float
}
ABC <|-- Shape
Canvas *-- Shape : _focus
Canvas o-- Shape : shapes
Shape <|-- Circle
```

The counts check out by hand: three classes, six attribute lines, six method lines, and four relation lines. The `Canvas` annotations show both relation kinds, and `Shape` is the only class with an external base, which appears as the stub `ABC`.

## Limits

The script does not verify that the diagram renders in a Mermaid viewer, and it does not check that the Python code runs. It lists module-level classes only. Nested classes, classes created inside functions or conditional blocks, and classes produced by metaclasses are not shown. Properties are listed as ordinary methods, and plain `self.x = value` assignments without an annotation are not listed as attributes. Method parameters show names only, with no types or defaults. When two files define a class with the same name, both blocks are printed, and Mermaid merges them into one node. The tool does not judge design quality, does not detect circular imports, and does not confirm that a relation reflects runtime behavior, since a composition hint comes from an annotation alone. It was run on Python 3.11 only.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
