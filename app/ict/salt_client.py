import requests
import json
import logging
from app import app

class SaltAPI():

    def __init__(self, **kwargs):
        self.token = None

        self.salt_host = app.config["SALT_HOST"]
        self.salt_username = app.config["SALT_USER"]
        self.salt_password = app.config["SALT_PASSWORD"]
        ###NEEED TO FIX SO THAT IT USES SSL!!!!!!!!!!!!!
        self.verify_ssl_cert = kwargs.get("verify_ssl_cert", False)

    def login(self):
        req = requests.post(self.salt_host + "/login", data={"eauth": "pam", "username": self.salt_username, "password": self.salt_password}, headers={"Accept": "application/json"}, verify=self.verify_ssl_cert, timeout=5.0)
        if req.status_code != 200:
            print(req.text)
            print(req.status_code)
            print("Signing into salt failed")
        logging.debug("Salt login response: %s - %s", req.status_code, req.text)
        if req.status_code != 200:
            print("Signing into salt failed")
        resp = req.json()
        self.token = resp["return"][0]["token"]
        return self.token

    def logout(self):
        req = requests.post(self.salt_host +"/logout", headers=self._get_headers(), verify = self.verify_ssl_cert)
        return 1

    def _get_headers(self):
        return {"Accept": "application/json", "X-Auth-Token": self.token}

    def checkComms(self):
        req = requests.get(self.salt_host, verify = self.verify_ssl_cert)
        code = req.status_code
        resp = 0
        if code == 200:
            resp = 1 #200 = connection good
        return resp

    def is_minion_reachable(self, minion_id):
        req = requests.post(self.salt_host, data={"client": "local", "tgt": minion_id, "fun": "test.ping"}, headers=self._get_headers(), verify=self.verify_ssl_cert)
        logging.debug("Salt ping response: %s - %s", req.status_code, req.text)
        resp = req.json()

        #if ping succeeds, resp== {'return': [{'minion_name':True}]}
        #if ping fails, resp=={'return':[{}]}

        if resp["return"][0].get(minion_id, None):   #returns true if the minion name can be found in the responce
            return resp["return"][0][minion_id]
        else:
            return False

    def get_minion_grains(self, minion_id):
        #the minion must be online for grains to be checked
        #function will fail if minion is offline
        req = requests.get(self.salt_host + "/minions/" + minion_id, headers=self._get_headers(), verify=self.verify_ssl_cert)
        resp = req.json()
        data = resp["return"][0]
        data2 = data[minion_id]
        return data2

    def get_salt_minion_keys(self):
        #nb, the external user configured in the salt master config file must have access to @wheel
        req = requests.get(self.salt_host + "/keys", headers=self._get_headers(), verify=self.verify_ssl_cert)
        resp = req.json()
        data = resp["return"]
        unaccepted_minions = data["minions_pre"]
        accepted_minions = data["minions"]
        return accepted_minions, unaccepted_minions

        keyname = "perfcentre-chris-01"
        payload = {'fun': 'key.accept','client':'wheel','tgt':'*','match':keyname}
        req = requests.post(api.salt_host, headers=api._get_headers(),data=payload,verify=api.verify_ssl_cert)

    def accept_salt_minion_key(self, minion_name):
        keyname = minion_name
        payload = {'fun': 'key.accept','client':'wheel','tgt':'*','match':keyname}
        req = requests.post(self.salt_host, headers=self._get_headers(),data=payload,verify=self.verify_ssl_cert)
        if req.status_code!=200:
            return False
        resp=req.json()
        data=resp['return'][0]['data']
        if data['success']==1 and data['return']['minions'][0]==minion_name:
            return True
        else:
            return False

    def get_minion_isntalled_services(self, minion_name):
        keyname = minion_name
        payload = {'client':'local','tgt':keyname, 'fun': 'service.get_all'}
        req = requests.post(self.salt_host, headers=self._get_headers(),data=payload,verify=self.verify_ssl_cert)
        if req.status_code != 200:
            return [""]
        elif req.status_code == 200:
            resp=req.json()
            data=resp["return"][0][keyname]
            return data
