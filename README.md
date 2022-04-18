# Type Inference

Type inference is the ability to infer, either partially or fully, the type of an expression at compile time. The objective of this project is the implementation of a **COOL** interpreter that has type inference by adding the `AUTO_TYPE` type.

A COOL program need not specify all type annotations if they are inferable given the context. Annotations are occasionally needed for disambiguation, eg type inference with polymorphic recursion is undecidable. Below are some examples showing some cases in which it is possible to infer the type of expressions and in which cases a semantic error will be thrown.