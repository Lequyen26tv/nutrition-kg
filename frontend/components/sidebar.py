import streamlit as st


SIDEBAR_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

[data-testid="stSidebar"] {
    background: #f0f7f3;
    border-right: 1px solid #ddeee5;
    color: #1a1f1d;
}

[data-testid="stSidebar"],
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {
    color: #1a1f1d;
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.4rem;
}

.sb-brand {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #ddeee5;
    margin-bottom: 1.1rem;
}

.sb-brand-icon {
    width: 2rem;
    height: 2rem;
    background: linear-gradient(135deg, #1a7a45, #2ea060);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex: 0 0 auto;
    box-shadow: 0 3px 10px rgba(26, 122, 69, 0.25);
}

.sb-title {
    color: #1a1f1d !important;
    font-size: 0.97rem;
    font-weight: 700;
    line-height: 1.2;
}

.sb-subtitle {
    color: #4a5e54 !important;
    font-size: 0.76rem;
    line-height: 1.45;
    margin-top: 0.2rem;
}

.sb-section {
    color: #1a7a45 !important;
    font-size: 0.69rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    margin: 1.1rem 0 0.55rem;
    text-transform: uppercase;
}

.sb-stat {
    border: 1px solid #ddeee5;
    border-radius: 10px;
    background: #ffffff;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 2px 8px rgba(26, 122, 69, 0.06);
}

.sb-stat-label {
    color: #4a5e54 !important;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.sb-stat-value {
    color: #1a7a45 !important;
    font-size: 1.3rem;
    font-weight: 700;
    line-height: 1.1;
    margin-top: 0.2rem;
    font-variant-numeric: tabular-nums;
}

.sb-list {
    border: 1px solid #ddeee5;
    border-radius: 10px;
    background: #ffffff;
    padding: 0.6rem 0.85rem;
    box-shadow: 0 2px 8px rgba(26, 122, 69, 0.06);
}

.sb-item {
    color: #1a1f1d !important;
    font-size: 0.84rem;
    line-height: 1.5;
    padding: 0.3rem 0;
    border-bottom: 1px solid #eef6f1;
    display: flex;
    align-items: center;
    gap: 0.45rem;
}

.sb-item:last-child {
    border-bottom: 0;
}

.sb-note {
    color: #4a5e54 !important;
    font-size: 0.76rem;
    line-height: 1.5;
    border-top: 1px solid #ddeee5;
    margin-top: 1rem;
    padding-top: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
</style>
"""


def render_sidebar(stats=None):
    stats = stats or {"nodes": None, "relationships": None, "status": "Neo4j Aura"}
    st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(
            """
            <div class="sb-brand">
                <div class="sb-brand-icon">🥗</div>
                <div>
                    <div class="sb-title">Nutrition Graph-RAG</div>
                    <div class="sb-subtitle">Hỏi đáp dinh dưỡng từ Neo4j.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sb-section">Phạm vi</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="sb-list">
                <div class="sb-item">🥩 Đái tháo đường</div>
                <div class="sb-item">❤️ Tăng huyết áp</div>
                <div class="sb-item">🍜 Món ăn Việt</div>
                <div class="sb-item">🥗 Khẩu phần &amp; dinh dưỡng</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        nodes_val = f"{stats.get('nodes'):,}" if stats.get('nodes') is not None else "--"
        rels_val = f"{stats.get('relationships'):,}" if stats.get('relationships') is not None else "--"

        st.markdown('<div class="sb-section">Cơ sở dữ liệu</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="sb-stat">
                <div class="sb-stat-label">Nodes (thực thể)</div>
                <div class="sb-stat-value">{nodes_val}</div>
            </div>
            <div class="sb-stat">
                <div class="sb-stat-label">Relationships (liên kết)</div>
                <div class="sb-stat-value">{rels_val}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="sb-note">
                🟢 Trạng thái: {stats.get("status", "Neo4j Aura")}
            </div>
            """,
            unsafe_allow_html=True,
        )
