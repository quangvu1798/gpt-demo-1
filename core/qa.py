import streamlit as st
from .process import construct_prompt, COMPLETIONS_API_PARAMS, count_tokens
import openai
import re
import os

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

def parse_response(response):
    response = response.replace(r'\n', '\n\n')
    links = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', response)
    if len(links) > 0:
        for link in links:
            link = link.replace('[', '').replace(']', '')
            if link[-4:] in ['.jpg', '.png', 'jpeg', '.gif']:
                response = response.replace('[' + link + ']', f'![image]({link})')
            if link.startswith('https://vimeo.com'):
                id = link[link.rindex('/') + 1:]
                response = response.replace('[' + link + ']', f'<iframe src="https://player.vimeo.com/video/{id}?autoplay=1&loop=1&title=0&byline=0&portrait=0" width="640" height="360" frameborder="0" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe>')
            if link.startswith('https://www.youtube.com/embed/'):
                response = response.replace('[' + link + ']', f'<iframe src="<iframe width="560" height="315" src="{link}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>')
    return response

def main():
    key = os.environ.get('OPENAI_KEY')
    if key is not None:
        openai.api_key = key
    else:
        st.error('Không có **Key**, vui lòng nhập **Key** thay thế!')
    key_input()
    param_input()
    st.markdown(
        '''
<h1 align="center">
    ✨ Question-Answering with Embedding
</h1>
        ''',
        unsafe_allow_html = True,
    )
    
    default_value = 'Cách khai báo loại tiền mới trên web?'
    question = st.text_input('Câu hỏi:', default_value)
    with st.expander('Context', False):
        context = st.empty()
        context.markdown('')
    st.write('Trả lời:')
    answer = st.empty()
    answer.markdown('')
    
    prompt = construct_prompt(question)[0]
    context.markdown(prompt)
    cont = st.checkbox('Trả lời tiếp')
    if st.button('Lấy câu trả lời'):
        if cont:
            prompt = construct_prompt(question)[0] + st.session_state.p
            tokens = count_tokens(prompt)
            response = st.session_state.p
        else:
            response = ''
            tokens = count_tokens(prompt)
        REPLACE_API_PARAMS['max_tokens'] = 4096 - tokens
        with st.spinner('Đang sinh câu trả lời...'):
            for resp in openai.Completion.create(prompt = prompt, **REPLACE_API_PARAMS):
                tokens += 1
                response += resp.choices[0].text
                response = parse_response(response)
                st.session_state.p = response
                try:
                    answer.markdown(response, unsafe_allow_html = True)
                except:
                    pass
        st.success(f'Đã tạo xong câu trả lời gồm {tokens} tokens tiêu tốn {0.02 * tokens / 1000}$')

    
if __name__ == '__main__':
    main()

