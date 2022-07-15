# Copyright 2021 Aditya Mehra <aix.m@outlook.com>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from mycroft_bus_client import Message
from ovos_plugin_manager.phal import PHALPlugin
from ovos_config.config import read_mycroft_config, update_mycroft_config


class ConfigurationProviderPlugin(PHALPlugin):
    def __init__(self, bus=None, config=None):
        super().__init__(bus=bus, name="ovos-PHAL-plugin-configuration-provider", config=config)
        self.bus = bus
        self.build_settings_meta()
        self.settings_meta = None

        self.bus.on("ovos.phal.configuration.provider.get",
                    self.get_settings_meta)
        self.bus.on("ovos.phal.configuration.provider.set",
                    self.set_settings_meta)

    def build_settings_meta(self):
        readable_config = read_mycroft_config()
        misc = {}
        new_config = {}

        for key in readable_config:
            if type(readable_config[key]) is not dict:
                misc[key] = readable_config[key]
            if type(readable_config[key]) is dict:
                new_config[key] = readable_config[key]

        new_config["misc"] = misc
        settingsmetadata = {}

        for key in new_config:
            settingsmetadata[key] = {}
            settingsmetadata[key]["fields"] = []
            for subkey in new_config[key]:
                field = self.generate_field(subkey, type(
                    new_config[key][subkey]), new_config[key][subkey])
                settingsmetadata[key]["fields"].append(field)

            if len(settingsmetadata[key]["fields"]) == 0:
                del settingsmetadata[key]["fields"]

            if "fields" not in settingsmetadata[key]:
                del settingsmetadata[key]

            self.settings_meta = settingsmetadata

    def generate_fields(self, value):
        fields = []
        for key in value:
            field = self.generate_field(key, type(value[key]), value[key])
            fields.append(field)
        return fields

    def generate_field(self, key, type, value):
        key = key
        type = type
        value = value
        field = {}
        field["name"] = key
        field["label"] = key.capitalize().replace("_", " ")
        field["type"] = type.__name__
        if type is dict:
            field["fields"] = self.generate_fields(value)
        else:
            field["value"] = value

        return field

    def get_settings_meta(self, message=None):
        section = message.data.get("section")
        if section is None:
            self.bus.emit(Message("ovos.configuration.provider.get.response", {
                          "settingsmetadata": self.settings_meta}))
        else:
            if section in self.settings_meta:
                self.bus.emit(Message("ovos.configuration.provider.get.response", {
                              "settingsmetadata": self.settings_meta[section]}))
            else:
                self.bus.emit(Message("ovos.configuration.provider.get.response", {
                              "settingsmetadata": None}))

    def set_settings_in_config(self, message=None):
        section = message.data.get("section")
        section_data = message.data.get("section_data")
        mycroft_config = read_mycroft_config()

        config = {}
        if section in mycroft_config:
            config.update(mycroft_config[section])

        for key in config:
            if key in section_data:
                config[key] = section_data[key]

        update_mycroft_config(config)
