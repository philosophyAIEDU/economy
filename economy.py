import streamlit as st
from openai import OpenAI
import time
import tempfile

# Streamlit 페이지 설정
st.set_page_config(page_title="나만의 경제분석팀", page_icon="🤖")
st.title("나만의 경제분석팀")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "file_id" not in st.session_state:
    st.session_state.file_id = None

# 고정된 Assistant ID
ASSISTANT_ID = "asst_vX3J0soVFiSe4IMCkRGYr7Cu"

# API 키 입력
api_key = st.text_input("OpenAI API 키를 입력하세요:", type="password")

if api_key:
    client = OpenAI(api_key=api_key)

    # Thread 생성 (처음 한 번만 실행)
    if not st.session_state.thread_id:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    # 파일 업로드
    uploaded_file = st.file_uploader("파일을 업로드하세요", type=["txt", "pdf", "csv"])
    if uploaded_file is not None:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        # OpenAI에 파일 업로드
        with open(tmp_file_path, "rb") as file:
            file_obj = client.files.create(file=file, purpose="assistants")
        
        st.session_state.file_id = file_obj.id
        st.success(f"파일이 성공적으로 업로드되었습니다. (File ID: {file_obj.id})")

    # 사용자 입력
    user_input = st.text_input("메시지를 입력하세요:")

    if st.button("전송") and user_input:
        # 메시지 추가
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=user_input
        )

        # 실행
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=ASSISTANT_ID,
            tools=[{"type": "retrieval"}]  # 파일 검색 도구 활성화
        )

        # 응답 대기
        with st.spinner("답변을 생성 중입니다..."):
            while run.status not in ["completed", "failed"]:
                time.sleep(1)
                run = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                )

            if run.status == "failed":
                st.error("답변 생성에 실패했습니다. 다시 시도해 주세요.")
            else:
                # 응답 가져오기
                messages = client.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id
                )

                # 메시지 저장 및 표시
                st.session_state.messages.append({"role": "user", "content": user_input})
                st.session_state.messages.append({"role": "assistant", "content": messages.data[0].content[0].text.value})

    # 대화 내용 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

else:
    st.warning("OpenAI API 키를 입력해주세요.")
