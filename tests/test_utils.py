import formset


def test_parse_number():
    # type: () -> None
    parse_number = formset.formset.parse_number
    assert parse_number("123") == 123
    assert parse_number("123k") == 123 * 10**3
    assert parse_number("123K") == 123 * 10**3
    assert parse_number("123m") == 123 * 10**6
    assert parse_number("123M") == 123 * 10**6
    assert parse_number("123g") == 123 * 10**9
    assert parse_number("123G") == 123 * 10**9
    assert parse_number("123t") == 123 * 10**12
    assert parse_number("123T") == 123 * 10**12


def test_round_human_readable():
    # type: () -> None
    round_human_readable = formset.formset.round_human_readable
    assert round_human_readable(12345, False, True) == "12300"
    assert round_human_readable(12345 * 10, False, True) == "123K"
    assert round_human_readable(12345 * 10**2, False, True) == "1230K"
    assert round_human_readable(12345 * 10**3, False, True) == "12300K"
    assert round_human_readable(12345 * 10**4, False, True) == "123M"
    assert round_human_readable(12345 * 10**5, False, True) == "1230M"
    assert round_human_readable(12345 * 10**6, False, True) == "12300M"
    assert round_human_readable(12345 * 10**7, False, True) == "123G"
    assert round_human_readable(12345 * 10**8, False, True) == "1230G"
    assert round_human_readable(12345 * 10**9, False, True) == "12300G"
    assert round_human_readable(12345 * 10**10, False, True) == "123T"
    assert round_human_readable(12345 * 10**11, False, True) == "1230T"
    assert round_human_readable(12345 * 10**12, False, True) == "12300T"

    assert round_human_readable(12345, True, True) == "12400"
    assert round_human_readable(12345 * 10, True, True) == "124K"
    assert round_human_readable(12345 * 10**2, True, True) == "1240K"
    assert round_human_readable(12345 * 10**3, True, True) == "12400K"
    assert round_human_readable(12345 * 10**4, True, True) == "124M"
    assert round_human_readable(12345 * 10**5, True, True) == "1240M"
    assert round_human_readable(12345 * 10**6, True, True) == "12400M"
    assert round_human_readable(12345 * 10**7, True, True) == "124G"
    assert round_human_readable(12345 * 10**8, True, True) == "1240G"
    assert round_human_readable(12345 * 10**9, True, True) == "12400G"
    assert round_human_readable(12345 * 10**10, True, True) == "124T"
    assert round_human_readable(12345 * 10**11, True, True) == "1240T"
    assert round_human_readable(12345 * 10**12, True, True) == "12400T"
