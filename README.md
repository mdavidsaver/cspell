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

So in the following, `myfunc()`, `thearg`, and `retval` will not
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
