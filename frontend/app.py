import os
import sys
from pathlib import Path

import requests
import streamlit as st


st.set_page_config(
    page_title="Nutrition Graph-RAG",
    page_icon="N",
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
:root {
    --page: #f3faf5;
    --panel: #ffffff;
    --panel-soft: #f7fcf8;
    --text: #171717;
    --muted: #53665b;
    --subtle: #76877d;
    --line: #d7eadc;
    --line-strong: #b8d8c2;
    --accent: #16733f;
    --accent-soft: #e6f5eb;
    --accent-hover: #d8efdf;
}

html, body, [class*="css"] {
    font-family: "Segoe UI", Arial, sans-serif;
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
    max-width: 1100px;
    padding-top: 1.25rem;
    padding-bottom: 6.5rem;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.topbar {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: flex-start;
    padding: 1rem 0 0.75rem;
    border-bottom: 1px solid var(--line);
    margin-bottom: 1rem;
}

.app-title {
    color: #0f3d25 !important;
    font-size: 1.7rem;
    font-weight: 750;
    letter-spacing: 0;
    line-height: 1.15;
    margin: 0;
}

.app-subtitle {
    color: var(--muted) !important;
    font-size: 0.95rem;
    line-height: 1.55;
    max-width: 720px;
    margin-top: 0.45rem;
}

.status-chip {
    border: 1px solid var(--line-strong);
    border-radius: 6px;
    color: #0f3d25 !important;
    background: var(--accent-soft);
    font-size: 0.78rem;
    font-weight: 650;
    padding: 0.45rem 0.65rem;
    white-space: nowrap;
}

.stats-row {
    display: grid;
    grid-template-columns: repeat(2, minmax(180px, 1fr));
    gap: 0.75rem;
    margin-bottom: 1rem;
}

.stat-card,
.quick-box,
.notice,
.chat-box {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 8px;
}

.stat-card {
    padding: 0.9rem 1rem;
    box-shadow: 0 6px 20px rgba(22, 115, 63, 0.05);
}

.stat-label {
    color: var(--muted) !important;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

.stat-value {
    color: var(--accent) !important;
    font-size: 1.85rem;
    font-weight: 760;
    line-height: 1.1;
    margin-top: 0.25rem;
}

.stat-hint {
    color: var(--subtle) !important;
    font-size: 0.78rem;
    margin-top: 0.35rem;
}

.notice {
    color: #244534 !important;
    font-size: 0.9rem;
    line-height: 1.55;
    padding: 0.75rem 0.9rem;
    margin-bottom: 1rem;
    background: #f8fdf9;
    border-left: 4px solid var(--accent);
}

.quick-box {
    padding: 0.8rem 0.9rem 0.95rem;
    margin-bottom: 1rem;
}

.section-title {
    color: var(--text);
    font-size: 0.96rem;
    font-weight: 750;
    margin-bottom: 0.65rem;
}

.stButton > button {
    min-height: 2.75rem;
    border-radius: 6px;
    border: 1px solid var(--line-strong);
    background: #fbfefc;
    color: #123d27 !important;
    font-weight: 650;
    line-height: 1.35;
    white-space: normal;
    box-shadow: none;
}

.stButton > button:hover {
    border-color: var(--accent);
    background: var(--accent-hover);
    color: #0f3d25 !important;
}

.stButton > button p,
.stButton > button span,
.stButton > button div {
    color: #123d27 !important;
}

.chat-box {
    padding: 0.35rem 0.7rem 0.1rem;
}

[data-testid="stChatMessage"] {
    border: 1px solid var(--line);
    background: var(--panel);
    color: var(--text) !important;
    border-radius: 8px;
    padding: 0.75rem 0.85rem;
    margin-bottom: 0.75rem;
}

[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div {
    color: var(--text) !important;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: #eef8f1;
    border-color: #c9e6d1;
}

[data-testid="stChatInput"] {
    background: rgba(243, 250, 245, 0.96);
}

[data-testid="stChatInput"] textarea {
    border: 1px solid var(--line-strong);
    border-radius: 8px;
    color: var(--text) !important;
    background: #ffffff !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #777777 !important;
}

@media (max-width: 780px) {
    .topbar {
        display: block;
    }

    .status-chip {
        display: inline-block;
        margin-top: 0.75rem;
    }

    .stats-row {
        grid-template-columns: 1fr;
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
        return {"nodes": None, "relationships": None, "status": "Thiáº¿u cáº¥u hÃ¬nh Neo4j"}

    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            nodes = session.run("MATCH (n) RETURN count(n) AS total").single()["total"]
            relationships = session.run("MATCH ()-[r]->() RETURN count(r) AS total").single()["total"]
        driver.close()
        return {"nodes": nodes, "relationships": relationships, "status": "Neo4j Aura"}
    except Exception:
        return {"nodes": None, "relationships": None, "status": "KhÃ´ng káº¿t ná»‘i Ä‘Æ°á»£c Neo4j"}


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
                    ÄÄƒng nháº­p Ä‘á»ƒ chatbot lÆ°u láº¡i lá»‹ch sá»­ há»i Ä‘Ã¡p dinh dÆ°á»¡ng theo tÃ i khoáº£n cá»§a báº¡n.
                </div>
            </div>
            <div class="status-chip">TÃ i khoáº£n ngÆ°á»i dÃ¹ng</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_tab, register_tab = st.tabs(["ÄÄƒng nháº­p", "ÄÄƒng kÃ½"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("TÃªn Ä‘Äƒng nháº­p", key="login_username")
            password = st.text_input("Máº­t kháº©u", type="password", key="login_password")
            submitted = st.form_submit_button("ÄÄƒng nháº­p", use_container_width=True)

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
                    st.error(response.json().get("detail", "KhÃ´ng Ä‘Äƒng nháº­p Ä‘Æ°á»£c."))
            except requests.exceptions.ConnectionError:
                st.error("KhÃ´ng káº¿t ná»‘i Ä‘Æ°á»£c backend FastAPI.")
            except Exception as exc:
                st.error(f"CÃ³ lá»—i khi Ä‘Äƒng nháº­p: {exc}")

    with register_tab:
        with st.form("register_form"):
            full_name = st.text_input("Há» tÃªn", key="register_full_name")
            username = st.text_input("TÃªn Ä‘Äƒng nháº­p", key="register_username")
            password = st.text_input("Máº­t kháº©u", type="password", key="register_password")
            submitted = st.form_submit_button("Táº¡o tÃ i khoáº£n", use_container_width=True)

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
                    st.error(response.json().get("detail", "KhÃ´ng táº¡o Ä‘Æ°á»£c tÃ i khoáº£n."))
            except requests.exceptions.ConnectionError:
                st.error("KhÃ´ng káº¿t ná»‘i Ä‘Æ°á»£c backend FastAPI.")
            except Exception as exc:
                st.error(f"CÃ³ lá»—i khi Ä‘Äƒng kÃ½: {exc}")


def render_user_controls():
    user = st.session_state.get("auth_user") or {}
    display_name = user.get("full_name") or user.get("username") or "NgÆ°á»i dÃ¹ng"

    with st.sidebar:
        st.markdown('<div class="sb-section">TÃ i khoáº£n</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="sb-list">
                <div class="sb-item">{display_name}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        clear_col, logout_col = st.columns(2)
        with clear_col:
            if st.button("XÃ³a lá»‹ch sá»­", use_container_width=True):
                try:
                    api_delete("/chat/history", timeout=15)
                    st.session_state.pop("history_loaded_for", None)
                    st.session_state.pop("messages", None)
                    st.rerun()
                except Exception as exc:
                    st.error(f"KhÃ´ng xÃ³a Ä‘Æ°á»£c lá»‹ch sá»­: {exc}")

        with logout_col:
            if st.button("ÄÄƒng xuáº¥t", use_container_width=True):
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
            "content": "ChÃ o báº¡n. HÃ£y nháº­p mÃ³n Äƒn, bá»‡nh lÃ½ hoáº·c kháº©u pháº§n báº¡n muá»‘n kiá»ƒm tra.",
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
        return f"**MÃ¡y chá»§ pháº£n há»“i lá»—i {response.status_code}.** Vui lÃ²ng kiá»ƒm tra backend FastAPI."

    data = response.json()
    return data.get(
        "answer",
        "MÃ¬nh chÆ°a tÃ¬m tháº¥y cÃ¢u tráº£ lá»i phÃ¹ há»£p. Báº¡n thá»­ há»i rÃµ hÆ¡n vá» mÃ³n Äƒn, bá»‡nh lÃ½ hoáº·c kháº©u pháº§n nhÃ©.",
    )


def render_header(stats):
    st.markdown(
        f"""
        <div class="topbar">
            <div>
                <h1 class="app-title">Nutrition Graph-RAG</h1>
                <div class="app-subtitle">
                    Chatbot há»i Ä‘Ã¡p dinh dÆ°á»¡ng dá»±a trÃªn Ä‘á»“ thá»‹ tri thá»©c Neo4j Aura.
                    Nháº­p mÃ³n Äƒn hoáº·c bá»‡nh lÃ½ Ä‘á»ƒ nháº­n gá»£i Ã½ ngáº¯n gá»n, dá»… Ã¡p dá»¥ng.
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
                <div class="stat-hint">Tá»•ng sá»‘ thá»±c thá»ƒ trong Neo4j Aura</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Relationships</div>
                <div class="stat-value">{format_count(stats["relationships"])}</div>
                <div class="stat-hint">Tá»•ng sá»‘ liÃªn káº¿t trong Neo4j Aura</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_notice():
    st.markdown(
        """
        <div class="notice">
            Ná»™i dung chá»‰ mang tÃ­nh tham kháº£o, khÃ´ng thay tháº¿ tÆ° váº¥n cá»§a bÃ¡c sÄ© hoáº·c chuyÃªn gia dinh dÆ°á»¡ng.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_quick_prompts():
    st.markdown(
        """
        <div class="quick-box">
            <div class="section-title">CÃ¢u há»i nhanh</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    prompts = [
        ("Tiá»ƒu Ä‘Æ°á»ng Äƒn chÃ¨ ThÃ¡i Ä‘Æ°á»£c khÃ´ng?", "Bá»‡nh nhÃ¢n Ä‘Ã¡i thÃ¡o Ä‘Æ°á»ng Äƒn chÃ¨ ThÃ¡i Ä‘Æ°á»£c khÃ´ng?"),
        ("Cao huyáº¿t Ã¡p uá»‘ng sinh tá»‘ bÆ¡ Ä‘Æ°á»£c khÃ´ng?", "NgÆ°á»i cao huyáº¿t Ã¡p uá»‘ng sinh tá»‘ bÆ¡ cÃ³ tá»‘t khÃ´ng?"),
        ("Ä‚n cÆ¡m tráº¯ng cáº§n chÃº Ã½ gÃ¬?", "NgÆ°á»i bá»‡nh tiá»ƒu Ä‘Æ°á»ng cáº§n lÆ°u Ã½ gÃ¬ khi Äƒn cÆ¡m tráº¯ng?"),
        ("Gá»£i Ã½ bá»¯a sÃ¡ng phÃ¹ há»£p", "NgÆ°á»i Ä‘Ã¡i thÃ¡o Ä‘Æ°á»ng vÃ  tÄƒng huyáº¿t Ã¡p nÃªn Äƒn sÃ¡ng mÃ³n Viá»‡t nÃ o?"),
    ]

    cols = st.columns(4)
    selected_prompt = None
    for index, (label, value) in enumerate(prompts):
        with cols[index]:
            if st.button(label, use_container_width=True):
                selected_prompt = value

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
        with st.spinner("Äang truy xuáº¥t Neo4j Aura vÃ  tá»•ng há»£p cÃ¢u tráº£ lá»i..."):
            try:
                answer = call_backend(prompt)
            except requests.exceptions.ConnectionError:
                answer = "**KhÃ´ng káº¿t ná»‘i Ä‘Æ°á»£c backend FastAPI.** HÃ£y khá»Ÿi Ä‘á»™ng backend trÆ°á»›c."
            except requests.exceptions.Timeout:
                answer = "**Backend pháº£n há»“i quÃ¡ lÃ¢u.** Báº¡n thá»­ há»i láº¡i sau."
            except Exception as exc:
                answer = f"**CÃ³ lá»—i khi xá»­ lÃ½ cÃ¢u há»i:** `{exc}`"

        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})


def main():
    inject_app_css()
    init_auth_state()

    if not st.session_state.get("auth_token"):
        render_auth_screen()
        st.stop()

    stats = get_neo4j_stats()

    if render_sidebar:
        render_sidebar(stats=stats)
    else:
        st.sidebar.info("Nutrition Graph-RAG")

    render_user_controls()
    load_chat_history()
    init_messages()
    render_header(stats)
    render_stats(stats)
    render_notice()
    quick_prompt = render_quick_prompts()
    render_chat_history()

    typed_prompt = st.chat_input("Nháº­p cÃ¢u há»i vá» mÃ³n Äƒn, bá»‡nh lÃ½ hoáº·c kháº©u pháº§n...")
    prompt = quick_prompt or typed_prompt

    if prompt:
        handle_prompt(prompt)
        if quick_prompt:
            st.rerun()


if __name__ == "__main__":
    main()
