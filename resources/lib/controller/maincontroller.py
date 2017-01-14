import threading

from requests import ConnectionError

from resources.lib.controller.basecontroller import BaseController, route
from resources.lib.nvhttp.request.staticrequestservice import StaticRequestService

from resources.lib.views.main import Main


class MainController(BaseController):
    def __init__(self, host_context_service, host_manager, logger):
        super(MainController, self).__init__()
        self.host_context_service = host_context_service
        self.host_manager = host_manager
        self.logger = logger
        self.window = None

    @route(name="index")
    def index_action(self):
        self.window = Main(controller=self, hosts=self.get_hosts())
        self.update_host_status()
        self.window.doModal()
        del self.window

    @route(name="host_select")
    def select_host(self, host):
        self.host_context_service.set_current_context(host)
        self.render('game_list', {'host': host})
        # window = GameList(host)
        # window.doModal()

    @route(name="add_host")
    def add_host(self):
        ret_val = self.render('host_add')
        if ret_val:
            self.window.update()

    @route(name="host_remove")
    def remove_host(self, host):
        ret_val = self.render('host_remove', {'host': host})
        if ret_val:
            self.window.update()

    def update_host_status(self):
        update_host_thread = threading.Thread(target=self._update_host_status)
        update_host_thread.start()

    def _update_host_status(self):
        import xbmcgui
        self.logger.info("Getting Host Status")
        background_dialog = xbmcgui.DialogProgressBG()
        background_dialog.create('Refreshing Host Status')
        hosts = self.host_manager.get_hosts()
        for key, host in hosts.iteritems():
            try:
                StaticRequestService.get_static_server_info(host.local_ip)
                host.state = host.STATE_ONLINE
            except ConnectionError:
                host.state = host.STATE_OFFLINE
        self.window.update_host_status(hosts.raw_dict())
        self.logger.info("Getting Host Status ... Done")
        background_dialog.close()
        del background_dialog
        return

    def get_hosts(self):
        return self.host_manager.get_hosts()
