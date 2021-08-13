C Code Spell Correction
=======================

Context aware spelling check of comments and string literals in C/C++ source code files.
Operation is non-interactive to facilitate operations on an existing large code base.

1. First pass to collect terms from source code and propose corrections to comments.

```sh
$ ./cspell --out-dict code.dic --out-corrections fix.json code.c ...
```

2. Edit candiate corrections in fix.json.

3. Apply corrections

```sh
$ ./cspell --add-dict code.dic --corrections fix.json --modify code.c ...
```

The argument `-f`/`--inputs` reads a list of source files from a file.

Operation
---------

`cspell` separates string literals and C/C++ comments from code.
Tokens/terms found in code are automatically excluding from spell check.

So in the following `example.c`, `myfunc()`, `thearg`, and `retval` will not
be flagged as spelling errors.

```c
/** Copyright 2021 Michael Davidsaver
*  Who can't spelll rite
*/
#include <stdio.h>
/** @brief special
 * @param thearg is the argument
 */
void myfunc(int thearg) {
    // myfunc() is a functon on thearg and retval
    int retval = thearg;
    if(thearg==42)
        printf("thearg is amagic value\n");
    /* another commment */
    return retval;
}
```

```sh
$ echo -e '1\nDavidsaver\n' > personal.dic
$ python3 -m cspell -q -D personal.dic -W example.dic -F example.json example.c
```

`example.json` now contains:

```json
{
  "amagic": "magic"
  // "a magic"
  // ... "thearg is amagic value\n"
  ,
  "commment": "comment"
  // "commitment" "commencement" "commandment" "commence"
  // ... /* another commment */
  ,
  "functon": "function"
  // "functor" "futon"
  // ... // myfunc() is a functon on thearg and retval
  ,
  "spelll": "spell"
  // "spells" "spell l"
  // ... *  Who can't spelll rite
}
}
```

Which should be edited and then applied with

```sh
$ cp example.c example.c.orig
$ python3 -m cspell -q -D personal.dic -D example.dic -C example.json example.c --modify
$ diff -u example.c.orig example.c
```

Shows

```diff
--- example.c.orig      2021-08-13 14:13:49.980036186 -0700
+++ example.c   2021-08-13 14:42:51.055857533 -0700
@@ -1,15 +1,15 @@
 /** Copyright 2021 Michael Davidsaver
-*  Who can't spelll rite
+*  Who can't spell rite
 */
 #include <stdio.h>
 /** @brief special
  * @param thearg is the argument
  */
 void myfunc(int thearg) {
-    // myfunc() is a functon on thearg and retval
+    // myfunc() is a function on thearg and retval
     int retval = thearg;
     if(thearg==42)
-        printf("thearg is amagic value\n");
-    /* another commment */
+        printf("thearg is magic value\n");
+    /* another comment */
     return retval;
 }
```
