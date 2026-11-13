
import os
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from langchain_core.messages import HumanMessage

from app.core.config import settings
from workflow import build_workflow


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "Hello! Welcome to Mevert Plan Bot. 😊\n\n"
        "I can help you with your Gmail and Google Calendar.\n"
        "Send me a message to get started."
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "Here are some things you can ask me:\n\n"
        "- Show my unread emails\n"
        "- Search emails from Mikkel\n"
        "- Show today's upcoming events\n"
        "- What meetings do I have tomorrow?"
    )


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message or not update.message.text:
        return

    user_message = update.message.text

    await update.message.reply_text(
        "Ek minute, main aapka kaam kar raha hoon. 😊"
    )

    try:
        workflow = context.application.bot_data["workflow"]

        # Separate conversation history for each Telegram chat.
        history = context.chat_data.setdefault("messages", [])

        history.append(HumanMessage(content=user_message))

        response = await workflow.ainvoke({
            "messages": history,
            "gmail_result": "",
            "calender_result": "",
            "result": "",
            "next_agent": ""
        })

        history[:] = response["messages"]

        final_message = response["messages"][-1].content

        if isinstance(final_message, list):
            final_message = str(final_message)

        if not final_message:
            final_message = "I couldn't generate a response."

        # Telegram message limit is 4096 characters.
        final_message = str(final_message)

        for i in range(0, len(final_message), 4000):
            await update.message.reply_text(
                final_message[i:i + 4000]
            )

    except Exception:
        logger.exception("Telegram message processing failed")

        await update.message.reply_text(
            "Sorry, something went wrong while processing your request."
        )


async def post_init(application: Application):
    logger.info("Initializing Mevert Plan Bot workflow...")

    application.bot_data["workflow"] = await build_workflow()

    logger.info("Mevert Plan Bot workflow initialized successfully.")


def main():

    # Render provides these environment variables.
    external_url = os.environ.get("RENDER_EXTERNAL_URL")
    port = int(os.environ.get("PORT", "10000"))

    if not external_url:
        raise RuntimeError(
            "RENDER_EXTERNAL_URL is missing. "
            "This application must run with a Render Web Service."
        )

    webhook_secret = settings.WEBHOOK_SECRET_TOKEN

    webhook_url = f"{external_url.rstrip('/')}/telegram"

    application = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Register Telegram handlers.
    application.add_handler(
        CommandHandler("start", start_command)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    logger.info("Starting Mevert Plan Bot in webhook mode...")
    logger.info("Webhook URL: %s", webhook_url)
    logger.info("Listening on port: %s", port)

    # Start Telegram webhook server.
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="telegram",
        webhook_url=webhook_url,
        secret_token=webhook_secret,
        drop_pending_updates=False,
    )


if __name__ == "__main__":
    main()
