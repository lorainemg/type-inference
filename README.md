# Type Inference

Type inference is the ability to infer, either partially or fully, the type of an expression at compile time. The objective of this project is the implementation of a **COOL** interpreter that has type inference by adding the `AUTO_TYPE` type.

A **COOL** program need not specify all type annotations if they are inferable given the context. Annotations are occasionally needed for disambiguation, eg type inference with polymorphic recursion is undecidable. Below are some examples showing some cases in which it is possible to infer the type of expressions and in which cases a semantic error will be thrown.

## Examples

The simplest case is when the type is omitted in a variable declaration. In this case, the type is inferred from the initialization expression:

```[cool]
class Main {
    function main() : AUTO_TYPE {
        let x : AUTO_TYPE <- 3 + 2 in {
            case x of y : Int => out_string("Ok");
        }
    };
};
```

The same happens with the attributes of a class, when they can be inferred by the type of the initialization expression:

```[cool]
class Point {
    x : AUTO_TYPE;
    y : AUTO_TYPE;
    init(n : Int, m : Int) : SELF_TYPE {
    {
        x <- n;
        y <- m;
    }};
};
```

A more complex case is when the return type of a function is left unspecified, but can be inferred from its body:

```[cool]
(...)
function succ(n : Int) : AUTO_TYPE { n + 1 };
(...)
```

In the above case, it's easy to infer the return type of succ because the expression returns exactly the same type as an argument. In these cases, it is even possible not to specify the type of the argument, since the `+` operator is only defined for `Int`:

```[cool]
(...)
function succ(n : AUTO_TYPE) : AUTO_TYPE { n + 1 };
(...)
```

However, it is sometimes not possible to infer the type of an argument from its use within a function body. In the following case, although we know that the type of the argument `p` must be `Point` to accept the invocation, it is not guaranteed that the type inference mechanism will have to infer it (because in the future there may be
other classes with a `translate` method). Depending on the implementation, in these cases it is allowed to throw a semantic error indicating that it was not possible to infer the type of the argument `p`.

```[cool]
(...)
function step(p : AUTO_TYPE) { p.translate(1,1) };
(...)
let p : AUTO_TYPE <- new Point(0,0) in {
    step(p) # Puede lanzar error semantico
};
(...)
```

Finally, recursive functions carry special complexity:

```[cool]
(...)
function fact(n : AUTO_TYPE) {
if (n<0) then 1 else n*fact(n-1) fi
};
(...)
```

The example above allows the type of the argument `n` and the return to be inferred simultaneously, since the return of the recursive function is used in a `+` operation that is only defined for `Int`. However, in the following example:

```[cool]
(...)
function ackermann(m : AUTO_TYPE, n: AUTO_TYPE) : AUTO_TYPE {
    if (m==0) then n+1 else
        if (n==0) then ackermann(m-1, 1) else
            ackermann(m-1, ackermann(m, n-1))
        fi
    fi
};
(...)
```

Since the return type is not used explicitly in a mathematical operation, it is not trivial to deduce that its return type is `Int`, since `Object` would also work as a return type. In these cases, you want the inference mechanism to deduce the most concrete type for the return and the most abstract type for the arguments that is possible.

Finally, two mutually recursive functions:

```[cool]
function f(a: AUTO_TYPE, b: AUTO_TYPE) : AUTO_TYPE {
    if (a==1) then b else
        g(a + 1, b/2)
    fi
}

function g(a: AUTO_TYPE, b: AUTO_TYPE) : AUTO_TYPE {
    if (b==1) then a else
        f(a/2, b+1)
    fi
}
```

In this case, it is theoretically possible to infer that `f` and `g` must both return type `Int`, but given the complexity of handling type inference in more than one function at a time, it is not guaranteed that it will be possible to infer types in this case.
