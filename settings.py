import json
from pathlib import Path


settings_dir = Path("settings")

if not settings_dir.exists():
    settings_dir.mkdir()

class ChatSettings:

    def __init__(self, chat_id):
        self.chat_id = chat_id

    @property
    def all_settings(self):
        settings_file = settings_dir / f"{self.chat_id}.json"
        if settings_file.exists():
            with open(settings_file, "r") as json_data:
                return json.load(json_data)
        return {}

    def modify_settings(
        self,
        language=None,
        summary_level=None
    ):
        settings_file = settings_dir / f"{self.chat_id}.json"
        settings = self.all_settings
        if language:
            settings["language"] = language
        if summary_level:
            settings["summary_level"] = summary_level
        with open(settings_file, "w") as json_data:
            json.dump(settings, json_data)

    def is_configured(self, setting_name):
        return setting_name in self.all_settings

    @property
    def language(self):
        if "language" in self.all_settings:
            return self.all_settings["language"]
        return "original"

    @property
    def summary_level(self):
        if "summary_level" in self.all_settings:
            return self.all_settings["summary_level"]
        return "ON"
