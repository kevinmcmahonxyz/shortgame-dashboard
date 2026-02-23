from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from backend.constants import DISTANCES


def distance_keyboard(include_made_it: bool = False) -> InlineKeyboardMarkup:
    """Build inline keyboard for putt distance selection."""
    buttons = []
    if include_made_it:
        buttons.append([InlineKeyboardButton("0 (Made It!)", callback_data="dist:0")])

    row: list[InlineKeyboardButton] = []
    for dist in DISTANCES:
        row.append(InlineKeyboardButton(dist, callback_data=f"dist:{dist}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    return InlineKeyboardMarkup(buttons)


def gir_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for GIR selection."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("GIR", callback_data="gir:yes"),
            InlineKeyboardButton("Non-GIR", callback_data="gir:no"),
        ]
    ])


def holes_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for 9 or 18 hole selection."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("9 holes", callback_data="holes:9"),
            InlineKeyboardButton("18 holes", callback_data="holes:18"),
        ]
    ])
