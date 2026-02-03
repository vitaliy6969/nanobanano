"""AI Image Hub - Streamlit Frontend MVP"""

import os
from datetime import datetime

import requests
import streamlit as st

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
API_TOKEN = os.getenv("API_TOKEN", "")

# Page configuration
st.set_page_config(
    page_title="AI Image Hub",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .prompt-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #e7f3ff;
        border: 1px solid #b6d4fe;
        font-family: monospace;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)


def get_headers():
    """Get authorization headers"""
    return {"X-API-Token": API_TOKEN}


def generate_image(description: str, width: int, height: int, style: str = None):
    """Call API to generate image"""
    payload = {
        "description": description,
        "width": width,
        "height": height,
    }
    if style:
        payload["style"] = style

    try:
        response = requests.post(
            f"{API_BASE_URL}/generate",
            headers=get_headers(),
            json=payload,
            timeout=120,
        )
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500


def edit_image(image_url: str, edit_description: str, strength: float):
    """Call API to edit image"""
    payload = {
        "image_url": image_url,
        "edit_description": edit_description,
        "strength": strength,
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/edit",
            headers=get_headers(),
            json=payload,
            timeout=120,
        )
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500


def get_history(page: int = 1, per_page: int = 10):
    """Get transaction history"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/history",
            headers=get_headers(),
            params={"page": page, "per_page": per_page},
            timeout=30,
        )
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500


def main():
    # Header
    st.markdown('<p class="main-header">🎨 AI Image Hub</p>', unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Налаштування")

        global API_TOKEN, API_BASE_URL
        API_TOKEN = st.text_input(
            "API Token",
            value=API_TOKEN,
            type="password",
            help="Введіть ваш API токен для доступу до сервера"
        )

        API_BASE_URL = st.text_input(
            "API URL",
            value=API_BASE_URL,
            help="URL адреса API сервера"
        )

        st.markdown("---")
        st.header("ℹ️ Про систему")
        st.markdown("""
        **AI Image Hub** - інтелектуальна платформа
        для генерації та редагування зображень.

        - 🤖 ChatGPT для створення промптів
        - 🎨 Nanobanano Pro для генерації
        - 📊 Повне логування операцій
        """)

    # Main tabs
    tab1, tab2, tab3 = st.tabs(["🖼️ Генерація", "✏️ Редагування", "📜 Історія"])

    # Tab 1: Generation
    with tab1:
        st.header("Створення нового зображення")

        col1, col2 = st.columns([2, 1])

        with col1:
            description = st.text_area(
                "Опис зображення",
                placeholder="Опишіть, яке зображення ви хочете створити (можна будь-якою мовою)...",
                height=150,
                help="Введіть опис бажаного зображення. ChatGPT автоматично перетворить його на професійний промпт."
            )

        with col2:
            width = st.selectbox(
                "Ширина",
                options=[512, 768, 1024, 1536, 2048],
                index=2,
            )
            height = st.selectbox(
                "Висота",
                options=[512, 768, 1024, 1536, 2048],
                index=2,
            )
            style = st.selectbox(
                "Стиль (опціонально)",
                options=["", "photorealistic", "artistic", "anime", "digital-art", "oil-painting"],
                index=0,
            )

        if st.button("🎨 Згенерувати", type="primary", use_container_width=True):
            if not description:
                st.error("Будь ласка, введіть опис зображення")
            elif not API_TOKEN:
                st.error("Будь ласка, введіть API токен в налаштуваннях")
            else:
                with st.spinner("Генерація зображення... Це може зайняти до 2 хвилин."):
                    result, status_code = generate_image(
                        description,
                        width,
                        height,
                        style if style else None
                    )

                if status_code == 200 and result.get("success"):
                    st.success("Зображення успішно згенеровано!")

                    # Show generated prompt
                    st.markdown("**Згенерований промпт:**")
                    st.markdown(f'<div class="prompt-box">{result.get("generated_prompt", "")}</div>',
                              unsafe_allow_html=True)

                    # Show image/result below
                    st.markdown("---")
                    st.markdown("### Результат:")
                    image_url = result.get("image_url")
                    if image_url:
                        if image_url.startswith("http"):
                            st.image(image_url, caption="Згенероване зображення", use_container_width=True)
                        else:
                            # If it's text content, show as text
                            st.markdown(f"**Відповідь моделі:**")
                            st.write(image_url)
                    else:
                        st.warning("URL зображення не отримано")

                    # Store in session for potential editing
                    st.session_state["last_image_url"] = image_url
                    st.session_state["last_prompt"] = result.get("generated_prompt")
                else:
                    error_msg = result.get("detail") or result.get("error") or "Невідома помилка"
                    st.error(f"Помилка генерації: {error_msg}")

    # Tab 2: Editing
    with tab2:
        st.header("Редагування зображення")

        # Option to use last generated image
        use_last = False
        if st.session_state.get("last_image_url"):
            use_last = st.checkbox("Використати останнє згенероване зображення")

        if use_last:
            image_url = st.session_state["last_image_url"]
            st.image(image_url, caption="Зображення для редагування", width=300)
        else:
            image_url = st.text_input(
                "URL зображення",
                placeholder="https://example.com/image.jpg",
                help="Введіть URL зображення, яке потрібно відредагувати"
            )

        edit_description = st.text_area(
            "Опис змін",
            placeholder="Опишіть, які зміни потрібно внести в зображення...",
            height=100,
        )

        strength = st.slider(
            "Сила редагування",
            min_value=0.1,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Чим вище значення, тим більше змін буде внесено"
        )

        if st.button("✏️ Редагувати", type="primary", use_container_width=True):
            if not image_url:
                st.error("Будь ласка, введіть URL зображення")
            elif not edit_description:
                st.error("Будь ласка, опишіть бажані зміни")
            elif not API_TOKEN:
                st.error("Будь ласка, введіть API токен в налаштуваннях")
            else:
                with st.spinner("Редагування зображення..."):
                    result, status_code = edit_image(image_url, edit_description, strength)

                if status_code == 200 and result.get("success"):
                    st.success("Зображення успішно відредаговано!")

                    st.markdown("**Промпт для редагування:**")
                    st.markdown(f'<div class="prompt-box">{result.get("generated_prompt", "")}</div>',
                              unsafe_allow_html=True)

                    if result.get("image_url"):
                        st.image(result["image_url"], caption="Відредаговане зображення")
                        st.session_state["last_image_url"] = result.get("image_url")
                else:
                    error_msg = result.get("detail") or result.get("error") or "Невідома помилка"
                    st.error(f"Помилка редагування: {error_msg}")

    # Tab 3: History
    with tab3:
        st.header("Історія запитів")

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 Оновити"):
                pass  # Will trigger re-fetch

        if not API_TOKEN:
            st.warning("Введіть API токен для перегляду історії")
        else:
            result, status_code = get_history(page=1, per_page=20)

            if status_code == 200 and "transactions" in result:
                transactions = result["transactions"]

                if not transactions:
                    st.info("Історія порожня. Згенеруйте перше зображення!")
                else:
                    for tx in transactions:
                        with st.expander(
                            f"#{tx['id']} - {tx['operation_type'].upper()} - {tx['status']} - {tx['created_at'][:19]}"
                        ):
                            st.markdown(f"**Оригінальний запит:** {tx['original_request']}")

                            if tx.get("generated_prompt"):
                                st.markdown("**Згенерований промпт:**")
                                st.code(tx["generated_prompt"], language=None)

                            if tx.get("result_image_url"):
                                st.image(tx["result_image_url"], width=400)

                            if tx.get("error_message"):
                                st.error(f"Помилка: {tx['error_message']}")

                            st.markdown(f"*Створено: {tx['created_at']}*")
            else:
                error_msg = result.get("detail") or result.get("error") or "Не вдалося завантажити історію"
                st.error(error_msg)


if __name__ == "__main__":
    main()
