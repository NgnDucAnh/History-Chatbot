import os
import streamlit as st
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph, Neo4jVector
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_neo4j.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

load_dotenv()

st.set_page_config(
    page_title="Hệ thống học Lịch sử Việt Nam", 
    page_icon="🇻🇳", 
    layout="centered"
)

st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🇻🇳 Phần mềm học Lịch sử Việt Nam")
st.subheader("Hệ thống Hybrid GraphRAG (Neo4j + AI)")


@st.cache_resource
def init_system():
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD")
    )
    
    chat_model = os.getenv("OPENAI_CHAT_MODEL", "gpt-5.4-mini")
    llm = ChatOpenAI(model=chat_model, temperature=0, max_retries=1, timeout=20)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    vector_store = Neo4jVector.from_existing_index(
        embedding=embeddings,
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD"),
        index_name="chunk_vector",
        text_node_property="text",
    )

    CYPHER_GENERATION_TEMPLATE = """
    Bạn là một kỹ sư cơ sở dữ liệu Neo4j chuyên về Lịch sử Việt Nam. 
    Nhiệm vụ của bạn là viết câu lệnh Cypher chuẩn xác để truy vấn đồ thị.

    QUY TẮC SINH CODE BẮT BUỘC:
    1. LUÔN dùng nhãn :Entity cho mọi node.
    2. LUÔN dùng cấu trúc đầy đủ: MATCH (n:Entity)-[r]->(m:Entity) 
       TUYỆT ĐỐI KHÔNG dùng cấu trúc thiếu biến r hoặc m.
    3. TÌM KIẾM MỀM: Dùng toLower() và CONTAINS cho cả n.id và m.id.
       Ví dụ: (toLower(n.id) CONTAINS toLower('tên')) OR (toLower(m.id) CONTAINS toLower('tên'))
    4. ALIAS: Luôn dùng dấu nháy ngược (`) cho tên cột. 
       Ví dụ: RETURN n.id AS `Chủ thể`, type(r) AS `Hành động`, m.id AS `Đối tượng`

    SCHEMA: {schema}
    Câu hỏi: {question}
    Cypher Query:"""

    cypher_prompt = PromptTemplate(
        input_variables=["schema", "question"], 
        template=CYPHER_GENERATION_TEMPLATE
    )
    
    graph_chain = GraphCypherQAChain.from_llm(
        llm=llm, 
        graph=graph, 
        verbose=True, 
        cypher_prompt=cypher_prompt,
        allow_dangerous_requests=True,
        return_direct=True 
    )
    
    return graph_chain, vector_store, llm

try:
    graph_chain, vector_store, final_llm = init_system()
except Exception as e:
    st.error(f" Lỗi kết nối hệ thống: {e}")
    st.stop()


def build_history_context(messages, max_messages=6, max_chars_per_message=1200):
    recent_messages = messages[-max_messages:]
    history_lines = []

    for msg in recent_messages:
        content = msg.get("content", "").replace("\n", " ").strip()
        if not content:
            continue
        if len(content) > max_chars_per_message:
            content = content[:max_chars_per_message] + "..."

        role = "Sinh vien" if msg.get("role") == "user" else "Tro ly"
        history_lines.append(f"{role}: {content}")

    return "\n".join(history_lines)


def rewrite_question_with_history(llm, user_query, previous_messages):
    history_context = build_history_context(previous_messages)
    if not history_context:
        return user_query

    rewrite_prompt = ChatPromptTemplate.from_messages([
        ("system", """You rewrite Vietnamese follow-up questions into standalone questions for a history retrieval system.
Use the conversation history only to resolve missing context, pronouns, and phrases like "chi tiet hon", "trinh bay tiep", or "van de nay".
If the current question is already standalone, return it unchanged.
Return exactly one standalone question. Do not answer the question."""),
        ("user", """Conversation history:
{history}

Current question:
{question}

Standalone question:""")
    ])

    try:
        rewritten_question = (rewrite_prompt | llm).invoke({
            "history": history_context,
            "question": user_query
        }).content.strip()

        return rewritten_question or user_query
    except Exception:
        return user_query


