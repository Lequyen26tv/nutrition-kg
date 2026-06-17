import os
import sys
import os
import sys
from pathlib import Path

import requests
import streamlit as st


st.set_page_config(
    page_title="Tư vấn Dinh dưỡng – Nutrition Graph-RAG",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent
BACKEND_ENV = PROJECT_DIR / "backend" / ".env"

if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

try:
    from components.sidebar import render_sidebar
except ImportError:
    render_sidebar = None


APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --page: #f8fbf9;
    --panel: #ffffff;
    --panel-soft: #eef6f1;
    --text: #1a1f1d;
    --muted: #4a5e54;
    --subtle: #7a8f85;
    --line: #ddeee5;
    --line-strong: #b8d9c7;
    --accent: #1a7a45;
    --accent-dark: #145e35;
    --accent-soft: #e4f5ec;
    --accent-hover: #d0eddc;
    --accent-glow: rgba(26, 122, 69, 0.12);
    --radius-sm: 10px;
    --radius-md: 14px;
    --radius-lg: 20px;
    --shadow-card: 0 2px 12px rgba(26, 122, 69, 0.08), 0 1px 3px rgba(0,0,0,0.05);
    --shadow-input: 0 4px 20px rgba(26, 122, 69, 0.15), 0 2px 6px rgba(0,0,0,0.06);
}

html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif !important;
}

.stApp {
    background: var(--page);
    color: var(--text);
}

.stApp,
.stApp p,
.stApp div,
.stApp span,
.stApp label,
.stApp li,
.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4,
.stApp h5,
.stApp h6,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p {
    color: var(--text);
}

[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] em {
    color: var(--text);
}

.block-container {
    max-width: 820px;
    padding-top: 1.5rem;
    padding-bottom: 7rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

header[data-testid="stHeader"] {
    background: transparent;
}

/* ── TOP HEADER ── */
.topbar {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: flex-start;
    padding: 0.5rem 0 1.5rem;
    border-bottom: 1px solid var(--line);
    margin-bottom: 1.2rem;
}

.app-brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.4rem;
}

.app-icon {
    width: 2.4rem;
    height: 2.4rem;
    background: linear-gradient(135deg, #1a7a45, #2ea060);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    flex: 0 0 auto;
    box-shadow: 0 4px 12px rgba(26, 122, 69, 0.3);
}

.app-title {
    color: var(--text) !important;
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    line-height: 1.2;
    margin: 0;
}

.app-subtitle {
    color: var(--muted) !important;
    font-size: 0.875rem;
    line-height: 1.6;
    max-width: 620px;
    margin-top: 0.3rem;
}

.status-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    border: 1px solid var(--line-strong);
    border-radius: 999px;
    color: var(--accent-dark) !important;
    background: var(--accent-soft);
    font-size: 0.76rem;
    font-weight: 600;
    padding: 0.4rem 0.9rem;
    white-space: nowrap;
    margin-top: 0.2rem;
}

.status-chip::before {
    content: '';
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
    flex: 0 0 auto;
}

/* ── STATS ── */
.stats-row {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    margin-bottom: 1.25rem;
}

.stat-card {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: var(--radius-md);
    padding: 1rem 1.1rem;
    box-shadow: var(--shadow-card);
    transition: box-shadow 0.2s;
}

.stat-card:hover {
    box-shadow: 0 4px 20px rgba(26, 122, 69, 0.12);
}

.stat-label {
    color: var(--muted) !important;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}

.stat-value {
    color: var(--accent) !important;
    font-size: 1.9rem;
    font-weight: 700;
    line-height: 1.1;
    margin-top: 0.2rem;
    font-variant-numeric: tabular-nums;
}

.stat-hint {
    color: var(--subtle) !important;
    font-size: 0.76rem;
    margin-top: 0.3rem;
}

/* ── NOTICE ── */
.notice {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    color: var(--muted) !important;
    font-size: 0.82rem;
    line-height: 1.55;
    padding: 0.6rem 0.9rem;
    margin: 0 0 1.2rem;
    background: var(--accent-soft);
    border: 1px solid var(--line);
    border-left: 3px solid var(--accent);
    border-radius: var(--radius-sm);
}

