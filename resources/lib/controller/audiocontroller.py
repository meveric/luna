import xbmcgui
from resources.lib.controller.basecontroller import BaseController, route


class AudioController(BaseController):
    def __init__(self, core, audio_manager, config_helper):
        self.core = core
        self.audio_manager = audio_manager
        self.config_helper = config_helper

    @route(name="select")
    def select_audio_device(self):
        device_list = [dev.get_name() for dev in self.audio_manager.devices]
        device_list.append('sysdefault')
        audio_device = xbmcgui.Dialog().select('Choose Audio Device', device_list)

        if audio_device != -1:
            device_name = device_list[audio_device]
            device = self.audio_manager.get_device_by_name(device_name)
            if device:
                self.core.set_setting('audio_device', device.handler)
                self.core.set_setting('audio_device_name', device.name)

        return
