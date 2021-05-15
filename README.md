formset
=======

A `form.set` generator.

This is a small script to generate a configuration file `form.set` of
[FORM](https://www.nikhef.nl/~form/) for your machine.
The script suggests adequate *static* buffer sizes for `tform` from
the number of CPUs and physical memory available on the computer.


Usage
-----

```shell
formset     # prints a set of adequate setup parameters

formset -o  # writes a set of adequate setup parameters to "form.set"
```

Note that this script considers only *static* buffers, allocated
at the start-up of FORM.
If your FORM program uses much bigger *dynamical* buffers than usual
(for example, you need to handle complicated rational functions
or you want to optimize very huge polynomials)
then you need to adjust the initial memory usage by
the `--percentage N` (or `-p N`) option:

```shell
formset -p 50
```

If your program requires a non-default `MaxTermSize` (or other parameters),
then you need to specify it:

```shell
formset MaxTermSize=200K
```

Other command-line options can be found in the help message:

```shell
formset --help
```


## License

[MIT](https://github.com/tueda/formset/blob/main/LICENSE)
