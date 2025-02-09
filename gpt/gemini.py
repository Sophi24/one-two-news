import google.generativeai as genai

GM_API = None
GM_MODEL = None
GM_SYSTEM = None
GM_SYSTEM = None

GM_MODEL_EMB = None
GM_SYSTEM_DG= None


def gm_digest_get(txt:str) -> str:
    genai.configure(api_key=GM_API)

    generation_config = {
        "temperature": 0.3,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        system_instruction=GM_SYSTEM_DG,
    )

    # model = genai.GenerativeModel(
    #     model_name=GM_MODEL,
    #     safety_settings={
    #             'HATE': 'BLOCK_NONE',
    #             'HARASSMENT': 'BLOCK_NONE',
    #             'SEXUAL' : 'BLOCK_NONE',
    #             'DANGEROUS' : 'BLOCK_NONE'
    #         },
    #     system_instruction=GM_SYSTEM_DG)

    response = model.generate_content(
        txt,
        generation_config=genai.types.GenerationConfig(
            candidate_count=1,
            # stop_sequences=["x"],
            # max_output_tokens=500,
            temperature=0.3,
            top_p=0.95,
            top_k=64,
            response_mime_type='text/plain',
        ),
    )


    chat_session = model.start_chat(
    history=[
        ]
    )

    response = chat_session.send_message(txt)

    # print('>>>', response)
    response_txt = response.text
    print(response_txt)
    return response_txt


def gm_rating_get(txt:str) -> str:
    print(txt)
    genai.configure(api_key=GM_API)

    model = genai.GenerativeModel(
        model_name=GM_MODEL,
        safety_settings={
                'HATE': 'BLOCK_NONE',
                'HARASSMENT': 'BLOCK_NONE',
                'SEXUAL' : 'BLOCK_NONE',
                'DANGEROUS' : 'BLOCK_NONE'
            },
        system_instruction=GM_SYSTEM)

    response = model.generate_content(
        txt,
        generation_config=genai.types.GenerationConfig(
            candidate_count=1,
            # stop_sequences=["x"],
            max_output_tokens=500,
            temperature=0,
            top_p=0.95,
            top_k=64,
            response_mime_type='text/plain',
        ),
    )

    # print('>>>', response)
    response_txt = response.text
    print(response_txt)
    return response_txt


def gm_sel(choices:str, txt:str) -> str:
    print(txt)
    genai.configure(api_key=GM_API)

    model = genai.GenerativeModel(
        model_name=GM_MODEL_EMB,
        safety_settings={
                'HATE': 'BLOCK_NONE',
                'HARASSMENT': 'BLOCK_NONE',
                'SEXUAL' : 'BLOCK_NONE',
                'DANGEROUS' : 'BLOCK_NONE'
            },
        system_instruction=GM_SYSTEM_CH.replace('@@@', txt))

    response = model.generate_content(
        choices,
        generation_config=genai.types.GenerationConfig(
            candidate_count=1,
            # stop_sequences=["x"],
            max_output_tokens=500,
            temperature=0,
            top_p=0.95,
            top_k=64,
            response_mime_type='text/plain',
        ),
    )

    print('>>>', response)
    response_txt = response.text
    print(response_txt)
    return response_txt




