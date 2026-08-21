from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_systemd_runner_does_not_install_dependencies_at_service_start() -> None:
    runner = (ROOT_DIR / "scripts" / "run_systemd_instance.sh").read_text()

    assert "bootstrap_venv.sh" not in runner
