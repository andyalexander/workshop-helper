"""The Result contract an Applet returns (spec §6)."""

import pytest

from workshop_utils import Result, Row, Table


def test_outputs_are_the_only_required_channel() -> None:
    result = Result(outputs={"allowance": 3.4})

    assert result.outputs == {"allowance": 3.4}
    assert result.table is None
    assert result.html is None
    assert result.graphic is None


def test_a_table_is_a_header_row_plus_rows() -> None:
    table = Table(columns=["Series", "Pitch"], rows=[Row(["ISO metric", 1.25])])

    assert table.columns == ("Series", "Pitch")
    assert table.rows[0].cells == ("ISO metric", 1.25)
    assert table.rows[0].flag is None


def test_sequences_are_normalised_so_two_equal_tables_compare_equal() -> None:
    """Authors write list literals; the Result stays a comparable value."""
    assert Table(columns=["A"], rows=[Row(["x"])]) == Table(
        columns=("A",), rows=(Row(("x",)),)
    )


def test_a_row_that_does_not_fit_the_header_is_an_error() -> None:
    """Caught in `compute()`, so it renders as a compute-time fault (§10.2)."""
    with pytest.raises(ValueError, match="2 columns"):
        Table(columns=["Series", "Pitch"], rows=[Row(["ISO metric"])])


def test_consecutive_rows_sharing_a_flag_are_one_group() -> None:
    """The whole of the tied-group model: a flag, and adjacency (§11.3)."""
    tied = "Indistinguishable — differ only in flank angle"
    table = Table(
        columns=["Designation"],
        rows=[
            Row(["1/4in UNC"], flag=tied),
            Row(["1/4in BSW"], flag=tied),
            Row(["M6"]),
        ],
    )

    assert [(flag, len(rows)) for flag, rows in table.groups()] == [
        (tied, 2),
        (None, 1),
    ]


def test_the_same_flag_twice_over_is_two_groups() -> None:
    """Adjacency, not string equality: two collisions are two refusals."""
    table = Table(
        columns=["Designation"],
        rows=[Row(["A"], flag="tied"), Row(["B"]), Row(["C"], flag="tied")],
    )

    assert [len(rows) for _, rows in table.groups()] == [1, 1, 1]
