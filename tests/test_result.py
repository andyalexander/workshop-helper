"""The Result contract an Applet returns (spec §6)."""

import pytest

from workshop_utils import Group, Result, Row, Table


def test_outputs_are_the_only_required_channel() -> None:
    result = Result(outputs={"allowance": 3.4})

    assert result.outputs == {"allowance": 3.4}
    assert result.table is None
    assert result.html is None
    assert result.graphic is None


def test_a_table_is_a_header_row_plus_rows() -> None:
    table = Table(columns=["Series", "Pitch"], rows=[Row(["ISO metric", 1.25])])

    assert table.columns == ("Series", "Pitch")
    ((row,),) = [group.rows for group in table.groups()]
    assert row.cells == ("ISO metric", 1.25)


def test_sequences_are_normalised_so_two_equal_tables_compare_equal() -> None:
    """Authors write list literals; the Result stays a comparable value."""
    assert Table(columns=["A"], rows=[Row(["x"])]) == Table(
        columns=("A",), rows=(Row(("x",)),)
    )


@pytest.mark.parametrize(
    "rows",
    [
        [Row(["ISO metric"])],
        [Group([Row(["ISO metric"])], flag="tied")],
    ],
)
def test_a_row_that_does_not_fit_the_header_is_an_error(rows: list[object]) -> None:
    """Caught in `compute()`, so it renders as a compute-time fault (§10.2)."""
    with pytest.raises(ValueError, match="2 columns"):
        Table(columns=["Series", "Pitch"], rows=rows)  # type: ignore[arg-type]


def test_every_entry_reads_as_a_group_so_rendering_has_one_shape() -> None:
    tied = "Indistinguishable — differ only in flank angle"
    table = Table(
        columns=["Designation"],
        rows=[
            Group([Row(['1/4" UNC']), Row(['1/4" BSW'])], flag=tied),
            Row(["M6"]),
        ],
    )

    assert [(group.flag, len(group.rows)) for group in table.groups()] == [
        (tied, 2),
        (None, 1),
    ]


def test_two_collisions_that_read_alike_stay_two_groups() -> None:
    """The Applet draws the boundary; no rule over the rows could find it."""
    table = Table(
        columns=["Designation"],
        rows=[
            Group([Row(["13 BA"]), Row(["M1.2"])], flag="tied"),
            Group([Row(["14 BA"]), Row(["M1"])], flag="tied"),
        ],
    )

    assert [len(group.rows) for group in table.groups()] == [2, 2]
