from src.tools import interaction


def test_shell_echo():
    assert interaction.shell("echo hello") == "hello"


def test_shell_reject():
    try:
        interaction.shell("rm -rf /")
    except ValueError:
        pass
    else:
        assert False, "disallowed command should raise"


def test_web_fetch_example():
    text = interaction.web_fetch("https://example.com")
    assert "Example Domain" in text


def test_speak_and_listen():
    assert interaction.speak("hi").startswith("speaking: hi")
    assert interaction.listen("hi").startswith("heard: hi")
