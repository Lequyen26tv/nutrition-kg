import streamlit as st


SIDEBAR_CSS = """
<style>
[data-testid="stSidebar"] {
    background: #f8fdf9;
    border-right: 1px solid #d7eadc;
    color: #171717;
}

[data-testid="stSidebar"],
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {
    color: #171717;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.2rem;
}

.sb-brand {
    padding-bottom: 0.9rem;
    border-bottom: 1px solid #d7eadc;
    margin-bottom: 1rem;
}

.sb-title {
    color: #0f3d25 !important;
    font-size: 1.05rem;
    font-weight: 760;
    line-height: 1.2;
}

.sb-subtitle {
    color: #53665b !important;
    font-size: 0.8rem;
    line-height: 1.45;
    margin-top: 0.35rem;
}

.sb-section {
    color: #16733f !important;
    font-size: 0.72rem;
    font-weight: 760;
    letter-spacing: 0.04em;
    margin: 1rem 0 0.5rem;
    text-transform: uppercase;
}

.sb-stat {
    border: 1px solid #c9e6d1;
    border-radius: 8px;
    padding: 0.8rem;
    margin-bottom: 0.55rem;
    background: #ffffff;
}

.sb-stat-label {
    color: #53665b !important;
    font-size: 0.76rem;
    font-weight: 720;
}

.sb-stat-value {
    color: #16733f !important;
    font-size: 1.35rem;
    font-weight: 780;
    line-height: 1.1;
    margin-top: 0.25rem;
}

.sb-list {
    border: 1px solid #c9e6d1;
    border-radius: 8px;
    padding: 0.75rem 0.85rem;
    background: #ffffff;
}

.sb-item {
    color: #244534 !important;
    font-size: 0.86rem;
    line-height: 1.45;
    padding: 0.35rem 0;
    border-bottom: 1px solid #e2f1e6;
}

.sb-item:last-child {
    border-bottom: 0;
}

.sb-note {
    color: #53665b !important;
    font-size: 0.78rem;
    line-height: 1.5;
    border-top: 1px solid #d7eadc;
    margin-top: 1rem;
    padding-top: 0.8rem;
}
</style>
"""


def _format_count(value):
    if value is None:
        return "--"
    return f"{value:,}"


def render_sidebar(stats=None):
    stats = stats or {"nodes": None, "relationships": None, "status": "Neo4j Aura"}
    st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(
            """
            <div class="sb-brand">
                <div class="sb-title">Nutrition Graph-RAG</div>
                <div class="sb-subtitle">Hỏi đáp dinh dưỡng từ đồ thị tri thức Neo4j Aura.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sb-section">Neo4j Aura</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="sb-stat">
                <div class="sb-stat-label">Nodes</div>
                <div class="sb-stat-value">{_format_count(stats.get("nodes"))}</div>
            </div>
            <div class="sb-stat">
                <div class="sb-stat-label">Relationships</div>
                <div class="sb-stat-value">{_format_count(stats.get("relationships"))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sb-section">Phạm vi</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="sb-list">
                <div class="sb-item">Đái tháo đường</div>
                <div class="sb-item">Tăng huyết áp</div>
                <div class="sb-item">Món ăn Việt</div>
                <div class="sb-item">Khẩu phần và lưu ý dinh dưỡng</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="sb-note">
                Trạng thái: {stats.get("status", "Neo4j Aura")}<br>
                Dữ liệu thống kê được đọc trực tiếp từ graph.
            </div>
            """,
            unsafe_allow_html=True,
        )
