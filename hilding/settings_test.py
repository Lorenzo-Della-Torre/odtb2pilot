"""
pytest for hilding/settings.py
"""
from tempfile import TemporaryFile
from settings import Settings

def test_settings():
    """ pytest: setting parsing """
    settings_file_content = b"""
    default_rig: p2
    rigs:
      - p2:
          hostname: host2.domain
          user: pi #optional
          platform: spa2
          signal_broker_port: 50051 #optional
    """
    settings_file = TemporaryFile()
    settings_file.write(settings_file_content)
    settings_file.seek(0)
    settings = Settings(settings_file_name=None)
    settings.read_settings_file(settings_file)
    assert settings.settings['default_rig'] == "p2"
    assert settings.hostname == "host2.domain"

def test_settings_yml():
    """ pytest: settings.yml parsing """
    settings = Settings()
    print(settings)
    assert settings.settings['default_rig'] == "p8"
    assert settings.hostname == "host2.domain"
