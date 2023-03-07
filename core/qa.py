import streamlit as st
from .process import construct_prompt, COMPLETIONS_API_PARAMS, count_tokens
import openai
import re
import os

REPLACE_API_PARAMS = COMPLETIONS_API_PARAMS.copy()
key = os.environ.get('OPENAI_KEY')
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


message = [
            {"role": "system", "content": 'Hướng dẫn: Trả lời chi tiết dựa vào tri thức (chỉ đưa ra link http và ký tự "\\n" nếu có trong tri thức của MISA)\nChú ý: Nếu câu trả lời không ở trong tri thức MISA, tự trả lời theo tri thức của mình.'}
        ]
questions = []
def main():
    
    
    global message, questions, key
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
    
    default_value = 'Các gói sản phẩm SME?'
    question = st.text_input('Câu hỏi:', default_value)
    with st.expander('Context', False):
        stindex = st.empty()
        context = st.empty()
        stindex.subheader('')
        context.markdown('')
    if st.button('reset context'):
        message = [
            {"role": "system", "content": 'Hướng dẫn: Trả lời chi tiết dựa vào tri thức (chỉ đưa ra link http và ký tự "\\n" nếu có trong tri thức của MISA)\nChú ý: Nếu câu trả lời không ở trong tri thức MISA, tự trả lời theo tri thức của mình.'}
        ]
        questions = []
    st.write('Trả lời:')
    answer = st.empty()
    answer.markdown('')
    # ques = ""
    # for item in message:
    #     if item["role"] == "user":
    #         ques += f'\n{item["content"]}'
    # ques += f'\n{question}'
    
    
    
    cont = st.checkbox('Trả lời tiếp')
    if st.button('Lấy câu trả lời'):
        questions.append(question)
        if len(questions) > 3:
            ques = "\n".join(questions[-3:])
        else:
            ques = "\n".join(questions)
        sum_ques = sumary_question(ques)
        st.text(f"3 question gần nhất: {str(questions[-3:])}")
        st.text(f"Sumary question: {sum_ques}")
        
        info = construct_prompt(sum_ques)
        _, index, document = info
        st.text(f"Doc for question: {document}")
        stindex.subheader(index[0])
        
        
        message.append({"role": "system", "content": f"MISA:\n{document}"})
        message.append({"role": "user", "content": question})
        if cont:
            # info = construct_prompt(question)
            # prompt, index, _ = info
            # prompt = info[0] + st.session_state.p
            tokens = count_tokens(str(message))
            while tokens > 3000:
            # if tokens > 3000:
                del message[1]
                tokens = count_tokens(str(message))
            response = st.session_state.p
        else:
            response = ''
            tokens = count_tokens(str(message))
            while tokens > 3000:
                del message[1]
                tokens = count_tokens(str(message))
        
        tokens = count_tokens(str(message))
        
        while count_tokens(str(message)) > 3000:
            del message[1]
        REPLACE_API_PARAMS['max_tokens'] = 3500 - tokens
        stindex.subheader(index[0])
        used = []
        
        with st.spinner('Đang sinh câu trả lời...'):
            for resp in openai.ChatCompletion.create(messages = message, **REPLACE_API_PARAMS):
                # print(resp)
                tokens += 1
                response += resp.choices[0].delta.content if resp.choices[0].delta.get("content") else ""
                response = parse_response(response, used)
                st.session_state.p = response
                try:
                    answer.markdown(response, unsafe_allow_html = True)
                except:
                    pass
        del message[-1]
        message.append({"role": "user", "content": question})
        message.append({"role": "assistant", "content": response})
        st.success(f'Đã tạo xong câu trả lời gồm {tokens} tokens tiêu tốn {0.0002 * tokens / 1000}$')

    
if __name__ == '__main__':
    main()

