from typing import List, Dict, Tuple
import numpy as np
import pandas as pd
import openai
import pickle
from transformers import GPT2TokenizerFast
import requests 
tokenizer = GPT2TokenizerFast.from_pretrained('gpt2')

def count_tokens(text: str) -> int:
    return len(tokenizer.encode(text))

df = pd.read_csv('data.csv', sep = '$')
df['tokens'] = [count_tokens(c) for c in df['contents'].values]

COMPLETIONS_MODEL = 'gpt-3.5-turbo'
EMBEDDING_MODEL = 'text-embedding-ada-002'

MAX_SECTION_LEN = 4000
SEPARATOR = '\n"""\n'
separator_len = count_tokens(SEPARATOR)

COMPLETIONS_API_PARAMS = {
    'temperature': 0.2,
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


def get_document(question: str, product = None):
    params = {
        "session_id": "",
        "product": "",
        "title": "",
        "document_id": "",
        "content": "",
        "question": question,
        "context": "",
        "is_stream": False
        }
    headers = {
        'api-key': 'AI_team'
    }
    response = requests.post(url, headers = headers, json=params).json()
    index = response['data'][0]['product']+' - ' + response['data'][0]['title']
    # print(response)
    return (index, response['data'][0]['content'])

# def construct_prompt(question: str, context_embeddings: dict = document_embeddings, df: pd.DataFrame = df, max_context = 1) -> str:
#     most_relevant_document_sections = order_document_sections_by_query_similarity(question, context_embeddings)
#     chosen_sections = []
#     chosen_sections_len = 0
#     chosen_sections_indexes = []
    
#     for _, section_index in most_relevant_document_sections:
#         idx = df.index[(df['products'] == section_index[0]) & (df['indexes'] == section_index[1])][0]
#         # Add contexts until we run out of space.        
#         document_section = df.iloc[[idx]]
        
#         chosen_sections_len += document_section.tokens.values[0] + separator_len
#         if chosen_sections_len > MAX_SECTION_LEN or len(chosen_sections) >= 1:
#             break
        
#         chosen_sections.append(SEPARATOR + document_section.contents.values[0] + SEPARATOR)
#         chosen_sections_indexes.append(str(section_index))
    
#     header = '''Hướng dẫn: Trả lời từng bước dựa vào ngữ cảnh bên dưới\nChú ý: Nếu câu trả lời không ở trong ngữ cảnh, chỉ trả lời theo tri thức.\n\nContext:\n'''
    
#     return (header + ''.join(chosen_sections) + '\n\n Question: ' + question + ' (kèm link http và ký tự "\\n" nếu có trong context)\n Answer:', chosen_sections_indexes, chosen_sections)


def construct_prompt(question: str, context_embeddings: dict = document_embeddings, df: pd.DataFrame = df, max_context = 1) -> str:
    most_relevant_document_sections = order_document_sections_by_query_similarity(question, context_embeddings)
    chosen_sections = []
    chosen_sections_len = 0
    chosen_sections_indexes = []
    
    for _, section_index in most_relevant_document_sections:
        idx = df.index[(df['products'] == section_index[0]) & (df['indexes'] == section_index[1])][0]
        # Add contexts until we run out of space.        
        document_section = df.iloc[[idx]]
        
        chosen_sections_len += document_section.tokens.values[0] + separator_len
        if chosen_sections_len > MAX_SECTION_LEN or len(chosen_sections) >= 1:
            break
        
        chosen_sections.append(SEPARATOR + document_section.contents.values[0] + SEPARATOR)
        chosen_sections_indexes.append(str(section_index))
    
    header = '''Hướng dẫn: Trả lời từng bước dựa vào ngữ cảnh bên dưới (kèm link http và ký tự "\\n" nếu có trong context)\nChú ý: Nếu câu trả lời không ở trong ngữ cảnh, chỉ trả lời theo tri thức.\n\nContext:\n'''
    
    return question, chosen_sections_indexes, chosen_sections

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