/* ── QUICK PROMPTS ── */
.quick-section {
    margin-bottom: 1.2rem;
}

.section-title {
    color: var(--muted);
    font-size: 0.76rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 0.7rem;
}

.stButton > button {
    min-height: 2.7rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--line-strong);
    background: var(--panel);
    color: var(--text) !important;
    font-weight: 500;
    font-size: 0.85rem;
    line-height: 1.4;
    white-space: normal;
    box-shadow: var(--shadow-card);
    transition: all 0.18s ease;
    text-align: left;
    padding: 0.5rem 0.8rem;
}

.stButton > button:hover {
    border-color: var(--accent);
    background: var(--accent-hover);
    color: var(--accent-dark) !important;
    box-shadow: 0 4px 16px var(--accent-glow);
    transform: translateY(-1px);
}

.stButton > button:active {
    transform: translateY(0);
}

.stButton > button p,
.stButton > button span,
.stButton > button div {
    color: inherit !important;
    font-size: 0.85rem !important;
}

/* ── CHAT ── */
.chat-box {
    padding: 0.1rem 0 0;
}

[data-testid="stChatMessage"] {
    border: 0;
    border-bottom: 1px solid var(--line);
    background: transparent;
    color: var(--text) !important;
    border-radius: 0;
    padding: 1.1rem 0.5rem;
    margin-bottom: 0;
}

[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div {
    color: var(--text) !important;
    font-size: 0.935rem;
    line-height: 1.65;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: var(--panel-soft);
    border-radius: var(--radius-sm);
    margin: 0.4rem 0;
    border: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
}

/* ── CHAT INPUT ── */
[data-testid="stChatInput"] {
    background: transparent;
    padding: 0.75rem 0;
}

[data-testid="stChatInput"] textarea {
    border: 1.5px solid var(--line-strong);
    border-radius: var(--radius-lg);
    color: var(--text) !important;
    background: var(--panel) !important;
    box-shadow: var(--shadow-input);
    font-size: 0.95rem !important;
    font-family: 'Inter', sans-serif !important;
    padding: 0.85rem 1.1rem !important;
    min-height: 56px !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}

[data-testid="stChatInput"] textarea:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-glow), var(--shadow-input);
    outline: none;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: var(--subtle) !important;
    font-style: italic;
}

/* ── USER CARD ── */
.user-card {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    border: 1px solid var(--line-strong);
    background: var(--panel);
    border-radius: var(--radius-sm);
    padding: 0.75rem;
    margin-bottom: 0.75rem;
    box-shadow: var(--shadow-card);
}

.user-icon {
    width: 2.2rem;
    height: 2.2rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #1a7a45, #2ea060);
    color: #ffffff !important;
    font-size: 0.95rem;
    font-weight: 700;
    flex: 0 0 auto;
    box-shadow: 0 2px 8px rgba(26,122,69,0.3);
}

.user-meta {
    min-width: 0;
}

.user-name {
    color: var(--text) !important;
    font-size: 0.9rem;
    font-weight: 600;
    line-height: 1.25;
    overflow-wrap: anywhere;
}

.user-status {
    color: var(--muted) !important;
    font-size: 0.76rem;
    line-height: 1.3;
    margin-top: 0.1rem;
}

