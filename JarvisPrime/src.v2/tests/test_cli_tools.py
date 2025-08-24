from src.cli.jarvisctl import main


def test_cli_dfs_portfolio(capsys):
    main(["dfs-portfolio", "--n", "1"])
    out = capsys.readouterr().out
    assert "lineups" in out


def test_cli_roi_report(capsys):
    main(["roi-report", "--days", "10"])
    out = capsys.readouterr().out
    assert "top" in out
