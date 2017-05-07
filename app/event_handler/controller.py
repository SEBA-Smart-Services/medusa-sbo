from app import notifier

class EventHandler():

    def handle_result(result):
        if result.passed == True and result.priority > min(result.site.email_trigger_priority, result.site.cmms_trigger_priority) and result.occurances == 1:
            notifier.send_issue(result)
