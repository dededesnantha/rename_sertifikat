import os
import re
import PyPDF2


# ─── Configuration ───────────────────────────────────────────────────────────
CERTIFICATE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certificate")


def extract_cert_info(pdf_path):
    """
    Extract certificate number and recipient name from a certificate PDF.

    Certificate number : text before 'Setda/DPMD' on the line containing it
    Recipient name     : extracted from the line before the certificate number,
                         where the name (ALL CAPS) is concatenated at the end
                         of the description text.
    """
    try:
        reader = PyPDF2.PdfReader(pdf_path)
        if len(reader.pages) == 0:
            print(f"  [SKIP] {pdf_path} - No pages found")
            return None, None

        text = reader.pages[0].extract_text()
        if not text:
            print(f"  [SKIP] {pdf_path} - Could not extract text")
            return None, None

        lines = text.split("\n")

        # --- Find the certificate number line index ---
        cert_line_idx = None
        for i, line in enumerate(lines):
            if "Setda/DPMD" in line or "Setda/ DPMD" in line:
                cert_line_idx = i
                break

        if cert_line_idx is None:
            return None, None

        # --- Extract certificate number ---
        # Take everything before 'Setda/DPMD'
        cert_line = lines[cert_line_idx]
        parts = re.split(r"Setda\s*/\s*DPMD", cert_line)
        cert_number = parts[0].strip().rstrip("/").strip() if parts else None

        # --- Extract recipient name ---
        # The name is concatenated at the end of the line BEFORE the cert number.
        # Strategy: combine the text between "Diberikan Kepada :" and the cert line,
        # then extract the trailing ALL-CAPS name from the end.
        name = None

        # Find "Diberikan Kepada :" line
        diberikan_idx = None
        for i, line in enumerate(lines):
            if "Diberikan Kepada" in line:
                diberikan_idx = i
                break

        if diberikan_idx is not None and cert_line_idx > diberikan_idx:
            # Join all text between "Diberikan Kepada :" and the cert number line
            middle_text = " ".join(
                lines[diberikan_idx + 1 : cert_line_idx]
            ).strip()

            # The name is the trailing ALL-CAPS portion at the end of the text.
            # Indonesian names are typically ALL CAPS in certificates.
            # Pattern: find a sequence of uppercase words at the end,
            # possibly preceded by a lowercase letter (concatenated without space).
            match = re.search(r"([A-Z][A-Z\s\.,']+)$", middle_text)
            if match:
                raw_name = match.group(1).strip()
                # Clean: sometimes starts mid-word, remove partial leading word
                # e.g. "BadungNI DESAK NYOMAN" -> "NI DESAK NYOMAN"
                # Check if first char follows a lowercase letter in the original
                start_pos = match.start(1)
                if start_pos > 0 and middle_text[start_pos - 1].islower():
                    # First word might be partial, keep it as it's actually the name start
                    pass
                name = raw_name.strip()

        return cert_number, name

    except Exception as e:
        print(f"  [ERROR] {pdf_path} - {e}")
        return None, None


def sanitize_filename(text):
    """Remove or replace characters that are not allowed in filenames."""
    # Replace slashes with underscores
    text = text.replace("/", "_").replace("\\", "_")
    # Remove other problematic characters
    text = re.sub(r'[<>:"|?*]', "", text)
    # Collapse multiple spaces/underscores
    text = re.sub(r"\s+", " ", text).strip()
    return text


def rename_certificates():
    """Scan certificate folder and rename PDFs based on extracted info."""
    if not os.path.isdir(CERTIFICATE_FOLDER):
        print(f"Error: Folder '{CERTIFICATE_FOLDER}' not found.")
        return

    pdf_files = [f for f in os.listdir(CERTIFICATE_FOLDER) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print("No PDF files found in the certificate folder.")
        return

    print(f"Found {len(pdf_files)} PDF file(s) in '{CERTIFICATE_FOLDER}'\n")
    print("=" * 60)

    renamed_count = 0
    skipped_count = 0

    for filename in pdf_files:
        filepath = os.path.join(CERTIFICATE_FOLDER, filename)
        print(f"\nProcessing: {filename}")

        cert_number, name = extract_cert_info(filepath)

        if not cert_number:
            print(f"  [SKIP] Could not extract certificate number")
            skipped_count += 1
            continue

        if not name:
            print(f"  [SKIP] Could not extract recipient name")
            skipped_count += 1
            continue

        print(f"  Certificate No : {cert_number}")
        print(f"  Recipient Name : {name}")

        # Build new filename: certNumber_recipientName.pdf
        safe_cert = sanitize_filename(cert_number)
        safe_name = sanitize_filename(name)
        new_filename = f"{safe_cert}_{safe_name}.pdf"
        new_filepath = os.path.join(CERTIFICATE_FOLDER, new_filename)

        # Avoid overwriting an existing file
        if os.path.exists(new_filepath) and new_filepath != filepath:
            print(f"  [SKIP] Target file already exists: {new_filename}")
            skipped_count += 1
            continue

        if filepath == new_filepath:
            print(f"  [SKIP] File already has the correct name")
            skipped_count += 1
            continue

        os.rename(filepath, new_filepath)
        print(f"  [OK]   Renamed to: {new_filename}")
        renamed_count += 1

    print("\n" + "=" * 60)
    print(f"Done! Renamed: {renamed_count} | Skipped: {skipped_count}")


if __name__ == "__main__":
    rename_certificates()
