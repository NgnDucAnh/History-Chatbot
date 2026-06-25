import os

from dotenv import load_dotenv

from langchain_community.graphs import Neo4jGraph

from langchain_openai import ChatOpenAI

from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

load_dotenv()

print("Đang đánh thức Chatbot và kết nối với Đồ thị Neo4j (Phiên bản mới)...")

try:
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD")
    )
except Exception as e:
    print(f"Lỗi kết nối Neo4j: {e}")
    exit()


CYPHER_GENERATION_TEMPLATE = """
Bạn là một chuyên gia Lịch sử Việt Nam. Nhiệm vụ của bạn là viết câu lệnh Cypher chuẩn xác để truy vấn đồ thị.

QUY TẮC CỐT LÕI:
1. LUÔN dùng nhãn :Entity cho mọi node.
2. TÌM KIẾM MỀM (Fuzzy Search): Vì tên gọi có thể lệch hoa thường, hãy dùng hàm toLower() và CONTAINS.
   Ví dụ: Thay vì {{name: 'Mỹ'}}, hãy dùng: toLower(n.id) CONTAINS toLower('Mỹ')
3. TRUY VẤN QUAN HỆ: Nếu người dùng hỏi về "Âm mưu", hãy tìm các quan hệ (relationships) mà tên của nó chứa chữ "ÂM_MƯU".
4. LẤY CẢ TÊN QUAN HỆ: Khi trả về kết quả, hãy lấy cả tên của node nguồn, node đích và LOẠI QUAN HỆ để AI có đủ dữ liệu tóm tắt.
5. SỬ DỤNG DẤU NHÁY NGƯỢC: Luôn dùng dấu ` để bao quanh tên cột (alias).

SCHEMA: {schema}

VÍ DỤ TỐT:
Câu hỏi: "Mỹ có âm mưu gì?"
Cypher: MATCH (n:Entity)-[r]->(m:Entity) WHERE toLower(n.id) CONTAINS 'mỹ' AND type(r) CONTAINS 'ÂM_MƯU' RETURN n.id AS `Chủ thể`, type(r) AS `Hành động`, m.id AS `Đối tượng`

Câu hỏi: {question}
Cypher Query:"""

CYPHER_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], 
    template=CYPHER_GENERATION_TEMPLATE
)

chat_model = os.getenv("OPENAI_CHAT_MODEL", "gpt-5.4-mini")
llm = ChatOpenAI(model=chat_model, temperature=0)

chain = GraphCypherQAChain.from_llm(
    llm=llm, 
    graph=graph, 
    verbose=True, 
    cypher_prompt=CYPHER_PROMPT, 
    allow_dangerous_requests=True 
)

print("\n KẾT NỐI THÀNH CÔNG!")
print("="*60)
print(" PHẦN MỀM HỌC LỊCH SỬ VIỆT NAM - CHATBOT ĐÃ SẴN SÀNG")
print("="*60)


def build_history_context(messages, max_messages=6, max_chars_per_message=1200):
    recent_messages = messages[-max_messages:]
    history_lines = []

    for msg in recent_messages:
        content = msg.get("content", "").replace("\n", " ").strip()
        if not content:
            continue
        if len(content) > max_chars_per_message:
            content = content[:max_chars_per_message] + "..."

        role = "Sinh vien" if msg.get("role") == "user" else "Chatbot"
        history_lines.append(f"{role}: {content}")

    return "\n".join(history_lines)


def rewrite_question_with_history(llm, question, previous_messages):
    history_context = build_history_context(previous_messages)
    if not history_context:
        return question

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
            "question": question
        }).content.strip()

        return rewritten_question or question
    except Exception:
        return question


conversation_history = []

while True:
    question = input("\n Sinh viên: ")
    if question.lower() in ['thoat', 'exit', 'quit']:
        print("Tạm biệt! Chúc bạn làm đồ án điểm cao!")
        break
    
    if not question.strip():
        continue
        
    try:
        print(" Chatbot đang tra cứu đồ thị tri thức...")
        standalone_question = rewrite_question_with_history(llm, question, conversation_history)
        response = chain.invoke({"query": standalone_question})
        answer = response['result']
        print(f"\n Chatbot: {answer}")

        conversation_history.append({"role": "user", "content": question})
        conversation_history.append({"role": "assistant", "content": answer})
    except Exception as e:
        print(f"\n Hệ thống gặp lỗi truy vấn: {e}")
