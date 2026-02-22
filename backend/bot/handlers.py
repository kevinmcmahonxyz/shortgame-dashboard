import logging
from datetime import date

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

from backend.config import settings
from backend.bot.keyboards import distance_keyboard, gir_keyboard
from backend.storage.database import Hole, Putt, Round, get_session

logger = logging.getLogger(__name__)

# Conversation states
FIRST_PUTT, GIR_SELECT, NEXT_PUTT = range(3)

# User data keys
ROUND_ID = "round_id"
HOLE_NUM = "hole_num"
HOLE_ID = "hole_id"
PUTT_NUM = "putt_num"
TOTAL_PUTTS = "total_putts"


async def start_round(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start a new round via /round command."""
    user_id = str(update.effective_user.id)

    with get_session() as session:
        round_obj = Round(telegram_user_id=user_id, date=date.today())
        session.add(round_obj)
        session.commit()
        session.refresh(round_obj)
        round_id = round_obj.id

    context.user_data[ROUND_ID] = round_id
    context.user_data[HOLE_NUM] = 1
    context.user_data[TOTAL_PUTTS] = 0

    await update.message.reply_text(
        "Starting round! Hole 1 of 18.\n\nSelect 1st putt distance:",
        reply_markup=distance_keyboard(include_made_it=False),
    )
    return FIRST_PUTT


async def first_putt_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle 1st putt distance selection."""
    query = update.callback_query
    await query.answer()

    distance = query.data.replace("dist:", "")
    hole_num = context.user_data[HOLE_NUM]
    round_id = context.user_data[ROUND_ID]

    with get_session() as session:
        hole = Hole(round_id=round_id, hole_number=hole_num, gir=False)
        session.add(hole)
        session.commit()
        session.refresh(hole)
        hole_id = hole.id

    context.user_data[HOLE_ID] = hole_id
    context.user_data[PUTT_NUM] = 1
    context.user_data["first_putt_distance"] = distance

    # Record the 1st putt
    with get_session() as session:
        putt = Putt(hole_id=hole_id, putt_number=1, distance=distance)
        session.add(putt)
        session.commit()

    if distance == "Gimmie":
        # Gimmie = 1 putt, made it, ask GIR
        context.user_data[TOTAL_PUTTS] += 1
        with get_session() as session:
            hole = session.get(Hole, hole_id)
            hole.putts_taken = 1
            session.add(hole)
            session.commit()
        await query.edit_message_text(
            f"Hole {hole_num}: Gimmie (1 putt)\n\nGreen in regulation?",
            reply_markup=gir_keyboard(),
        )
        return GIR_SELECT

    # Ask for GIR
    await query.edit_message_text(
        f"Hole {hole_num}: 1st putt from {distance}\n\nGreen in regulation?",
        reply_markup=gir_keyboard(),
    )
    return GIR_SELECT


async def gir_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle GIR selection."""
    query = update.callback_query
    await query.answer()

    gir = query.data == "gir:yes"
    hole_id = context.user_data[HOLE_ID]
    hole_num = context.user_data[HOLE_NUM]
    first_distance = context.user_data["first_putt_distance"]

    with get_session() as session:
        hole = session.get(Hole, hole_id)
        hole.gir = gir
        session.add(hole)
        session.commit()

    gir_text = "GIR" if gir else "Non-GIR"

    if first_distance == "Gimmie":
        # Already recorded 1 putt, move to next hole
        return await _advance_hole(query, context, gir_text)

    # Ask for 2nd putt
    context.user_data[PUTT_NUM] = 2
    await query.edit_message_text(
        f"Hole {hole_num} ({gir_text}): 1st putt from {first_distance}\n\n"
        "Select 2nd putt distance:",
        reply_markup=distance_keyboard(include_made_it=True),
    )
    return NEXT_PUTT


async def next_putt_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle 2nd+ putt distance selection."""
    query = update.callback_query
    await query.answer()

    distance = query.data.replace("dist:", "")
    hole_id = context.user_data[HOLE_ID]
    hole_num = context.user_data[HOLE_NUM]
    putt_num = context.user_data[PUTT_NUM]

    if distance == "0":
        # "Made It!" means the previous putt went in
        # e.g. at 2nd putt prompt, Made It = 1st putt was made = 1 putt total
        actual_putts = putt_num - 1
        context.user_data[TOTAL_PUTTS] += actual_putts
        with get_session() as session:
            hole = session.get(Hole, hole_id)
            hole.putts_taken = actual_putts
            session.add(hole)
            session.commit()
        return await _advance_hole(query, context)
    else:
        # Record the putt and ask for next
        with get_session() as session:
            putt = Putt(hole_id=hole_id, putt_number=putt_num, distance=distance)
            session.add(putt)
            session.commit()

        context.user_data[PUTT_NUM] = putt_num + 1
        await query.edit_message_text(
            f"Hole {hole_num}: Putt {putt_num} from {distance}\n\n"
            f"Select putt {putt_num + 1} distance:",
            reply_markup=distance_keyboard(include_made_it=True),
        )
        return NEXT_PUTT


async def _advance_hole(query, context, gir_text: str = "") -> int:
    """Move to the next hole or finish the round."""
    hole_num = context.user_data[HOLE_NUM]
    total_putts = context.user_data[TOTAL_PUTTS]

    if hole_num >= 18:
        # Round complete
        await query.edit_message_text(
            f"Round complete! {total_putts} total putts.\n\n"
            f"View your dashboard to see updated stats."
        )
        return ConversationHandler.END

    # Next hole
    context.user_data[HOLE_NUM] = hole_num + 1
    next_hole = hole_num + 1
    await query.edit_message_text(
        f"Hole {hole_num} done. Total putts so far: {total_putts}\n\n"
        f"Hole {next_hole} of 18 - Select 1st putt distance:",
        reply_markup=distance_keyboard(include_made_it=False),
    )
    return FIRST_PUTT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current round."""
    round_id = context.user_data.get(ROUND_ID)
    if round_id:
        with get_session() as session:
            round_obj = session.get(Round, round_id)
            if round_obj:
                # Delete associated holes and putts
                for hole in round_obj.holes:
                    for putt in hole.putts:
                        session.delete(putt)
                    session.delete(hole)
                session.delete(round_obj)
                session.commit()

    context.user_data.clear()
    await update.message.reply_text("Round cancelled.")
    return ConversationHandler.END


def build_bot_app() -> Application:
    """Build and return the telegram bot Application."""
    app = Application.builder().token(settings.telegram_bot_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("round", start_round)],
        states={
            FIRST_PUTT: [
                CallbackQueryHandler(first_putt_selected, pattern=r"^dist:"),
            ],
            GIR_SELECT: [
                CallbackQueryHandler(gir_selected, pattern=r"^gir:"),
            ],
            NEXT_PUTT: [
                CallbackQueryHandler(next_putt_selected, pattern=r"^dist:"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    return app
