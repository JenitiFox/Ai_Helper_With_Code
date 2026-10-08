import streamlit as st
import os
from dotenv import load_dotenv
from controller import (
    init_session_state,
    process_code_requests,
    generate_quiz,
    save_chat_to_history
)

load_dotenv()


def apply_custom_theme():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&family=Fira+Code:wght@400;700&display=swap');

        .stApp {
            background-color: #0d1117;
            color: #00ff66;
            font-family: 'VT323', 'Fira Code', monospace;
            font-size: 18px;
        }

        h1, h2, h3, h4, h5, h6, .stHeader {
            color: #00ff66 !important;
            font-family: 'Press Start 2P', monospace !important;
            text-shadow: 0 0 10px #00ff66;
            letter-spacing: 1px;
        }

        [data-testid="stSidebar"] {
            background-color: #050a05;
            border-right: 2px solid #00ff66;
        }

        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox select {
            background-color: #000000 !important;
            color: #00ff66 !important;
            border: 1px solid #00ff66 !important;
            font-family: 'Fira Code', monospace !important;
            box-shadow: 0 0 5px rgba(0, 255, 102, 0.3);
        }

        .stTextInput input:focus,
        .stTextArea textarea:focus {
            border-color: #00ff66 !important;
            box-shadow: 0 0 12px #00ff66 !important;
        }

        .stButton button {
            background-color: #000000 !important;
            color: #00ff66 !important;
            border: 2px solid #00ff66 !important;
            font-family: 'Press Start 2P', monospace !important;
            font-size: 12px !important;
            padding: 10px 20px !important;
            transition: all 0.2s ease-in-out !important;
            border-radius: 0px !important;
        }

        .stButton button:hover {
            background-color: #00ff66 !important;
            color: #000000 !important;
            box-shadow: 0 0 15px #00ff66 !important;
            cursor: pointer;
        }

        [data-testid="stMetricValue"] {
            color: #00ff66 !important;
            font-family: 'Press Start 2P', monospace !important;
            text-shadow: 0 0 8px #00ff66;
        }

        [data-testid="stMetricLabel"] {
            color: #00cc52 !important;
            font-family: 'VT323', monospace !important;
            font-size: 20px !important;
        }

        code, pre {
            background-color: #020b02 !important;
            color: #00ff66 !important;
            border: 1px solid #004d1a !important;
            font-family: 'Fira Code', monospace !important;
        }

        .stAlert {
            background-color: #001a00 !important;
            color: #00ff66 !important;
            border: 1px solid #00ff66 !important;
        }

        .stRadio label,
        .stCheckbox label {
            color: #00ff66 !important;
            font-family: 'VT323', monospace !important;
            font-size: 20px !important;
        }

        hr {
            border-color: #00ff66 !important;
            box-shadow: 0 0 5px #00ff66;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def main():
    st.set_page_config(
        page_title="AI Code Assistant",
        page_icon="💻",
        layout="wide"
    )

    apply_custom_theme()
    init_session_state()

    # =========================
    # SIDEBAR
    # =========================

    st.sidebar.title("⚙️ Налаштування")

    default_api_key = os.getenv("GEMINI_API_KEY", "")

    api_key_input = st.sidebar.text_input(
        "Gemini API Key",
        type="password",
        value=default_api_key
    )

    st.sidebar.divider()

    st.sidebar.metric(
        "🪙 Монети",
        st.session_state.coins
    )

    # =========================
    # ЗАГОЛОВОК
    # =========================

    st.title("👾 AI Code Assistant & Quiz")

    # =========================
    # ВКЛАДКИ
    # =========================

    tab1, tab2, tab3 = st.tabs(
        [
            "🔍 Аналіз коду",
            "📝 Тест на засвоєння",
            "📜 Історія запитів"
        ]
    )

    # =========================================================
    # ВКЛАДКА 1 — АНАЛІЗ КОДУ
    # =========================================================

    with tab1:
        st.subheader("Аналіз та оптимізація коду")

        user_code = st.text_area(
            "Вставте ваш Python код сюди:",
            height=200,
            key="input_user_code"
        )

        selected_task = st.selectbox(
            "Оберіть дію:",
            [
                "Поясни код",
                "Знайти помилки / Оптимізувати",
                "Задати своє питання"
            ]
        )

        user_question = ""

        if selected_task == "Задати своє питання":
            user_question = st.text_input(
                "Введіть ваше запитання щодо коду:"
            )

        if st.button("🚀 Запустити аналіз"):

            if st.session_state.coins < 3:
                st.error(
                    "У вас недостатньо монет! "
                    "Потрібно мінімум 3 монети для запиту."
                )

            elif not user_code.strip():
                st.warning("Будь ласка, вставте код для аналізу.")

            else:
                with st.spinner("ШІ аналізує ваш код..."):

                    active_key = (
                        api_key_input
                        if api_key_input
                        else os.getenv("GEMINI_API_KEY", "")
                    )

                    explanation = process_code_requests(
                        active_key,
                        user_code,
                        selected_task,
                        user_question
                    )

                # Якщо API повернув помилку
                if explanation.startswith("Помилка при запиті до API:"):
                    st.error(explanation)

                elif explanation.startswith("Будь ласка,"):
                    st.warning(explanation)

                else:
                    save_chat_to_history(
                        selected_task,
                        user_code,
                        user_question,
                        explanation,
                        []
                    )

                    st.success(
                        "Аналіз успішно завершено! "
                        "Списано 3 монети."
                    )

                    st.rerun()

        # =========================
        # РЕЗУЛЬТАТ АНАЛІЗУ
        # =========================

        if (
            st.session_state.current_chat_index is not None
            and st.session_state.history
        ):
            current_item = st.session_state.history[
                st.session_state.current_chat_index
            ]

            st.divider()

            st.subheader("📌 Результат поточного аналізу:")

            st.markdown(
                current_item["explanation"]
            )

    # =========================================================
    # ВКЛАДКА 2 — ТЕСТ
    # =========================================================

    with tab2:
        st.subheader("Перевірка знань")

        if (
            st.session_state.current_chat_index is not None
            and st.session_state.history
        ):
            current_item = st.session_state.history[
                st.session_state.current_chat_index
            ]

            # Якщо тесту ще немає
            if not current_item["quiz_list"]:

                if st.button(
                    "🧩 Згенерувати тест за цим матеріалом"
                ):

                    with st.spinner(
                        "ШІ генерує тест..."
                    ):

                        active_key = (
                            api_key_input
                            if api_key_input
                            else os.getenv(
                                "GEMINI_API_KEY",
                                ""
                            )
                        )

                        quizzes = generate_quiz(
                            active_key,
                            current_item["explanation"]
                        )

                        current_item["quiz_list"] = quizzes

                        if quizzes:
                            st.success(
                                "Тест успішно згенеровано!"
                            )
                            st.rerun()

                        else:
                            st.error(
                                "Не вдалося згенерувати тест. "
                                "Спробуйте ще раз."
                            )

            # =========================
            # ПОКАЗ ТЕСТІВ
            # =========================

            if current_item["quiz_list"]:

                for i, q in enumerate(
                    current_item["quiz_list"]
                ):

                    st.markdown(
                        f"**Питання {i + 1}:** "
                        f"{q['question']}"
                    )

                    user_choice = st.radio(
                        f"Виберіть варіант "
                        f"(Питання {i + 1}):",
                        q["options"],
                        key=(
                            f"q_"
                            f"{st.session_state.current_chat_index}_"
                            f"{i}"
                        )
                    )

                    if st.button(
                        f"Перевірити відповідь #{i + 1}",
                        key=(
                            f"btn_"
                            f"{st.session_state.current_chat_index}_"
                            f"{i}"
                        )
                    ):

                        if (
                            user_choice.strip()
                            == q["correct_answer"].strip()
                        ):

                            st.success(
                                "🎉 Правильно!"
                            )

                            reward_key = (
                                f"reward_claimed_{i}"
                            )

                            if not current_item.get(
                                reward_key,
                                False
                            ):
                                st.session_state.coins += 2

                                current_item[
                                    reward_key
                                ] = True

                                st.info(
                                    "+2 монети за правильну "
                                    "відповідь! 🎉"
                                )

                                st.rerun()

                        else:
                            st.error(
                                "❌ Неправильно. "
                                f"Правильна відповідь: "
                                f"{q['correct_answer']}"
                            )

            else:
                st.info(
                    "Спочатку виконайте аналіз коду "
                    "на першій вкладці, а потім "
                    "натисніть кнопку генерації тестів."
                )

        else:
            st.info(
                "Історія запитів порожня. "
                "Зробіть аналіз коду на першій вкладці."
            )

    # =========================================================
    # ВКЛАДКА 3 — ІСТОРІЯ
    # =========================================================

    with tab3:
        st.subheader("Архів запитів")

        if st.session_state.history:

            for idx, item in enumerate(
                reversed(st.session_state.history)
            ):

                real_idx = (
                    len(st.session_state.history)
                    - 1
                    - idx
                )

                with st.expander(
                    f"Запит #{real_idx + 1}: "
                    f"{item['task']} "
                    f"(Код: {item['code'][:30]}...)"
                ):

                    st.markdown(
                        f"**Завдання:** "
                        f"{item['task']}"
                    )

                    if item["question"]:
                        st.markdown(
                            f"**Запитання:** "
                            f"{item['question']}"
                        )

                    st.markdown("**Код:**")

                    st.code(
                        item["code"],
                        language="python"
                    )

                    st.markdown(
                        "**Пояснення / Результат:**"
                    )

                    st.markdown(
                        item["explanation"]
                    )

                    if st.button(
                        f"📂 Відкрити цей запит",
                        key=f"open_hist_{real_idx}"
                    ):

                        st.session_state.current_chat_index = (
                            real_idx
                        )

                        st.success(
                            "Запит активовано!"
                        )

                        st.rerun()

        else:
            st.info(
                "Поки немає жодного запису "
                "в історії."
            )


if __name__ == "__main__":
    main()