
import os
import sys
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ==========================================================
# THIẾT LẬP ĐƯỜNG DẪN PROJECT
# ==========================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)

if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

# ==========================================================
# IMPORT DATABASE
# ==========================================================
from app.db.neo4j_connection import neo4j_db
from app.db.auth_store import auth_store

# ==========================================================
# KHỞI TẠO GRAPH-RAG SERVICE
# ==========================================================
rag_service = None
test_mode = True

try:
    from app.services.retrieval import RetrievalService

    rag_service = RetrievalService()
    test_mode = False

    print("✅ [NGR-Engine] Đã nạp RetrievalService thành công.")

except Exception as e:
    print(f"⚠️ [WARNING] Không nạp được RetrievalService:")
    traceback.print_exc()
    print("🤖 Hệ thống chuyển sang Backend Test Mode.")

# ==========================================================
# REQUEST MODEL
# ==========================================================
class QuestionRequest(BaseModel):
    question: str


class AuthRequest(BaseModel):
    username: str
    password: str
    full_name: str | None = None


def public_user(user):
    return {
        "id": user["id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "created_at": user["created_at"],
    }


def extract_token(authorization: str | None):
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def get_current_user(authorization: str | None):
    token = extract_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Vui long dang nhap.")

    user = auth_store.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Phien dang nhap khong hop le.")
    return user


def get_optional_user(authorization: str | None):
    token = extract_token(authorization)
    if not token:
        return None
    return auth_store.get_user_by_token(token)


# ==========================================================
# LIFESPAN
# ==========================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Nutrition Graph-RAG Backend đang khởi động...")
    print("🎉 Kết nối Neo4j Aura thành công!")

    yield

    print("🛑 Đang đóng kết nối Neo4j...")
    neo4j_db.close()


# ==========================================================
# TẠO APP
# ==========================================================
app = FastAPI(
    title="Nutrition Graph-RAG Engine",
    lifespan=lifespan
)

# ==========================================================
# CORS
# ==========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# ROUTE ROOT
# ==========================================================
@app.get("/")
def read_root():
    return {
        "status": "Online",
        "mode": "REAL" if not test_mode else "TEST"
    }


@app.post("/auth/register")
def register(payload: AuthRequest):
    username = payload.username.strip()
    password = payload.password

    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Ten dang nhap can it nhat 3 ky tu.")

    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Mat khau can it nhat 6 ky tu.")

    user = auth_store.create_user(username, password, payload.full_name)
    if not user:
        raise HTTPException(status_code=409, detail="Ten dang nhap da ton tai.")

    token = auth_store.create_token(user["id"])
    return {"token": token, "user": public_user(user)}


@app.post("/auth/login")
def login(payload: AuthRequest):
    user = auth_store.authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Ten dang nhap hoac mat khau khong dung.")

    token = auth_store.create_token(user["id"])
    return {"token": token, "user": public_user(user)}


@app.post("/auth/logout")
def logout(authorization: str | None = Header(default=None)):
    token = extract_token(authorization)
    if token:
        auth_store.delete_token(token)
    return {"ok": True}


@app.get("/auth/me")
def me(authorization: str | None = Header(default=None)):
    user = get_current_user(authorization)
    return {"user": public_user(user)}


@app.get("/chat/history")
def chat_history(authorization: str | None = Header(default=None)):
    user = get_current_user(authorization)
    rows = auth_store.list_chat_messages(user["id"])
    return {
        "messages": [
            {
                "id": row["id"],
                "role": row["role"],
                "content": row["content"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    }


@app.delete("/chat/history")
def clear_chat_history(authorization: str | None = Header(default=None)):
    user = get_current_user(authorization)
    auth_store.clear_chat_messages(user["id"])
    return {"ok": True}


# ==========================================================
# ROUTE CHAT
# ==========================================================
@app.post("/chat")
async def chat_endpoint(payload: QuestionRequest, authorization: str | None = Header(default=None)):
    question = payload.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Câu hỏi không được để trống."
        )

    try:
        user = get_optional_user(authorization)
        if user:
            auth_store.add_chat_message(user["id"], "user", question)

        # ==========================
        # REAL MODE
        # ==========================
        if not test_mode and rag_service:

            if hasattr(rag_service, "answer_question"):
                answer = rag_service.answer_question(question)

            elif hasattr(rag_service, "query"):
                answer = rag_service.query(question)

            elif hasattr(rag_service, "_get_expanded_graph_context"):
                context = rag_service._get_expanded_graph_context(question)

                if context:
                    answer = (
                        "🧠 Dữ liệu truy xuất từ đồ thị:\n\n"
                        f"{context}"
                    )
                else:
                    answer = (
                        "🥦 Không tìm thấy thực thể "
                        "trong đồ thị tri thức."
                    )

            else:
                answer = (
                    "⚠ RetrievalService chưa có hàm "
                    "trả lời câu hỏi."
                )

        # ==========================
        # TEST MODE
        # ==========================
        else:
            answer = (
                f"🤖 [Backend Test Mode]\n\n"
                f"Hệ thống đã nhận câu hỏi:\n"
                f"'{question}'"
            )

        if user:
            auth_store.add_chat_message(user["id"], "assistant", answer)

        return {
            "answer": answer
        }

    except Exception as e:
        print("\n💥 LỖI GRAPH-RAG:")
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xử lý Graph-RAG: {str(e)}"
        )

