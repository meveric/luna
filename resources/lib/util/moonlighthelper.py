import Queue
import os
import subprocess
import threading

import xbmc

from resources.lib.model.inputmap import InputMap
from resources.lib.util.inputwrapper import InputWrapper
from resources.lib.util.stoppableinputhandler import StoppableInputHandler
from resources.lib.util.stoppablejshandler import StoppableJSHandler


def loop_lines(dialog, iterator):
    """
    :type dialog:   DialogProgress
    :type iterator: iterator
    """
    for line in iterator:
        dialog.update(0, line)


class MoonlightHelper:
    regex_connect = '(Connect to)'
    regex_moonlight = '(Moonlight Embedded)'
    regex_certificate_gen = '(Generating certificate...done)'
    regex_connection_failed = '(Can\'t connect to server)'

    def __init__(self, core, config_helper, host_context_service, request_service, logger):
        self.core = core
        self.config_helper = config_helper
        self.host_context_service = host_context_service
        self.request_service = request_service
        self.logger = logger
        self.internal_path = core.internal_path

    def create_ctrl_map(self, dialog, map_file):
        mapping_proc = subprocess.Popen(
            ['stdbuf', '-oL', self.config_helper.get_binary(), 'map', map_file, '-input',
             self.core.get_setting('input_device', unicode)], stdout=subprocess.PIPE)

        lines_iterator = iter(mapping_proc.stdout.readline, b"")

        mapping_thread = threading.Thread(target=loop_lines, args=(dialog, lines_iterator))
        mapping_thread.start()

        # TODO: Make a method or function from this
        while True:
            xbmc.sleep(1000)
            if not mapping_thread.isAlive():
                dialog.close()
                success = True
                break
            if dialog.iscanceled():
                mapping_proc.kill()
                dialog.close()
                success = False
                break

        if os.path.isfile(map_file) and success:

            return True
        else:

            return False

    def create_ctrl_map_new(self, dialog, map_file, device):
        # TODO: Implementation detail which should be hidden?
        input_queue = Queue.Queue()
        input_map = InputMap(map_file)
        input_device = None

        for handler in device.handlers:
            if handler[:-1] == 'js':
                input_device = os.path.join('/dev/input', handler)

        if not input_device:
            return False

        input_wrapper = InputWrapper(input_device, device.name, input_queue, input_map)
        input_wrapper.build_controller_map()

        print 'num buttons: %s' % input_wrapper.num_buttons
        print 'num_axes: %s' % input_wrapper.num_axes
        expected_input_number = input_wrapper.num_buttons + (input_wrapper.num_axes * 2)

        js = StoppableJSHandler(input_wrapper, input_map)
        it = StoppableInputHandler(input_queue, input_map, dialog, expected_input_number)

        success = False

        while True:
            xbmc.sleep(1000)
            if not it.isAlive():
                js.stop()
                dialog.close()
                js.join(timeout=2)
                if input_map.status == InputMap.STATUS_DONE:
                    success = True
                if input_map.status == InputMap.STATUS_PENDING or input_map.status == InputMap.STATUS_ERROR:
                    success = False
                break
            if dialog.iscanceled():
                it.stop()
                js.stop()
                success = False
                it.join(timeout=2)
                js.join(timeout=2)
                dialog.close()
                break

        if os.path.isfile(map_file) and success:

            return True
        else:

            return False

    def launch_game(self, game_id):
        self.config_helper.configure()
        host = self.host_context_service.get_current_context()

        (pre_script, post_script) = self.core.prepare_init_scripts()

        self.logger.info("Got script paths: %s and %s" % (pre_script, post_script))

        subprocess.call([
            self.internal_path + '/resources/lib/launchscripts/osmc/launch-helper-osmc.sh',
            self.internal_path + '/resources/lib/launchscripts/osmc/launch.sh',
            self.internal_path + '/resources/lib/launchscripts/osmc/moonlight-heartbeat.sh',
            host.local_ip,
            host.key_dir,
            game_id,
            self.config_helper.get_config_path(),
            self.core.get_setting('enable_moonlight_debug', str),
            pre_script,
            post_script
        ])

    def list_games(self):
        return self.request_service.get_app_list()
