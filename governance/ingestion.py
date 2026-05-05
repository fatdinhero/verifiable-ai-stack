"""
governance/ingestion.py
Multi-Modal Ingestion Layer — verarbeitet URLs, Bilder, PDFs und Text
als strukturierte Signale fuer den COGNITUM Autonomous Loop.
"""
import io
import json
import logging
import re
import urllib.request
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)

OLLAMA_BASE = "http://localhost:11434"
_YT_DOMAINS = {"youtube.com", "youtu.be", "tiktok.com", "instagram.com", "reel"}
_URL_RE = re.compile(r'https?://\S+')


def _is_video_url(url: str) -> bool:
    lower = url.lower()
    return any(d in lower for d in _YT_DOMAINS)


class IngestionLayer:

    def ingest(self, content: Union[str, bytes], content_type: str) -> dict:
        """
        Verarbeitet eingehenden Content und gibt strukturiertes Signal zurueck.
        content_type: "url", "youtube", "tiktok", "image", "pdf", "text"
        """
        if isinstance(content, bytes):
            if content_type == "pdf":
                return self._process_pdf(content)
            return self._process_image(content)

        if content_type in ("url", "youtube", "tiktok"):
            return self._process_url(content.strip())

        if content_type == "image":
            # base64-dekodierter Pfad oder Text-URL
            return self._process_url(content.strip()) if content.startswith("http") \
                else self._process_text(content)

        # text / fallback
        return self._process_text(content)

    # ── URL ──────────────────────────────────────────────────────────────────

    def _process_url(self, url: str) -> dict:
        if _is_video_url(url):
            return self._process_video_url(url)
        return self._process_web_url(url)

    def _process_video_url(self, url: str) -> dict:
        try:
            import yt_dlp
            ydl_opts = {
                "writesubtitles": True,
                "skip_download": True,
                "quiet": True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "")
                description = info.get("description", "")
                # Transcript bevorzugen, fallback auf description
                text = description[:2000] if description else title
                return {
                    "text": text.strip(),
                    "source_type": "youtube" if "youtube" in url or "youtu.be" in url else "tiktok",
                    "source_url": url,
                    "title": title,
                    "metadata": {
                        "duration": info.get("duration"),
                        "uploader": info.get("uploader", ""),
                        "view_count": info.get("view_count"),
                    },
                }
        except Exception as e:
            logger.warning(f"yt-dlp Fehler fuer {url}: {e}")
            return self._fallback_url(url)

    def _process_web_url(self, url: str) -> dict:
        try:
            import requests
            from bs4 import BeautifulSoup

            headers = {"User-Agent": "Mozilla/5.0 (compatible; COGNITUM/1.0)"}
            resp = requests.get(url, timeout=30, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            title = (soup.title.string or "").strip() if soup.title else ""
            meta_desc = ""
            meta = soup.find("meta", attrs={"name": "description"})
            if meta and meta.get("content"):
                meta_desc = meta["content"].strip()

            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 50]
            full_text = " ".join(paragraphs)

            parts = [x for x in [meta_desc, full_text] if x]
            text = " ".join(parts)[:3000]

            return {
                "text": text or title,
                "source_type": "url",
                "source_url": url,
                "title": title,
                "metadata": {"status_code": resp.status_code},
            }
        except Exception as e:
            logger.warning(f"Web-Extraktion Fehler fuer {url}: {e}")
            return self._fallback_url(url)

    def _fallback_url(self, url: str) -> dict:
        return {
            "text": url,
            "source_type": "url",
            "source_url": url,
            "title": url,
            "metadata": {"fallback": True},
        }

    # ── Bild ─────────────────────────────────────────────────────────────────

    def _process_image(self, image_bytes: bytes) -> dict:
        # 1. Tesseract OCR
        ocr_text = ""
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(io.BytesIO(image_bytes))
            ocr_text = pytesseract.image_to_string(img).strip()
        except Exception as e:
            logger.debug(f"OCR Fehler: {e}")

        if ocr_text:
            return {
                "text": ocr_text[:2000],
                "source_type": "image",
                "source_url": "",
                "title": "Bild (OCR)",
                "metadata": {"method": "tesseract"},
            }

        # 2. LLaVA via Ollama falls verfuegbar
        llava_text = self._llava_describe(image_bytes)
        return {
            "text": llava_text,
            "source_type": "image",
            "source_url": "",
            "title": "Bild",
            "metadata": {"method": "llava" if llava_text != "Bild ohne extrahierbaren Text" else "none"},
        }

    def _llava_describe(self, image_bytes: bytes) -> str:
        try:
            import base64
            b64 = base64.b64encode(image_bytes).decode("utf-8")
            payload = json.dumps({
                "model": "llava",
                "prompt": "Beschreibe den Inhalt dieses Bildes auf Deutsch, besonders Text und technische Informationen.",
                "images": [b64],
                "stream": False,
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{OLLAMA_BASE}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response", "").strip() or "Bild ohne extrahierbaren Text"
        except Exception as e:
            logger.debug(f"LLaVA nicht verfuegbar: {e}")
            return "Bild ohne extrahierbaren Text"

    # ── PDF ──────────────────────────────────────────────────────────────────

    def _process_pdf(self, pdf_bytes: bytes) -> dict:
        try:
            from pdfminer.high_level import extract_text
            text = extract_text(io.BytesIO(pdf_bytes))[:2000].strip()
            if text:
                return {
                    "text": text,
                    "source_type": "pdf",
                    "source_url": "",
                    "title": "PDF-Dokument",
                    "metadata": {"method": "pdfminer"},
                }
        except Exception as e:
            logger.debug(f"pdfminer Fehler: {e}")

        return {
            "text": "PDF ohne extrahierbaren Text",
            "source_type": "pdf",
            "source_url": "",
            "title": "PDF-Dokument",
            "metadata": {"method": "none"},
        }

    # ── Text ─────────────────────────────────────────────────────────────────

    def _process_text(self, text: str) -> dict:
        # URL-Detection: falls Text eine URL enthaelt -> _process_url()
        url_match = _URL_RE.search(text)
        if url_match:
            url = url_match.group(0)
            result = self._process_url(url)
            # Kombination: original-text als zusaetzlicher Kontext
            if result["text"] and result["text"] != url:
                extra = text.replace(url, "").strip()
                if extra:
                    result["text"] = f"{extra}\n{result['text']}"
            return result

        return {
            "text": text[:2000],
            "source_type": "text",
            "source_url": "",
            "title": text[:80],
            "metadata": {},
        }
