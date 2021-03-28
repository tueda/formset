import formset

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Any


def test_version():
    # type: () -> None
    assert formset.__version__


def test_setup_scale():
    # type: () -> None
    sp0 = formset.Setup((4, 2, 1))
    sp0.threads = 8

    # accuracy test 1

    mem = 10 ** 12  # 1T
    sp = sp0.copy()
    sp = sp.scale(mem)
    usage = sp.calc()
    assert usage <= mem
    assert float(abs(usage - mem)) / mem < 0.00001

    # accuracy test 2

    mem = 10 ** 12  # 1T
    sp = sp0.copy()
    sp.maxtermsize = 10 ** 6
    sp = sp.scale(mem)
    usage = sp.calc()
    assert usage <= mem
    assert float(abs(usage - mem)) / mem < 0.00001

    # case with scaling < 1

    mem = 16 * 10 ** 9  # 16G
    sp = sp0.copy()
    sp.largesize = mem  # too big
    sp = sp.scale(mem)
    usage = sp.calc()
    assert usage <= mem

    # lowest_scale test

    mem = 16 * 10 ** 9  # 16G
    sp = sp0.copy()
    sp.largesize = mem  # too big
    sp = sp.scale(mem, 1.0)
    usage = sp.calc()
    assert usage >= mem


def test_main(capsys):
    # type: (Any) -> None
    args = [
        "--usage",
        "--ncpus=40",
        "--total-cpus=80",
        "--total-memory=1000000000000",
        "--percentage=80",
    ]
    formset.main(args)
    captured = capsys.readouterr()
    reserved_memory = int(1000000000000 * 0.5 * 0.80 + 0.5)
    memory_usage = int(captured[0])
    assert memory_usage <= reserved_memory
    assert float(abs(reserved_memory - memory_usage)) / reserved_memory < 0.00001
