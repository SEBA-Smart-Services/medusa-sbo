from .inbuildings import inbuildings_asset_request, inbuildings_raise_job

class CMMS():

    def raise_job_inbuildings(self, issue):
        inbuildings_raise_job(asset=issue.asset, message=issue.algorithm.descr, priority=issue.asset.priority)

    def get_assets_inbuildings(self, site):
        inbuildings_asset_request(site)
