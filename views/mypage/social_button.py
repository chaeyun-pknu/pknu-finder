
import html
import streamlit as st


def render_social_login_buttons(
    google_url: str | None = None,
    github_url: str | None = None,
) -> None:
    """Google 및 GitHub OAuth 로그인 버튼을 표시합니다."""

    st.markdown(
        """
        <style>
        .social-login-container {
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
            margin: 16px auto;
        }

        .social-login-button {
            box-sizing: border-box;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            width: 100%;
            max-width: 360px;
            min-height: 50px;
            padding: 12px 18px;
            border: 1px solid #DADCE0;
            border-radius: 10px;
            text-decoration: none !important;
            font-family: Arial, sans-serif;
            font-size: 15px;
            font-weight: 600;
            transition: background-color 0.2s;
        }

        .social-login-button img {
            display: block;
            width: 22px;
            height: 22px;
            object-fit: contain;
        }

        .social-login-button.google {
            color: #202124 !important;
            background: #FFFFFF;
        }

        .social-login-button.google:hover {
            background: #F7F8FA;
            border-color: #AEB4BC;
        }

        .social-login-button.github {
            color: #FFFFFF !important;
            background: #24292F;
            border-color: #24292F;
        }

        .social-login-button.github:hover {
            background: #32383F;
            border-color: #32383F;
        }

        @media (max-width: 480px) {
            .social-login-button {
                max-width: 100%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    buttons = []

    if google_url:
        buttons.append(
            f"""
            <a class="social-login-button google"
               href="{html.escape(google_url, quote=True)}">
                <img
                    src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
                    alt="Google"
                />
                <span>Continue with Google</span>
            </a>
            """
        )

    if github_url:
        buttons.append(
            f"""
            <a class="social-login-button github"
               href="{html.escape(github_url, quote=True)}">
                <img
                    src="https://cdn.simpleicons.org/github/FFFFFF"
                    alt="GitHub"
                />
                <span>Continue with GitHub</span>
            </a>
            """
        )

    if buttons:
        button_html = (
            '<div class="social-login-container">'
            + "".join(buttons)
            + "</div>"
        )

        st.html(button_html)