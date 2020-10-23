import requests

class clist:
    def contests(self):
        try:
            resp = requests.get('https://clist.by/api/v1/json/contest/?limit=500&order_by=-start', headers= {
                'Authorization': 'ApiKey joynahiid:339ccb7ec3e1dff04de10312f4d8811c0ad7c35a'
            })

            return resp.json()
        except Exception as e:
            print('api_clist', e)

clistApi = clist()