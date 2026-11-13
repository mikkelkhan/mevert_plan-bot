
import asyncio
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from langchain_core.messages import HumanMessage, AIMessage

from app.core.config import settings
from workflow import build_workflow


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "Hello! Welcome to Mevert Plan Bot.\n\n"
        "I can help you with your Gmail and Google Calendar.\n"
        "Send me a message to get started."
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "You can ask me things like:\n\n"
        "- Show my unread emails\n"
        "- Search emails from Mikkel\n"
        "- Show today's upcoming events\n"
        "- What meetings do I have tomorrow?"
    )


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user_message = update.message.text

    await update.message.reply_text("Ek minute, main aapka kaam kar raha hoon.")

    try:
        workflow = context.application.bot_data["workflow"]

        # Maintain separate conversation history for each Telegram chat.
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

        # Telegram messages have a 4096-character limit.
        for i in range(0, len(str(final_message)), 4000):
            await update.message.reply_text(
                str(final_message)[i:i + 4000]
            )

    except Exception:
        logger.exception("Telegram message processing failed")
        await update.message.reply_text(
            "Sorry, something went wrong while processing your request."
        )


async def post_init(application: Application):
    application.bot_data["workflow"] = await build_workflow()
    logger.info("Mevert Plan Bot workflow initialized")


def main():
    application = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("Mevert Plan Bot is running on Telegram...")

    application.run_polling()


if __name__ == "__main__":
    main()
