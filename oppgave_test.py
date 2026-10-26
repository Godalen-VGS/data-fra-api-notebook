"""Automatisk retting av 19-data-fra-api.

Hver sjekk i SJEKKER er én deltest, og poengene fordeles likt på dem.
De samme sjekkene ligger i "Test løsningen din"-cellen nederst i notebooken.
"""
import pytest

from notebook_loader import last_notebook

def naer(a, b, rel=1e-3):
    """Sant hvis tallet a er innenfor rel (relativt) av b."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) <= rel * abs(b)


def S(tekst):
    """Gjør tekst om til et sympy-uttrykk, f.eks. S("x**2 - 1")."""
    import sympy
    return sympy.sympify(tekst, locals={n: sympy.Symbol(n) for n in ("N", "O", "Q", "S")})


def lik(a, b):
    """Sant hvis a og b er matematisk like.

    Lister og mengder sammenlignes uten hensyn til rekkefølge, tupler (koordinater) i rekkefølge.
    """
    import sympy
    if a is None:
        return False
    if isinstance(b, tuple):
        if not isinstance(a, (tuple, list, sympy.Tuple)) or len(a) != len(b):
            return False
        return all(lik(x, y) for x, y in zip(a, b))
    if isinstance(b, (list, set)):
        if isinstance(a, sympy.FiniteSet):
            a = list(a)
        if not isinstance(a, (list, tuple, set)) or len(a) != len(b):
            return False
        rest = list(a)
        for y in b:
            for i, x in enumerate(rest):
                if lik(x, y):
                    del rest[i]
                    break
            else:
                return False
        return True
    if isinstance(b, dict):
        if not isinstance(a, dict) or len(a) != len(b):
            return False
        a = {str(k): v for k, v in a.items()}
        return all(str(k) in a and lik(a[str(k)], v) for k, v in b.items())
    try:
        a, b = sympy.sympify(a), sympy.sympify(b)
    except (sympy.SympifyError, TypeError):
        return False
    vanlige = lambda u: u.subs({s: sympy.Symbol(s.name) for s in u.free_symbols})
    a, b = vanlige(a), vanlige(b)
    if isinstance(a, sympy.Set) or isinstance(b, sympy.Set):
        return a == b
    if getattr(b, "is_Relational", False):
        return a == b
    try:
        return sympy.simplify(a - b) == 0
    except TypeError:
        return a == b

oppgave = last_notebook("oppgave")

SJEKKER = [
    ('1_temp', 'temperaturer(varsel) skal gi listen med air_temperature', "lik(temperaturer({'properties': {'timeseries': [{'time': '2026-10-26T19:00:00Z', 'data': {'instant': {'details': {'air_temperature': 8.1, 'wind_speed': 4.2}}}}, {'time': '2026-10-26T20:00:00Z', 'data': {'instant': {'details': {'air_temperature': 7.4, 'wind_speed': 5.0}}}}, {'time': '2026-10-26T21:00:00Z', 'data': {'instant': {'details': {'air_temperature': 6.9, 'wind_speed': 3.1}}}}]}}), [8.1, 7.4, 6.9]) and list(temperaturer({'properties': {'timeseries': [{'time': '2026-10-26T19:00:00Z', 'data': {'instant': {'details': {'air_temperature': 8.1, 'wind_speed': 4.2}}}}, {'time': '2026-10-26T20:00:00Z', 'data': {'instant': {'details': {'air_temperature': 7.4, 'wind_speed': 5.0}}}}, {'time': '2026-10-26T21:00:00Z', 'data': {'instant': {'details': {'air_temperature': 6.9, 'wind_speed': 3.1}}}}]}}))[0] == 8.1"),
    ('1_vind', 'vindstyrker(varsel) skal gi listen med wind_speed', "list(vindstyrker({'properties': {'timeseries': [{'time': '2026-10-26T19:00:00Z', 'data': {'instant': {'details': {'air_temperature': 8.1, 'wind_speed': 4.2}}}}, {'time': '2026-10-26T20:00:00Z', 'data': {'instant': {'details': {'air_temperature': 7.4, 'wind_speed': 5.0}}}}, {'time': '2026-10-26T21:00:00Z', 'data': {'instant': {'details': {'air_temperature': 6.9, 'wind_speed': 3.1}}}}]}})) == [4.2, 5.0, 3.1]"),
    ('1_rekkefolge', 'temperaturer skal komme i samme rekkefølge som tidspunktene', "list(temperaturer({'properties': {'timeseries': [{'time': '2026-10-26T19:00:00Z', 'data': {'instant': {'details': {'air_temperature': 8.1, 'wind_speed': 4.2}}}}, {'time': '2026-10-26T20:00:00Z', 'data': {'instant': {'details': {'air_temperature': 7.4, 'wind_speed': 5.0}}}}, {'time': '2026-10-26T21:00:00Z', 'data': {'instant': {'details': {'air_temperature': 6.9, 'wind_speed': 3.1}}}}]}})) == [8.1, 7.4, 6.9]"),
    ('3_eksempel', "aarsmiddel(['2000-01-01', '2000-06-01', '2001-01-01'], [0, 10, 3]) skal gi {2000: 5.0, 2001: 3.0}", "aarsmiddel(['2000-01-01', '2000-06-01', '2001-01-01'], [0, 10, 3]) == {2000: 5.0, 2001: 3.0}"),
    ('3_mange', 'aarsmiddel skal regne gjennomsnittet av alle dagene i året', "naer(aarsmiddel(['1999-01-01', '1999-01-02', '1999-01-03', '1999-12-31'], [1, 2, 3, 6])[1999], 3)"),
    ('4', 'varmeste_dag skal gi datoen og temperaturen for den varmeste dagen', "tuple(varmeste_dag(['2020-07-01', '2020-07-02', '2020-07-03'], [18.5, 24.1, 21.0])) == ('2020-07-02', 24.1)"),
]


@pytest.mark.parametrize(
    "beskrivelse,uttrykk", [s[1:] for s in SJEKKER], ids=[s[0] for s in SJEKKER]
)
def test_sjekk(beskrivelse, uttrykk):
    navnerom = {**vars(oppgave), "naer": naer, "lik": lik, "S": S}
    assert eval(uttrykk, navnerom), beskrivelse
