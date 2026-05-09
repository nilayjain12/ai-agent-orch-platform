"""
Tests for app.messaging.telegram_bot — Telegram bot handlers.
All Telegram and workflow dependencies are mocked.
"""
import os
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.db.database import Base, engine
from app.db.models import Workflow, Execution
from sqlalchemy.orm import sessionmaker

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Seed an active workflow for the tests
    if not db.query(Workflow).filter(Workflow.name == "Customer Support Workflow").first():
        db.add(Workflow(name="Customer Support Workflow", description="T", nodes=[], edges=[], active=True))
        db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def _make_update(text="Hello bot"):
    update = MagicMock()
    update.message.text = text
    update.message.reply_text = AsyncMock()
    update.effective_chat.id = 42
    return update


# ═══════════════════════════════════════════════════════════════
#  /start command
# ═══════════════════════════════════════════════════════════════

async def test_start_command():
    from app.messaging.telegram_bot import start
    update = _make_update()
    await start(update, MagicMock())
    update.message.reply_text.assert_called_once()
    assert "Hello" in update.message.reply_text.call_args[0][0]


# ═══════════════════════════════════════════════════════════════
#  handle_message — success path
# ═══════════════════════════════════════════════════════════════

@patch("app.messaging.telegram_bot.run_workflow_bg")
async def test_handle_message_success(mock_run):
    from app.messaging.telegram_bot import handle_message

    def side_effect(wf_id, exec_id, msg, thread):
        db = TestingSessionLocal()
        exe = db.query(Execution).filter(Execution.id == exec_id).first()
        if exe:
            exe.status = "completed"
            exe.result = {"output": "Agent says hello"}
            db.commit()
        db.close()

    mock_run.side_effect = side_effect
    update = _make_update("Hi there")

    with patch("app.messaging.telegram_bot.SessionLocal", TestingSessionLocal):
        await handle_message(update, MagicMock())

    # First call is "processing…", second is the actual output
    calls = [str(c) for c in update.message.reply_text.call_args_list]
    assert any("Agent says hello" in c for c in calls)


# ═══════════════════════════════════════════════════════════════
#  handle_message — failure path
# ═══════════════════════════════════════════════════════════════

@patch("app.messaging.telegram_bot.run_workflow_bg")
async def test_handle_message_failure(mock_run):
    from app.messaging.telegram_bot import handle_message

    def side_effect(wf_id, exec_id, msg, thread):
        db = TestingSessionLocal()
        exe = db.query(Execution).filter(Execution.id == exec_id).first()
        if exe:
            exe.status = "failed"
            exe.result = {"error": "LLM timeout"}
            db.commit()
        db.close()

    mock_run.side_effect = side_effect
    update = _make_update("Cause error")

    with patch("app.messaging.telegram_bot.SessionLocal", TestingSessionLocal):
        await handle_message(update, MagicMock())

    calls = [str(c) for c in update.message.reply_text.call_args_list]
    assert any("error" in c.lower() for c in calls)


# ═══════════════════════════════════════════════════════════════
#  handle_message — no active workflows
# ═══════════════════════════════════════════════════════════════

async def test_handle_message_no_workflows():
    from app.messaging.telegram_bot import handle_message

    # Create a session with no active workflows
    db = TestingSessionLocal()
    db.query(Workflow).update({Workflow.active: False})
    db.commit()
    db.close()

    update = _make_update("Hello")
    with patch("app.messaging.telegram_bot.SessionLocal", TestingSessionLocal):
        await handle_message(update, MagicMock())

    calls = [str(c) for c in update.message.reply_text.call_args_list]
    assert any("No active workflows" in c for c in calls)

    # Re-activate the workflow for other tests
    db = TestingSessionLocal()
    db.query(Workflow).update({Workflow.active: True})
    db.commit()
    db.close()


# ═══════════════════════════════════════════════════════════════
#  handle_message — exception during processing
# ═══════════════════════════════════════════════════════════════

@patch("app.messaging.telegram_bot.run_workflow_bg", side_effect=Exception("boom"))
async def test_handle_message_exception(mock_run):
    from app.messaging.telegram_bot import handle_message
    update = _make_update("Crash")

    with patch("app.messaging.telegram_bot.SessionLocal", TestingSessionLocal):
        await handle_message(update, MagicMock())

    calls = [str(c) for c in update.message.reply_text.call_args_list]
    assert any("Internal error" in c for c in calls)


# ═══════════════════════════════════════════════════════════════
#  start_telegram_bot — token guard
# ═══════════════════════════════════════════════════════════════

def test_start_bot_no_token():
    from app.messaging.telegram_bot import start_telegram_bot
    old = os.environ.pop("TELEGRAM_BOT_TOKEN", None)
    try:
        start_telegram_bot()  # Should return immediately, not raise
    finally:
        if old:
            os.environ["TELEGRAM_BOT_TOKEN"] = old


def test_start_bot_placeholder_token():
    from app.messaging.telegram_bot import start_telegram_bot
    os.environ["TELEGRAM_BOT_TOKEN"] = "your_telegram_bot_token_here"
    start_telegram_bot()  # Should return immediately
