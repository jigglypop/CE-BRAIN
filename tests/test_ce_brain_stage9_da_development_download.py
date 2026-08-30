from examples.brain import ce_brain_stage9_da_development_download as download


def test_selection_is_exactly_seven_development_animals_and_locked_split_day():
    rows = download.selected_rows()
    assert len(rows) == 57
    assert {row["path"].split("/")[0] for row in rows} == set(download.DEVELOPMENT)
    assert all("ses-day" in row["path"] for row in rows)
    assert sum("sub-60sD-F8_ses-day02" in row["path"] for row in rows) == 2
