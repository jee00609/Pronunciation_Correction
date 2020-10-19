import urllib3
import json
import base64

import urllib3
from typing import Dict

def proCorrect(myScript):
    openApiURL = "http://aiopen.etri.re.kr:8000/WiseASR/Pronunciation"
    accessKey = "api 키"
    audioFilePath = "audio/test.raw"
    languageCode = "english"
    script = myScript

    file = open(audioFilePath, "rb")
    audioContents = base64.b64encode(file.read()).decode("utf8")
    file.close()

    requestJson = {
        "access_key": accessKey,
        "argument": {
            "language_code": languageCode,
            "script" : script,
            "audio": audioContents
        }
    }

    http = urllib3.PoolManager()
    response = http.request(
        "POST",
        openApiURL,
        headers={"Content-Type": "application/json; charset=UTF-8"},
        body=json.dumps(requestJson)
    )

    result = json.loads(response.data.decode('utf-8'))

    score = result['return_object']['score']
    score = round(score,2)
    return score