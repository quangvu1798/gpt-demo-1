import streamlit as st
from .process import construct_prompt, COMPLETIONS_API_PARAMS, count_tokens
import openai
import re
import os
from streamlit_chat import message
key = os.environ.get('OPENAI_KEY')
REPLACE_API_PARAMS = COMPLETIONS_API_PARAMS.copy()

def key_input():
    rkey = st.sidebar.text_input('OpenAI Key')
    if st.sidebar.checkbox('Key thay thế'):
        openai.api_key = rkey

def param_input():
    REPLACE_API_PARAMS['temperature'] = st.sidebar.slider(
        'temperature', min_value = 0.0, max_value = 2.0, value = COMPLETIONS_API_PARAMS['temperature'], step = 0.01
    )
    REPLACE_API_PARAMS['top_p'] = st.sidebar.slider(
        'top_p', min_value = 0.0, max_value = 1.0, value = COMPLETIONS_API_PARAMS['top_p'], step = 0.01
    )

def parse_response(response, used):
    response = response.replace(r'\n', '\n\n')
    links = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', response)
    if len(links) > 0:
        for link in links:
            if link[-4:] in ['.jpg', '.png', 'jpeg', '.gif'] and link not in used:
                used.append(link)
                response = response.replace(link, f'![image]({link})')
            elif link.startswith('https://player.vimeo.com/video/') and link not in used and len(link.rsplit('/', 1)[-1]) == 9:
                link = link.strip('.')
                used.append(link)
                response = response.replace(link, f'<iframe src="{link}?autoplay=1&loop=1&title=0&byline=0&portrait=0" width="640" height="360" frameborder="0" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe>')
            elif link.startswith('https://www.youtube.com/embed/') and link not in used and len(link.rsplit('/', 1)[-1]) == 11:
                link = link.strip('.')
                used.append(link)
                response = response.replace(link, f'<iframe src="{link}" width="640" height="360" frameborder="0" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe>')
    return response

def sumary_question(ques):
    openai.api_key = key
    mess = [
        {"role": "system", "content":"Tóm tắt câu hỏi của user thành 1 câu, chỉ đưa ra câu tóm tắt"},
        {"role": "user", "content": f"Tóm tắt câu hỏi: {ques}"}
    ]
    PARAMS = {
        'temperature': 0.0,
        'top_p': 0.0,
        'max_tokens': 100,
        'model': 'gpt-3.5-turbo',
        'stream': False
    }
    res = openai.ChatCompletion.create(messages = mess, **PARAMS)
    return res.choices[0].message.content.replace("Tóm tắt:", "")

messages = [
            {"role": "system", "content": 'Hướng dẫn: Trả lời chi tiết dựa vào tri thức (chỉ đưa ra link http và ký tự "\\n" nếu có trong tri thức của MISA)\nChú ý: Nếu câu trả lời không ở trong tri thức MISA, tự trả lời theo tri thức của mình.'}
        ]

def generate_response(messages):
    REPLACE_API_PARAMS["stream"] = False
    response = openai.ChatCompletion.create(messages = messages, **REPLACE_API_PARAMS)
    message = response.choices[0].message.content
    return message

def get_text():
    input_text = st.text_input("You: ","", key="input")
    return input_text

questions = []

def main():
    
    global messages, questions
    if key is not None:
        openai.api_key = key
        st.success('**Key** hiện có thể sử dụng, không cần nhập **Key** thay thế!')
    else:
        st.error('Không có **Key**, vui lòng nhập **Key** thay thế!')
    key_input()
    param_input()
    

    st.markdown(
        '''
<h1 align="center">
    🔥 Hệ thống hỏi đáp
</h1>
        ''',
        unsafe_allow_html = True,
    )
    
    # default_value = 'Các gói sản phẩm SME?'
    # question = st.text_input('Câu hỏi:', default_value)
    # Storing the chat
    if 'generated' not in st.session_state:
        st.session_state['generated'] = []

    if 'past' not in st.session_state:
        st.session_state['past'] = []
    user_input = get_text()

    if user_input:
        questions.append(user_input)
        if len(questions) > 3:
            ques = "\n".join(questions[-3:])
        else:
            ques = "\n".join(questions)
        sum_ques = sumary_question(ques)
        info = construct_prompt(sum_ques)
        # info = construct_prompt(user_input)
        _, index, document = info
        messages.append({"role": "system", "content": f"MISA:\n{document}"})
        messages.append({"role": "user", "content": user_input})
        tokens = count_tokens(str(messages))
        while tokens > 3000:
        # if tokens > 3000:
            del messages[1]
            tokens = count_tokens(str(messages))
        REPLACE_API_PARAMS['max_tokens'] = 3900 - tokens
        output = generate_response(messages)
        messages.append({"role": "assistant", "content": output})
        # store the output 
        st.session_state.past.append(user_input)
        st.session_state.generated.append(output)


        if st.session_state['generated']:
            for i in range(len(st.session_state['generated'])):
                message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')
                message(st.session_state["generated"][i], key=str(i))
                
            
            


    
if __name__ == '__main__':
    main()

