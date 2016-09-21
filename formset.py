#!/bin/sh
""":" .

exec python "$0" "$@"
"""

from __future__ import print_function

import argparse
import contextlib
import copy
import re
import subprocess
import sys

__doc__ = """\
Generate form.set suited for the local machine.

Example
-------
$ formset.py -o
$ tform `formset.py -f` calcdia.frm
$ minos `formset.py -m` minos.file
"""


@contextlib.contextmanager
def open_w_or_stdout(filename=None):
    """Context manager for a file or stdout."""
    if filename:
        f = open(filename, 'w')
    else:
        f = sys.stdout
    yield f
    if filename:
        f.close()


def round_down(x, n):
    """Round down `x` to nearest `n`."""
    return x // n * n


def round_up(x, n):
    """Round down `x` to nearest `n`."""
    return (x + (n - 1)) // n * n


class classproperty(property):  # noqa
    """Decorator to make a property of a class."""

    def __get__(self, cls, owner):
        """Getter."""
        return classmethod(self.fget).__get__(None, owner)()


class SystemInfo(object):
    """System information."""

    _cpu_info = None
    _mem_info = None

    @classproperty
    def number_of_nodes(cls):  # noqa
        """Return the number of nodes."""
        info = cls._get_cpu_info()
        return int(info['NUMA node(s)'])

    @classproperty
    def number_of_cpus(cls):  # noqa
        """Return the number of cpus."""
        info = cls._get_cpu_info()
        return int(info['CPU(s)'])

    @classproperty
    def number_of_physical_cores(cls):  # noqa
        """Return the number of physical cores."""
        info = cls._get_cpu_info()
        return int(info['Socket(s)']) * int(info['Core(s) per socket'])

    @classproperty
    def total_memory(cls):  # noqa
        """Return the total physical memory in bytes."""
        info = cls._get_mem_info()
        return int(info['Mem'][0])

    @classmethod
    def _get_cpu_info(cls):
        if cls._cpu_info is None:
            info = subprocess.check_output(['lscpu'])
            info = info.decode(encoding='utf-8')
            info = info.strip().split('\n')
            info = [[ss.strip() for ss in s.split(':')] for s in info]
            info = dict(info)
            cls._cpu_info = info
        return cls._cpu_info

    @classmethod
    def _get_mem_info(cls):
        if cls._mem_info is None:
            info = subprocess.check_output(['free', '-b'])
            info = info.decode(encoding='utf-8')
            info = info.strip().split('\n')
            info = [[ss.strip() for ss in s.split(':')] for s in info]
            info = [s for s in info if len(s) == 2]
            info = [[s[0], s[1].split()] for s in info]
            info = dict(info)
            cls._mem_info = info
        return cls._mem_info


