import json
import sys

from pypdf import PdfReader


def main(path: str) -> None:
    reader = PdfReader(path)
    if reader.is_encrypted:
        try:
            if reader.decrypt("") == 0:
                raise RuntimeError("Encrypted PDF")
        except Exception as exc:
            raise RuntimeError("Encrypted PDF") from exc
    if len(reader.pages) > 200:
        raise RuntimeError("PDF has more than 200 pages")

    pages = []
    for index, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append({"number": index + 1, "text": text})

    combined = "\n\n".join(page["text"] for page in pages).strip()
    if len(combined) > 1_500_000:
        raise RuntimeError("Extracted text is too large")
    print(json.dumps({"text": combined, "pages": len(pages), "characters": len(combined)}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
