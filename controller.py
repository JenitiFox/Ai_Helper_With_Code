import streamlit as st
from google import genai
from dotenv import load_dotenv
import os
import time


load_dotenv()


# =========================================================
# GEMINI CLIENT
# =========================================================

def init_gemini_client(api_key: str) -> genai.Client:
    key = (
        api_key.strip()
        if api_key and api_key.strip()
        else os.getenv("GEMINI_API_KEY", "")
    )

    if not key:
        raise ValueError(
            "Gemini API Key не знайдено."
        )

    return genai.Client(api_key=key)


# =========================================================
# SESSION STATE
# =========================================================

def init_session_state():

    if "coins" not in st.session_state:
        st.session_state.coins = 10

    if "history" not in st.session_state:
        st.session_state.history = []

    if "current_chat_index" not in st.session_state:
        st.session_state.current_chat_index = None


# =========================================================
# PROMPT
# =========================================================

def build_prompt(
    user_code: str,
    selected_task: str,
    user_question: str = ""
) -> str:

    if selected_task == "Поясни код":

        return (
            "Поясни простими словами, як працює цей код. "
            "Розбивши пояснення на зрозумілі кроки. "
            "Якщо у коді є складні поняття, поясни їх "
            "простими словами.\n\n"
            "Код:\n"
            "```python\n"
            f"{user_code}\n"
            "```"
        )

    elif selected_task == "Знайти помилки / Оптимізувати":

        return (
            "Проаналізуй цей Python код.\n\n"
            "1. Знайди помилки, якщо вони є.\n"
            "2. Поясни, чому вони виникають.\n"
            "3. Запропонуй покращення.\n"
            "4. Покажи виправлену версію коду.\n"
            "5. Якщо код уже правильний, скажи про це.\n\n"
            "Код:\n"
            "```python\n"
            f"{user_code}\n"
            "```"
        )

    else:

        return (
            "Зважай на цей Python код:\n\n"
            "```python\n"
            f"{user_code}\n"
            "```\n\n"
            "Дай відповідь на запитання користувача:\n"
            f"{user_question}"
        )


# =========================================================
# ПЕРЕВІРКА, ЧИ ПОМИЛКА Є ТИМЧАСОВОЮ
# =========================================================

def is_temporary_api_error(error_text: str) -> bool:

    temporary_errors = [
        "503",
        "UNAVAILABLE",
        "429",
        "RESOURCE_EXHAUSTED",
        "temporarily unavailable",
        "high demand",
        "rate limit"
    ]

    error_lower = error_text.lower()

    return any(
        error.lower() in error_lower
        for error in temporary_errors
    )


# =========================================================
# АНАЛІЗ КОДУ
# =========================================================

def process_code_requests(
    api_key: str,
    user_code: str,
    selected_task: str,
    user_question: str = ""
) -> str:

    active_key = (
        api_key.strip()
        if api_key and api_key.strip()
        else os.getenv("GEMINI_API_KEY", "")
    )

    # Перевірка API ключа
    if not active_key:

        return (
            "Будь ласка, вкажіть Gemini API Key "
            "у файлі .env або у бічній панелі."
        )

    # Перевірка коду
    if not user_code.strip():

        return (
            "Будь ласка, вставте код для аналізу."
        )

    # Перевірка монет
    if st.session_state.coins < 3:

        return (
            "У вас недостатньо монет! "
            "Потрібно мінімум 3 монети для запиту."
        )

    # Списуємо монети перед запитом
    st.session_state.coins -= 3

    try:

        client = init_gemini_client(
            active_key
        )

        prompt = build_prompt(
            user_code,
            selected_task,
            user_question
        )

        # Робимо кілька спроб, якщо Gemini
        # тимчасово недоступний
        max_attempts = 3

        last_error = None

        for attempt in range(max_attempts):

            try:

                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt
                )

                result = getattr(
                    response,
                    "text",
                    None
                )

                if not result:
                    raise ValueError(
                        "Gemini повернув порожню відповідь."
                    )

                return result

            except Exception as e:

                last_error = e
                error_text = str(e)

                # Якщо це тимчасова помилка —
                # пробуємо ще раз
                if (
                    is_temporary_api_error(
                        error_text
                    )
                    and attempt < max_attempts - 1
                ):

                    wait_time = 2 ** attempt

                    time.sleep(wait_time)

                    continue

                # Інші помилки або остання спроба
                raise

        raise last_error

    except Exception as e:

        # Повертаємо монети,
        # якщо API не спрацював
        st.session_state.coins += 3

        error_text = str(e)

        if is_temporary_api_error(
            error_text
        ):

            return (
                "Помилка при запиті до API: "
                "Gemini тимчасово недоступний "
                "через високе навантаження. "
                "Ми автоматично зробили кілька "
                "спроб. Будь ласка, спробуйте ще раз "
                "через декілька секунд."
            )

        return (
            "Помилка при запиті до API: "
            f"{error_text}"
        )