/* ── RESPONSIVE ── */
@media (max-width: 780px) {
    .topbar {
        display: block;
    }

    .status-chip {
        display: inline-flex;
        margin-top: 0.75rem;
    }

    .stats-row {
        grid-template-columns: 1fr;
    }

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
}
</style>
"""


def inject_app_css():
    st.markdown(APP_CSS, unsafe_allow_html=True)


def load_backend_env():
    if not BACKEND_ENV.exists():
        return

    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND_ENV)
    except Exception:
        for line in BACKEND_ENV.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line or line.strip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@st.cache_data(ttl=60, show_spinner=False)
def get_neo4j_stats():
    load_backend_env()

    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    if not uri or not user or not password:
        return {"nodes": None, "relationships": None, "status": "Thiếu cấu hình Neo4j"}

    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            nodes = session.run("MATCH (n) RETURN count(n) AS total").single()["total"]
            relationships = session.run("MATCH ()-[r]->() RETURN count(r) AS total").single()["total"]
        driver.close()
        return {"nodes": nodes, "relationships": relationships, "status": "Neo4j Aura"}
    except Exception:
        return {"nodes": None, "relationships": None, "status": "Không kết nối được Neo4j"}


def format_count(value):
    if value is None:
        return "--"
    return f"{value:,}"


def get_api_base_url() -> str:
    configured_base = os.getenv("NUTRITION_API_BASE")
    if configured_base:
        return configured_base.rstrip("/")

    chat_url = os.getenv("NUTRITION_CHAT_API")
    if chat_url and chat_url.rstrip("/").endswith("/chat"):
        return chat_url.rstrip("/")[:-5]

    return "http://127.0.0.1:8000"


def auth_headers():
    token = st.session_state.get("auth_token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def api_post(path: str, payload=None, timeout=30):
    url = f"{get_api_base_url()}{path}"
    return requests.post(url, json=payload or {}, headers=auth_headers(), timeout=timeout)


def api_get(path: str, timeout=30):
    url = f"{get_api_base_url()}{path}"
    return requests.get(url, headers=auth_headers(), timeout=timeout)


def api_delete(path: str, timeout=30):
    url = f"{get_api_base_url()}{path}"
    return requests.delete(url, headers=auth_headers(), timeout=timeout)


def init_auth_state():
    st.session_state.setdefault("auth_token", None)
    st.session_state.setdefault("auth_user", None)


def set_auth(data):
    st.session_state.auth_token = data["token"]
    st.session_state.auth_user = data["user"]
    st.session_state.pop("history_loaded_for", None)
    st.session_state.pop("messages", None)


def render_auth_screen():
    st.markdown(
        """
        <div class="topbar">
            <div>
                <h1 class="app-title">Nutrition Graph-RAG</h1>
                <div class="app-subtitle">
                    Đăng nhập để chatbot lưu lại lịch sử hỏi đáp dinh dưỡng theo tài khoản của bạn.
                </div>
            </div>
            <div class="status-chip">Tài khoản người dùng</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_tab, register_tab = st.tabs(["Đăng nhập", "Đăng ký"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập", key="login_username")
            password = st.text_input("Mật khẩu", type="password", key="login_password")
            submitted = st.form_submit_button("Đăng nhập", use_container_width=True)

        if submitted:
            try:
                response = api_post(
                    "/auth/login",
                    {"username": username, "password": password},
                    timeout=15,
                )
                if response.status_code == 200:
                    set_auth(response.json())
                    st.rerun()
                else:
                    st.error(response.json().get("detail", "Không đăng nhập được."))
            except requests.exceptions.ConnectionError:
                st.error("Không kết nối được backend FastAPI.")
            except Exception as exc:
                st.error(f"Có lỗi khi đăng nhập: {exc}")

    with register_tab:
        with st.form("register_form"):
            full_name = st.text_input("Họ tên", key="register_full_name")
            username = st.text_input("Tên đăng nhập", key="register_username")
            password = st.text_input("Mật khẩu", type="password", key="register_password")
            submitted = st.form_submit_button("Tạo tài khoản", use_container_width=True)

        if submitted:
            try:
                response = api_post(
                    "/auth/register",
                    {
                        "full_name": full_name,
                        "username": username,
                        "password": password,
                    },
                    timeout=15,
                )
                if response.status_code == 200:
                    set_auth(response.json())
                    st.rerun()
                else:
                    st.error(response.json().get("detail", "Không tạo được tài khoản."))
            except requests.exceptions.ConnectionError:
                st.error("Không kết nối được backend FastAPI.")
            except Exception as exc:
                st.error(f"Có lỗi khi đăng ký: {exc}")


def render_user_controls():
    user = st.session_state.get("auth_user") or {}

    with st.sidebar:
        st.markdown('<div class="sb-section">Tài khoản</div>', unsafe_allow_html=True)

        if not user:
            st.markdown(
                """
                <div class="user-card">
                    <div class="user-icon">U</div>
                    <div class="user-meta">
                        <div class="user-name">Khách</div>
                        <div class="user-status">Chat tự do, chưa lưu lịch sử</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption("Bạn có thể chat không cần đăng nhập. Đăng nhập để xem 10 lượt hỏi đáp gần nhất của mình.")
            login_tab, register_tab = st.tabs(["Đăng nhập", "Đăng ký"])

            with login_tab:
                with st.form("sidebar_login_form"):
                    username = st.text_input("Tên đăng nhập", key="sidebar_login_username")
                    password = st.text_input("Mật khẩu", type="password", key="sidebar_login_password")
                    submitted = st.form_submit_button("Đăng nhập", use_container_width=True)

                if submitted:
                    try:
                        response = api_post(
                            "/auth/login",
                            {"username": username, "password": password},
                            timeout=15,
                        )
                        if response.status_code == 200:
                            set_auth(response.json())
                            st.rerun()
                        else:
                            st.error(response.json().get("detail", "Không đăng nhập được."))
                    except requests.exceptions.ConnectionError:
                        st.error("Không kết nối được backend FastAPI.")
                    except Exception as exc:
                        st.error(f"Có lỗi khi đăng nhập: {exc}")

            with register_tab:
                with st.form("sidebar_register_form"):
                    full_name = st.text_input("Họ tên", key="sidebar_register_full_name")
                    username = st.text_input("Tên đăng nhập", key="sidebar_register_username")
                    password = st.text_input("Mật khẩu", type="password", key="sidebar_register_password")
                    submitted = st.form_submit_button("Tạo tài khoản", use_container_width=True)

                if submitted:
                    try:
                        response = api_post(
                            "/auth/register",
                            {
                                "full_name": full_name,
                                "username": username,
                                "password": password,
                            },
                            timeout=15,
                        )
                        if response.status_code == 200:
                            set_auth(response.json())
                            st.rerun()
                        else:
                            st.error(response.json().get("detail", "Không tạo được tài khoản."))
                    except requests.exceptions.ConnectionError:
                        st.error("Không kết nối được backend FastAPI.")
                    except Exception as exc:
                        st.error(f"Có lỗi khi đăng ký: {exc}")
            return

        display_name = user.get("full_name") or user.get("username") or "Người dùng"
        initial = display_name.strip()[0].upper() if display_name.strip() else "U"
        st.markdown(
            f"""
            <div class="user-card">
                <div class="user-icon">{initial}</div>
                <div class="user-meta">
                    <div class="user-name">{display_name}</div>
                    <div class="user-status">Đang hiển thị 10 lượt hỏi đáp gần nhất</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        clear_col, logout_col = st.columns(2)
        with clear_col:
            if st.button("Xóa lịch sử", use_container_width=True):
                try:
                    api_delete("/chat/history", timeout=15)
                    st.session_state.pop("history_loaded_for", None)
                    st.session_state.pop("messages", None)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Không xóa được lịch sử: {exc}")

        with logout_col:
            if st.button("Đăng xuất", use_container_width=True):
                try:
                    api_post("/auth/logout", timeout=15)
                except Exception:
                    pass
                st.session_state.auth_token = None
                st.session_state.auth_user = None
                st.session_state.pop("history_loaded_for", None)
                st.session_state.pop("messages", None)
                st.rerun()


def default_messages():
    return [
        {
            "role": "assistant",
            "content": "Chào bạn. Hãy nhập món ăn, bệnh lý hoặc khẩu phần bạn muốn kiểm tra.",
        }
    ]


def load_chat_history():
    user = st.session_state.get("auth_user")
    if not user:
        return

    user_id = user.get("id")
    if st.session_state.get("history_loaded_for") == user_id:
        return

    try:
        response = api_get("/chat/history", timeout=15)
        if response.status_code == 200:
            messages = response.json().get("messages", [])
            st.session_state.messages = messages or default_messages()
            st.session_state.history_loaded_for = user_id
        elif response.status_code == 401:
            st.session_state.auth_token = None
            st.session_state.auth_user = None
            st.session_state.pop("history_loaded_for", None)
            st.session_state.messages = default_messages()
        else:
            st.session_state.messages = default_messages()
    except Exception:
        st.session_state.messages = default_messages()


def call_backend(question: str) -> str:
    response = api_post("/chat", {"question": question}, timeout=30)

    if response.status_code != 200:
        return f"**Máy chủ phản hồi lỗi {response.status_code}.** Vui lòng kiểm tra backend FastAPI."

    data = response.json()
    return data.get(
        "answer",
        "Mình chưa tìm thấy câu trả lời phù hợp. Bạn thử hỏi rõ hơn về món ăn, bệnh lý hoặc khẩu phần nhé.",
    )


def render_header(stats):
    st.markdown(
        f"""
        <div class="topbar">
            <div>
                <div class="app-brand">
                    <div class="app-icon">🥗</div>
                    <h1 class="app-title">Nutrition Graph-RAG</h1>
                </div>
                <div class="app-subtitle">
                    Chatbot hỏi đáp dinh dưỡng từ đồ thị tri thức Neo4j.
                    Hỏi về món ăn, bệnh lý hoặc khẩu phần để nhận gợi ý phù hợp.
                </div>
            </div>
            <div class="status-chip">{stats["status"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stats(stats):
    st.markdown(
        f"""
        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-label">Nodes</div>
                <div class="stat-value">{format_count(stats["nodes"])}</div>
                <div class="stat-hint">Tổng số thực thể trong Neo4j Aura</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Relationships</div>
                <div class="stat-value">{format_count(stats["relationships"])}</div>
                <div class="stat-hint">Tổng số liên kết trong Neo4j Aura</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_notice():
    st.markdown(
        """
        <div class="notice">
            ⚕️ Nội dung chỉ mang tính tham khảo, không thay thế tư vấn của bác sĩ hoặc chuyên gia dinh dưỡng.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_quick_prompts():
    st.markdown(
        '<div class="section-title">💬 Câu hỏi nhanh</div>',
        unsafe_allow_html=True,
    )

    prompts = [
        ("🍮 Tiểu đường ăn chè Thái được không?", "Bệnh nhân đái tháo đường ăn chè Thái được không?"),
        ("🥑 Cao huyết áp uống sinh tố bơ?", "Người cao huyết áp uống sinh tố bơ có tốt không?"),
        ("🍚 Ăn cơm trắng cần chú ý gì?", "Người bệnh tiểu đường cần lưu ý gì khi ăn cơm trắng?"),
        ("🌅 Gợi ý bữa sáng phù hợp", "Người đái tháo đường và tăng huyết áp nên ăn sáng món Việt nào?"),
    ]

    selected_prompt = None
    row1_cols = st.columns(2)
    row2_cols = st.columns(2)
    all_cols = row1_cols + row2_cols
    for index, (label, value) in enumerate(prompts):
        with all_cols[index]:
            if st.button(label, use_container_width=True, key=f"qp_{index}"):
                selected_prompt = value

    st.markdown("<div style='margin-bottom:0.6rem'></div>", unsafe_allow_html=True)
    return selected_prompt


def init_messages():
    if "messages" not in st.session_state:
        st.session_state.messages = default_messages()


def render_chat_history():
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    st.markdown("</div>", unsafe_allow_html=True)


def handle_prompt(prompt: str):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Đang truy xuất Neo4j Aura và tổng hợp câu trả lời..."):
            try:
                answer = call_backend(prompt)
            except requests.exceptions.ConnectionError:
                answer = "**Không kết nối được backend FastAPI.** Hãy khởi động backend trước."
            except requests.exceptions.Timeout:
                answer = "**Backend phản hồi quá lâu.** Bạn thử hỏi lại sau."
            except Exception as exc:
                answer = f"**Có lỗi khi xử lý câu hỏi:** `{exc}`"

        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})


def main():
    inject_app_css()
    init_auth_state()
    stats = get_neo4j_stats()

    if render_sidebar:
        render_sidebar(stats=stats)
    else:
        st.sidebar.info("Nutrition Graph-RAG")

    render_user_controls()
    if st.session_state.get("auth_token"):
        load_chat_history()
    init_messages()
    render_header(stats)
    render_stats(stats)
    render_notice()
    selected = render_quick_prompts()
    render_chat_history()

    typed_prompt = st.chat_input("Hỏi về món ăn, bệnh lý, khẩu phần... (VD: Tiểu đường ăn cơm trắng được không?)")
    prompt = typed_prompt or selected

    if prompt:
        handle_prompt(prompt)


if __name__ == "__main__":
    main()