DETAILED_HISTORY_SYSTEM_PROMPT = """
Ban la mot giao vien Lich su Viet Nam. Hay tra loi theo phong cach bai hoc tu luan, day du va mach lac.

NGUYEN TAC NOI DUNG:
1. Chi su dung thong tin co trong Du lieu Do thi va Du lieu Van ban Vector duoc cung cap.
2. Neu du lieu co lien quan nhung chua du mot y nao do, hay ghi ngan gon: "Du lieu truy xuat chua neu ro noi dung nay." Khong duoc tu bia them chi tiet.
3. Neu ca hai nguon du lieu deu trong hoac khong lien quan, tra loi dung cau: "Xin loi, du lieu lich su cua toi chua co thong tin ve van de nay."
4. Khong ket thuc bang cau goi y nhu "Neu ban muon..." hoac moi nguoi dung hoi tiep.

YEU CAU TRINH BAY MAC DINH:
- Mac dinh tra loi chi tiet, khong viet qua ngan.
- Mo dau bang mot cau gioi thieu ngan ve chu de.
- Neu cau hoi yeu cau trinh bay mot chien luoc, su kien, giai doan hoac khai niem lich su, hay uu tien bo cuc:
  1. Khai niem hoac khai quat
  2. Hoan canh ra doi / boi canh lich su
  3. Am muu, muc tieu
  4. Luc luong tham gia
  5. Cach tien hanh / thu doan chu yeu
  6. Dien bien chinh
  7. Ket qua
  8. Y nghia lich su
  9. Tom tat ngan gon
- Moi muc nen co 2-4 cau hoac cac gach dau dong co giai thich ro rang.
- Chi dung muc nao phu hop voi cau hoi va du lieu truy xuat; khong ep du 9 muc neu cau hoi khong can.
- Khong them muc "Nhan xet theo tai lieu" tru khi nguoi dung yeu cau nhan xet.
- Giong van trang trong, de hoc, phu hop voi hoc sinh/sinh vien on thi.
"""


if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Chào Đức Anh! Tôi đã sẵn sàng cùng bạn khám phá lịch sử qua Đồ thị tri thức. Bạn muốn tìm hiểu về sự kiện hay nhân vật nào?"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user_query = st.chat_input("Nhập câu hỏi lịch sử...")

if user_query:
    previous_messages = st.session_state.messages.copy()
    st.chat_message("user").write(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    with st.chat_message("assistant"):
        with st.spinner("Hệ thống Hybrid RAG đang phân tích dữ liệu..."):
            try:
                standalone_question = rewrite_question_with_history(final_llm, user_query, previous_messages)

                vector_docs = vector_store.similarity_search(standalone_question, k=6)
                vector_context = "\n\n".join([f"[Đoạn văn {i+1}]: {doc.page_content}" for i, doc in enumerate(vector_docs)])
                
                try:
                    graph_res = graph_chain.invoke({"query": standalone_question})
                    graph_context = str(graph_res['result'])
                except:
                    graph_context = "Không có dữ liệu đồ thị cụ thể cho câu hỏi này."

                final_prompt = ChatPromptTemplate.from_messages([
                    ("system", DETAILED_HISTORY_SYSTEM_PROMPT),
                    ("user", """Cau hoi cua sinh vien: {question}

--- DU LIEU DO THI ---
{graph_context}

--- DU LIEU VAN BAN VECTOR ---
{vector_context}
""")
                ])

                response_chain = final_prompt | final_llm
                full_response = response_chain.invoke({
                    "question": standalone_question,
                    "graph_context": graph_context,
                    "vector_context": vector_context
                }).content
                
                st.write(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                with st.expander("Nhật ký truy vấn dữ liệu"):
                    tab1, tab2 = st.tabs(["Dữ liệu Đồ thị", "Dữ liệu Vector"])
                    st.caption(f"Cau hoi dung de truy van: {standalone_question}")
                    with tab1:
                        st.code(graph_context, language="json")
                    with tab2:
                        st.write(vector_context)

            except Exception as e:
                st.error("Rất tiếc, hệ thống gặp khó khăn khi kết nối. Hãy thử diễn đạt câu hỏi rõ ràng hơn.")
                st.info(f"Chi tiết kỹ thuật: {e}")
