import math
import traceback
from typing import List

from discord import Color, Embed


def error_to_embed(error: Exception = None) -> List[Embed]:
    traceback_text: str = (
        "".join(traceback.format_exception(type(error), error, error.__traceback__))
        if error
        else traceback.format_exc()
    )

    length: int = len(traceback_text)
    chunks: int = math.ceil(length / 1990)

    traceback_texts: List[str] = [
        traceback_text[l * 1990 : (l + 1) * 1990] for l in range(chunks)
    ]
    return [
        Embed(
            title="Traceback",
            description=("```py\n" + text + "\n```"),
            color=Color.red(),
        )
        for text in traceback_texts
    ]
