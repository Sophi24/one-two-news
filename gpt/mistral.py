from mistralai import Mistral

MI_API = None

MI_MODEL = None
MI_SYSTEM = None

MI_MODEL_EMB = None
MI_SYSTEM_CH = None


def mi_rating_get(txt:str) -> str:
    client = Mistral(api_key=MI_API)

    response = client.chat.complete(
        model= MI_MODEL,
        temperature=0,
        messages = [
            {
                'role': 'system',
                'content': MI_SYSTEM,
            },
            {
                'role': 'user',
                'content': f'Text: {txt}'
            }    
        ]
    )
    response_txt = response.choices[0].message.content
    print(response_txt)
    return response_txt


def mi_sel(choices:str, txt:str) -> str:
    client = Mistral(api_key=MI_API)

    response = client.chat.complete(
        model= MI_MODEL_EMB,
        temperature=0,
        messages = [
            {
                'role': 'system',
                'content': MI_SYSTEM_CH.replace('@@@', txt),
            },
            {
                'role': 'user',
                'content': f'{choices}'
            }    
        ]
    )
    print(response)
    response_txt = response.choices[0].message.content
    print(response_txt)
    return response_txt
