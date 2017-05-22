from .inbuildings import inbuildings_asset_request, inbuildings_raise_job

class CMMS():

    def raise_job_inbuildings(issue):
        inbuildings_raise_job(asset=issue.asset, message=issue.algorithm.descr, priority=issue.asset.priority)

    def get_assets_inbuildings(site):
        inbuildings_asset_request(site)