class Setup(object):
    """Setup parameters."""

    def __init__(self):
        """Construct a set of setup parameters."""
        self.compresssize = 90000
        self.filepatches = 256
        self.hidesize = 50000000
        self.largepatches = 256
        self.largesize = 50000000
        self.maxtermsize = 40000  # 64-bit
        self.numstorecaches = 4
        self.scratchsize = 50000000
        self.sizestorecache = 32768
        self.smallextension = 20000000
        self.smallsize = 10000000
        self.sortiosize = 100000
        self.termsinsmall = 100000
        self.threadbucketsize = 500
        self.threads = -1  # form
        self.threadscratchoutsize = 2500000
        self.threadscratchsize = 100000
        self.workspace = 40000000  # 64-bit

        self.bracketindexsize = 200000
        self.constindex = 128
        self.continuationlines = 15
        self.functionlevels = 30
        self.maxnumbersize = 200
        self.maxwildcards = 100
        self.parentheses = 100
        self.processbucketsize = 1000
        self.subfilepatches = 64
        self.sublargepatches = 64
        self.sublargesize = 4000000
        self.subsmallextension = 800000
        self.subsmallsize = 500000
        self.subsortiosize = 32768
        self.subtermsinsmall = 10000

        # 64-bit
        self._ptrsize = 8
        self._possize = 8
        self._wordsize = 4

    def items(self):
        """Return pairs of parameters and values."""
        items = [(k, v) for (k, v) in self.__dict__.items() if k[0] != '_']
        items.sort()
        return tuple(items)

    def __str__(self):
        """Return the string representaiton."""
        mem = self.calc()
        params = ['{0}: {1}'.format(k, v) for (k, v) in self.items()]
        return '<Setup: {0} bytes, {1}>'.format(mem, ', '.join(params))

    def copy(self):
        """Return a shallow copy."""
        return copy.copy(self)

    def calc(self):
        """Return an estimation of memory usage."""
        self.maxtermsize = max(self.maxtermsize, 200)

        self.compresssize = max(self.compresssize,
                                2 * self.maxtermsize * self._wordsize)
        self.sortiosize = max(self.sortiosize,
                              self.maxtermsize * self._wordsize)

        # The strange factor WordSize**2 is used in the FORM source...
        self.scratchsize = max(self.scratchsize,
                               4 * self.maxtermsize * self._wordsize**2)
        if self.hidesize > 0:
            self.hidesize = max(self.hidesize,
                                4 * self.maxtermsize * self._wordsize**2)

        self.threadscratchsize = max(self.threadscratchsize,
                                     4 * self.maxtermsize * self._wordsize**2)
        self.threadscratchoutsize = max(self.threadscratchoutsize,
                                        4 * self.maxtermsize *
                                        self._wordsize**2)

        # constraints in RecalcSetups()

        self.filepatches = max(self.filepatches, self.threads)

        self.termsinsmall = round_up(self.termsinsmall, 16)

        numberofblocksinsort = 10
        minimumnumberofterms = 10
        n = numberofblocksinsort * minimumnumberofterms
        if self.threads >= 0:
            minbufsize = (self.threads * (1 + n) * self.maxtermsize *
                          self._wordsize)
            if self.largesize + self.smallextension < minbufsize:
                self.largesize = minbufsize - self.smallextension

        # constraints in AllocSort()

        self.filepatches = max(self.filepatches, 4)

        self.smallsize = max(self.smallsize,
                             16 * self.maxtermsize * self._wordsize)

        self.smallextension = max(self.smallextension, self.smallsize * 3 // 2)

        if self.largesize > 0:
            self.largesize = max(self.largesize, 2 * self.smallsize)

        compinc = 2
        minbufsize = self.filepatches * (self.sortiosize +
                                         (compinc + 2 * self.maxtermsize) *
                                         self._wordsize)
        if self.largesize + self.smallextension < minbufsize:
            if self.largesize == 0:
                self.smallextension = minbufsize
            else:
                self.largesize = minbufsize - self.smallextension

        iotry = (((self.largesize + self.smallextension) // self.filepatches //
                 self._wordsize) - 2 * self.maxtermsize - compinc)  # in words
        self.sortiosize = max(self.sortiosize, iotry)  # bytes vs. words??

        # Compute the memory usage.

        mem = 0
        mem += (self.scratchsize * 2 + (self.hidesize
                                        if self.hidesize > 0
                                        else self.scratchsize))
        mem += self.workspace * self._wordsize
        mem += (self.compresssize + 10) * self._wordsize
        mem += (self.largesize + self.smallextension + 3 * self.termsinsmall *
                self._ptrsize + self.sortiosize)

        storecachesize = self._possize * 2 * self._ptrsize + self._wordsize
        # ignore the padding
        storecachesize += self.sizestorecache
        mem += storecachesize * self.numstorecaches

        if self.threads >= 1:
            mem += ((self.threadscratchoutsize + self.threadscratchsize * 2) *
                    self.threads)
            mem += self.workspace * self._wordsize * self.threads
            mem += (self.compresssize + 10) * self._wordsize * self.threads

            mem += self._thread_alloc_sort(self.largesize // self.threads,
                                           self.smallsize // self.threads,
                                           self.smallextension // self.threads,
                                           self.termsinsmall,
                                           self.largepatches,
                                           self.filepatches // self.threads,
                                           self.sortiosize) * self.threads

            mem += storecachesize * self.numstorecaches * self.threads

            sizethreadbuckets = ((self.threadbucketsize + 1) *
                                 self.maxtermsize + 2) * self._wordsize
            if self.threadbucketsize >= 250:
                sizethreadbuckets //= 4
            elif self.threadbucketsize >= 90:
                sizethreadbuckets //= 3
            elif self.threadbucketsize >= 40:
                sizethreadbuckets //= 2
            sizethreadbuckets //= self._wordsize
            mem += ((2 * sizethreadbuckets * self._wordsize +
                    (self.threadbucketsize + 1) * self._possize) *
                    2 * self.threads)
            if self.threads >= 3:
                mem += ((self.workspace * self._wordsize // 8 +
                        2 * self.maxtermsize * self._wordsize) *
                        (self.threads - 2))

        return mem

    def _thread_alloc_sort(self, largesize, smallsize, smallextension,
                           termsinsmall, largepatches, filepatches,
                           sortiosize):

        filepatches = max(filepatches, 4)

        smallsize = max(smallsize, 16 * self.maxtermsize * self._wordsize)

        smallextension = max(smallextension, smallsize * 3 // 2)

        if largesize > 0:
            largesize = max(largesize, 2 * smallsize)

        compinc = 2
        minbufsize = filepatches * (sortiosize + (compinc +
                                    2 * self.maxtermsize) * self._wordsize)
        if largesize + smallextension < minbufsize:
            if largesize == 0:
                smallextension = minbufsize
            else:
                largesize = minbufsize - smallextension

        iotry = (((largesize + smallextension) // filepatches //
                 self._wordsize) - 2 * self.maxtermsize - compinc)  # in words
        sortiosize = max(sortiosize, iotry)  # bytes vs. words??

        return (largesize + smallextension + 3 * termsinsmall * self._ptrsize +
                sortiosize)


def main():
    """Entry point."""
    nnodes = SystemInfo.number_of_nodes
    total_cpus = SystemInfo.number_of_physical_cores
    memory = int(SystemInfo.total_memory)

    # Parse the command line arguments.
    parser = argparse.ArgumentParser(
        usage='%(prog)s [options] [par=val].. [par+=int].. [par*=float]..'
    )
    parser.add_argument('-o',
                        '--output',
                        action='store',
                        nargs='?',
                        const='form.set',
                        help=('output to FILE (default: no (stdout), '
                              'FILE=form.set)'),
                        metavar='FILE')
    parser.add_argument('-f',
                        '--form',
                        action='store_const',
                        const=True,
                        help='print tform options and exit')
    parser.add_argument('-m',
                        '--minos',
                        action='store_const',
                        const=True,
                        help='print minos options and exit')
    parser.add_argument('-u',
                        '--usage',
                        action='store_const',
                        const=True,
                        help='print expected initial memory usage and exit')
    parser.add_argument('-n',
                        '--ncpus',
                        action='store',
                        default=None,
                        type=int,
                        help=('number of cpus '
                              '(default: number of cpus in a node)'),
                        metavar='N')
    parser.add_argument('-p',
                        '--percentage',
                        action='store',
                        default=0.75,
                        type=float,
                        help=('percentage of initial memory usage '
                              '(default: 0.75)'),
                        metavar='N')
    parser.add_argument('args',
                        nargs='*',
                        help=argparse.SUPPRESS)
    args = parser.parse_args()
    pars = {}

    # Use 1 node for each job by default.
    ncpus = total_cpus // nnodes
    if ncpus < 2:
        ncpus = max(ncpus, total_cpus)
    # Can be overwritten.
    if args.ncpus is not None:
        ncpus = args.ncpus

    sp = Setup()
    sp.threads = ncpus if ncpus >= 2 else -1

    def metric_prefix(s):
        s = s.lower()
        if s == '':
            return 1
        if s == 'k':
            return 1000
        if s == 'm':
            return 1000**2
        if s == 'g':
            return 1000**3
        if s == 't':
            return 1000**4
        return None

    for a in args.args:
        m = re.match(r'([a-zA-Z][a-zA-Z0-9]*)([+*]?)=(.*)', a)
        if m:
            par = m.group(1).lower()
            ope = m.group(2)
            val = m.group(3)
            if par in sp.__dict__:
                if ope == '' or ope == '+':
                    try:
                        scale = 1
                        m = re.match(r'(.*)([kmgtKMGT])$', val)
                        if m:
                            val = m.group(1)
                            scale = metric_prefix(m.group(2))
                        val = int(val) * scale
                        if ope == '':
                            setattr(sp, par, val)
                        else:
                            setattr(sp, par, getattr(sp, par) + val)
                        continue
                    except ValueError:
                        pass
                    parser.error(
                        'non-integer value for parameter: {0}'.format(a))
                else:
                    try:
                        val = float(val)
                        setattr(sp, par, int(getattr(sp, par) * val))
                        continue
                    except ValueError:
                        pass
                    parser.error(
                        'non-float value for parameter: {0}'.format(a))
            elif ope == '':
                pars[par] = val
                continue
        parser.error('unrecognized argument: {0}'.format(a))

    # Our resource.
    cpus = max(sp.threads, 1)
    memory = int(memory * args.percentage * cpus / total_cpus)

    # For --form option.
    if args.form:
        print('-w{0}'.format(cpus))
        exit()

    # For --minos option.
    if args.minos:
        print('-m{0}x{1}'.format(total_cpus // cpus, cpus))
        exit()

    # Presumably increasing MaxTermSize requires increasing WorkSpace too.
    sp.workspace = max(sp.workspace, sp.maxtermsize * 250)

    # Optimize the memory usage.
    max_iteration = 50

    sp0 = sp.copy()

    def f(x):
        # Hopefully monochrome increasing.
        sp = sp0.copy()
        sp.smallsize = int(sp.smallsize * x)
        sp.largesize = int(sp.largesize * x)
        sp.termsinsmall = int(sp.termsinsmall * x)
        sp.scratchsize = int(sp.scratchsize * x)
        m = sp.calc()
        return (- (memory - m), sp)

    x1 = 1.0
    x2 = None
    y1 = f(x1)[0]
    y2 = None
    for i in range(max_iteration):
        if x2 is None:
            if y1 < 0:
                x = x1 * 2.0
                y = f(x)[0]
                if y > 0:
                    x2 = x
                    y2 = y
                else:
                    x1 = x
                    y1 = y
            else:
                x = x1 * 0.5
                y = f(x)[0]
                if y < 0:
                    x2 = x1
                    y2 = y1
                    x1 = x
                    y1 = y
                else:
                    x1 = x
                    y1 = y
        else:
            x = (x1 + x2) * 0.5
            y = f(x)[0]
            if y < 0:
                x1 = x
                y1 = y
            else:
                x2 = x
                y2 = y
        if x2 is not None:
            assert x1 < x2 and y1 < y2

    if x2 is None:
        if x1 < 1.0e-12:
            x1 = 0
        parser.exit('failed to find parameters: memory({0})={1}'.format(
            x1, y1))

    # For --usage option.
    if args.usage:
        print(f(x1)[1].calc())
        exit()

    # Output.
    with open_w_or_stdout(args.output) as fi:
        sp = f(x1)[1]
        sp0 = Setup()  # default value
        dic0 = dict(sp0.items())
        for k, v in sp.items():
            if k == 'threads':
                # 'threads N' doesn't work, must be given by tform option -wN.
                continue
            if v == dic0[k]:
                # Don't write when same as the default value.
                continue
            print('{0} {1}'.format(k, v), file=fi)
        for k, v in pars.items():
            print('{0} {1}'.format(k, v), file=fi)


if __name__ == '__main__':
    main()
