from app.notification import Notifier
import app

class EventHandler():

    def __init__(self):
        self.notifier = Notifier()

    def handle_result(self, result):
        if result.passed == False and result.priority < max(result.asset.site.email_trigger_priority, result.asset.site.cmms_trigger_priority) and result.occurances == 1:
            self.notifier.send_issue(result)

    def sync_cmms(self):
        pass
        #app.inbuildings.controllers.inbuildings_request_all_sites()