# =========================================================
# ГЕНЕРАЦІЯ ТЕСТУ
# =========================================================

def generate_quiz(
    api_key: str,
    explanation_text: str
) -> list:

    try:

        active_key = (
            api_key.strip()
            if api_key and api_key.strip()
            else os.getenv("GEMINI_API_KEY", "")
        )

        if not active_key:
            return []

        if not explanation_text.strip():
            return []

        client = init_gemini_client(
            active_key
        )

        prompt = (
            "На основі наведеного пояснення створи "
            "РІВНО 5 тестових запитань для перевірки "
            "засвоєння матеріалу.\n\n"

            "Для кожного питання має бути рівно "
            "5 варіантів відповіді.\n\n"

            "Використовуй СУВОРО такий формат:\n\n"

            "Питання: [текст питання]\n"
            "Варіанти: [варіант А]|[варіант Б]|"
            "[варіант В]|[варіант Г]|[варіант Д]\n"
            "Правильна: [точний текст правильного "
            "варіанта]\n"
            "---\n\n"

            "Не додавай ніякого додаткового тексту "
            "до або після тестів.\n\n"

            "Пояснення:\n"
            f"{explanation_text}"
        )

        max_attempts = 3
        last_error = None

        for attempt in range(max_attempts):

            try:

                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt
                )

                response_text = getattr(
                    response,
                    "text",
                    None
                )

                if not response_text:
                    raise ValueError(
                        "Gemini повернув порожню відповідь."
                    )

                # =========================================
                # РОЗБІР ВІДПОВІДІ
                # =========================================

                quizzes = []

                blocks = (
                    response_text
                    .strip()
                    .split("---")
                )

                for block in blocks:

                    if not block.strip():
                        continue

                    lines = (
                        block
                        .strip()
                        .splitlines()
                    )

                    question = ""
                    options = []
                    correct = ""

                    for line in lines:

                        line = line.strip()

                        if line.startswith(
                            "Питання:"
                        ):

                            question = (
                                line
                                .split(":", 1)[1]
                                .strip()
                            )

                        elif (
                            line.startswith(
                                "Варіанти:"
                            )
                        ):

                            raw_options = (
                                line
                                .split(":", 1)[1]
                                .strip()
                            )

                            options = [
                                option.strip()
                                for option in
                                raw_options.split("|")
                                if option.strip()
                            ]

                        elif (
                            line.startswith(
                                "Правильна:"
                            )
                        ):

                            correct = (
                                line
                                .split(":", 1)[1]
                                .strip()
                            )

                    # Перевіряємо,
                    # що питання повністю сформоване
                    if (
                        question
                        and len(options) == 5
                        and correct
                        and correct in options
                    ):

                        quizzes.append(
                            {
                                "question": question,
                                "options": options,
                                "correct_answer": correct
                            }
                        )

                # Нам потрібно рівно 5 питань
                if len(quizzes) == 5:

                    return quizzes

                # Якщо Gemini повернув не 5,
                # пробуємо ще раз
                if attempt < max_attempts - 1:

                    time.sleep(
                        2 ** attempt
                    )

                    continue

                return []

            except Exception as e:

                last_error = e

                error_text = str(e)

                if (
                    is_temporary_api_error(
                        error_text
                    )
                    and attempt < max_attempts - 1
                ):

                    time.sleep(
                        2 ** attempt
                    )

                    continue

                raise

        return []

    except Exception:

        return []


# =========================================================
# ЗБЕРЕЖЕННЯ ІСТОРІЇ
# =========================================================

def save_chat_to_history(
    task: str,
    code: str,
    question: str,
    explanation: str,
    quiz_list: list
):

    new_chat_item = {
        "task": task,
        "code": code,
        "question": question,
        "explanation": explanation,
        "quiz_list": quiz_list,
        "reward_claimed": False
    }

    st.session_state.history.append(
        new_chat_item
    )

    st.session_state.current_chat_index = (
        len(st.session_state.history) - 1
    )