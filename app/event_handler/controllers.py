from app import notifier

class EventHandler():

    def handle_result(self, result):
        if result.passed == True and result.priority > min(result.asset.site.email_trigger_priority, result.asset.site.cmms_trigger_priority) and result.occurances == 1:
            notifier.send_issue(result)
