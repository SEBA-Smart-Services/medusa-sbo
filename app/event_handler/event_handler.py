from app.notification import Notifier
import app

class EventHandler():

    def __init__(self):
        self.notifier = Notifier()

    def handle_result(self, result):
        if self.test_for_notification(result):
            self.notifier.send_issue(result)
            
    def test_priority(self, result):
        return result.priority < max(result.asset.site.email_trigger_priority, result.asset.site.cmms_trigger_priority)
    
    def test_for_notification(self, result):
        """
        testing if an issue meets the requirements to trigger a notification.
        
        must pass 3 tests:
        1. must fail the algo check
        2. must be above site notification priority
        3. same issue must not have already been notified
        
        """
        return (
            result.passed == False and \
            self.test_priority(result) and \
            result.occurances == 1
        )

    def sync_cmms(self):
        pass
        #app.inbuildings.controllers.inbuildings_request_all_sites()
