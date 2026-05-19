from click.testing import CliRunner
from questions.cli import cli
from pathlib import Path

def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'ai' in result.output
    assert 'validate' in result.output

def test_cli_validate_file(tmp_path):
    f = tmp_path / "test.gift"
    f.write_text("::Title:: Q{=A}")
    
    runner = CliRunner()
    result = runner.invoke(cli, ['validate', str(f)])
    assert result.exit_code == 0
    assert 'Archivo válido' in result.output

def test_cli_format(tmp_path):
    f = tmp_path / "test.gift"
    f.write_text("::T::Q{=A}")
    
    runner = CliRunner()
    result = runner.invoke(cli, ['format', str(f)])
    assert result.exit_code == 0
    assert 'MODIFICADO' in result.output
    
    # Verify formatted content
    content = f.read_text()
    assert '    =A' in content

def test_cli_fix_slugify(tmp_path):
    f = tmp_path / "Test Name.gift"
    f.write_text("::T::Q{=A}")
    
    runner = CliRunner()
    result = runner.invoke(cli, ['fix', 'slugify', str(f)])
    assert result.exit_code == 0
    assert 'test_name.gift' in result.output
    assert not f.exists()
    assert (tmp_path / "test_name.gift").exists()
