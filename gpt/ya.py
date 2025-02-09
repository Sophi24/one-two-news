import requests

YA_OAUTH = None
YA_FOLDER_ID = None
YA_GPT_REQUEST = None


def ya_iam_get() -> str:
    post_data = {'yandexPassportOauthToken': YA_OAUTH}
    response = requests.post('https://iam.api.cloud.yandex.net/iam/v1/tokens', json = post_data)
    # print('IAM', response.status_code)
    # print('IAM', response.json()['iamToken'])
    return response.json()['iamToken']


def ya_rating_get(txt:str) -> str:
    ya_aim = ya_iam_get()
    headers = {
        'Content-Type' : 'application/json',
        'Authorization': f'Bearer {ya_aim}',
        'x-folder-id': YA_FOLDER_ID,
        }

    post_data = YA_GPT_REQUEST
    post_data['text'] = f'Текст: {txt}'

    response = requests.post('https://llm.api.cloud.yandex.net/foundationModels/v1/fewShotTextClassification', json = post_data, headers=headers)
    # print(response.status_code)
    # print(response.json())
    # response_txt = str(response.json())
    response_txt = ''
    
    # 80%
    for el in response.json()['predictions']:
        if el['confidence']>0.80:
            response_txt = el['label']
    
    # 30%
    if len(response_txt) <1:
        for el in response.json()['predictions']:
            if el['confidence']>0.30:
                response_txt += el['label'] + ', '
    
    # 20%
    if len(response_txt) <1:
        for el in response.json()['predictions']:
            if el['confidence']>0.20:
                response_txt += el['label'] + ', '

    print(response_txt)

    return response_txt, str(response.json())


