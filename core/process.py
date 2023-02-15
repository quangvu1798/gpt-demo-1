from typing import List, Dict, Tuple
import numpy as np
import pandas as pd
import openai
import pickle
from transformers import GPT2TokenizerFast

tokenizer = GPT2TokenizerFast.from_pretrained('gpt2')

def count_tokens(text: str) -> int:
    return len(tokenizer.encode(text))

df = pd.read_csv('data.csv', sep = '$', names = ['title', 'heading', 'content'])
df['tokens'] = [count_tokens(c) for c in df['content'].values]

COMPLETIONS_MODEL = 'text-davinci-003'
EMBEDDING_MODEL = 'text-embedding-ada-002'

MAX_SECTION_LEN = 4000
SEPARATOR = '\n"""\n'
separator_len = count_tokens(SEPARATOR)

COMPLETIONS_API_PARAMS = {
    'temperature': 0.0,
    'top_p': 0.0,
    'max_tokens': 1000,
    'model': COMPLETIONS_MODEL,
    'stream': True
}

with open('doc_embeddings.pickle', 'rb') as handle:
    document_embeddings = pickle.load(handle)

def get_embedding(text: str, model: str = EMBEDDING_MODEL) -> List[float]:
    result = openai.Embedding.create(
      model = model,
      input = text
    )
    return result['data'][0]['embedding']

def vector_similarity(x: List[float], y: List[float]) -> float:
    return np.dot(np.array(x), np.array(y)) / (np.linalg.norm(np.array(x)) * np.linalg.norm(np.array(y)))

def order_document_sections_by_query_similarity(query: str, document_embeddings: Dict[Tuple[str, str], np.ndarray]) -> List[Tuple[float, Tuple[str, str]]]:
    query_embedding = get_embedding(query)
    
    document_similarities = sorted([
        (vector_similarity(query_embedding, doc_embedding), doc_index) for doc_index, doc_embedding in document_embeddings.items()
    ], reverse = True)
    
    return document_similarities

def construct_prompt(question: str, context_embeddings: dict = document_embeddings, df: pd.DataFrame = df, max_context = 1) -> str:
    most_relevant_document_sections = order_document_sections_by_query_similarity(question, context_embeddings)
    chosen_sections = []
    chosen_sections_len = 0
    chosen_sections_indexes = []
     
    for _, section_index in most_relevant_document_sections:
        idx = df.index[(df['title'] == section_index[0]) & (df['heading'] == section_index[1])][0]
        # Add contexts until we run out of space.        
        document_section = df.iloc[[idx]]
        
        chosen_sections_len += document_section.tokens.values[0] + separator_len
        if chosen_sections_len > MAX_SECTION_LEN or len(chosen_sections) >= 1:
            break
        
        chosen_sections.append(SEPARATOR + document_section.content.values[0] + SEPARATOR) #  và giao tiếp lại nếu các câu hỏi thuộc các chủ đề hỏi đáp thường ngày
        chosen_sections_indexes.append(str(section_index))
    
    header = '''Hướng dẫn: Trả lời từng bước dựa vào ngữ cảnh bên dưới (lấy cả những link http bên trong ngoặc vuông này [] và ký tự "\\n")\nChú ý: Nếu câu trả lời không ở trong ngữ cảnh, chỉ trả lời theo tri thức.\n\nContext:\n'''
    
    return (header + ''.join(chosen_sections) + '\n\n Question: ' + question + ' (kèm link http)\n Answer:', chosen_sections_indexes, chosen_sections)

def answer_query_with_context(
    query: str,
    df: pd.DataFrame = df,
    document_embeddings: Dict[Tuple[str, str], np.ndarray] = document_embeddings,
    show_prompt: bool = False
) -> str:
    prompt = construct_prompt(
        query,
        document_embeddings,
        df
    )[0]
    if show_prompt:
        print(prompt)

    response = ''
    for resp in openai.Completion.create(prompt = prompt, **COMPLETIONS_API_PARAMS):
        print(resp.choices[0].text, end = '', flush = True)
    
        response += resp.choices[0].text
    return response

if __name__ == '__main__':
    answer_query_with_context('Cách khai báo loại tiền mới trên web?')
