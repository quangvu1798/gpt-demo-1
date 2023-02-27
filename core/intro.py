import streamlit as st

def main():
    st.markdown(
        '''
<h1 align="center">
    Question-Answering Demo site 👋
</h1>
        ''',
        unsafe_allow_html = True,
    )
    with st.expander('Giới thiệu', True):
        st.markdown(
            '''
Demo sử dụng phương pháp **Embeddings** để tìm bài viết liên quan nhất đến câu hỏi tạo thành ngữ cảnh sau đó sử dụng API của **InstructGPT** để tạo câu trả lời.
![InstructGPT](https://lh3.googleusercontent.com/7pDo9u-QNevF0FY-4NzgEk_IgTJipLwVItlrpAnEVzIaEpgiA7F-YOnglbgSuA20zUxnXdVAwXTss0VRilHnSCmc2OMsC7cnhYmRxNyOsrBmeLU057jiiSTcDlAgJoKqmD8KJ5cNZNsqSrI9Tyfr35UeApoZ8z687LviNJsSBHkAUqkpaP5XrgMKL43YnQ)
Hiện tại demo đang trong quá trình hoàn thiện các bài ngữ cảnh, hiện đã hỗ trợ cho một số sản phẩm sau:
1. MISA eShop
2. MISA eSign
3. MISA Lending
4. MISA AMIS Kế toán
5. MISA mTax
6. MISA AMIS Tuyển dụng
7. MISA BankHub
8. MISA SME
9. MISA AMIS aiMarketing
10. MISA AMIS Khuyến mại
11. MISA ASP
12. MISA AMIS CRM
13. MISA AMIS Thông tin nhân sự
14. ...
            '''
        )
    
if __name__ == '__main__':
    main()

