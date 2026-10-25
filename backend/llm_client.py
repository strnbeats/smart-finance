import os
from pathlib import Path

from dotenv import load_dotenv
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
CERT_PATH = PROJECT_ROOT / "certs" / "russian_trusted_root_ca_pem.crt"

load_dotenv(ENV_PATH)


class GigaChatClient:
    def __init__(self):
        credentials = os.getenv("GIGACHAT_CREDENTIALS")
        if not credentials:
            raise RuntimeError(
                "Не задан GIGACHAT_CREDENTIALS в файле .env"
            )

        if not CERT_PATH.is_file():
            raise RuntimeError(
                f"Не найден сертификат: {CERT_PATH}"
            )

        self.model = os.getenv("GIGACHAT_MODEL", "GigaChat-3-Pro")
        self.client = GigaChat(
            credentials=credentials,
            model=self.model,
            ca_bundle_file=str(CERT_PATH),
            verify_ssl_certs=True,
        )

    def ask(self, prompt: str) -> str:
        if not prompt.strip():
            raise ValueError("Запрос не должен быть пустым.")

        response = self.client.chat(
            Chat(
                messages=[
                    Messages(
                        role=MessagesRole.USER,
                        content=prompt,
                    )
                ]
            )
        )

        if not response.choices:
            raise RuntimeError("GigaChat вернул пустой ответ.")

        return response.choices[0].message.content or ""
