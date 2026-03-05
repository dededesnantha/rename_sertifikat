import os
import re
import pdfplumber


# ─── Configuration ───────────────────────────────────────────────────────────
CERTIFICATE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certificate")

# Create the certificates folder if it doesn't exist
if not os.path.exists(CERTIFICATE_FOLDER):
    os.makedirs(CERTIFICATE_FOLDER)
    print(f"Folder '{CERTIFICATE_FOLDER}' created. Please add certificate PDF files and run again.")


def extract_cert_info(pdf_path):
    """
    Extract certificate number and recipient name from a certificate PDF.

    Certificate number : text before 'Setda/DPMD' on the line containing it
    Recipient name     : line immediately after 'Diberikan Kepada :'
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) == 0:
                print(f"  [SKIP] {pdf_path} - No pages found")
                return None, None

            text = pdf.pages[0].extract_text()
            if not text:
                print(f"  [SKIP] {pdf_path} - Could not extract text")
                return None, None

        lines = text.split("\n")

        # --- Extract certificate number ---
        # Find the line containing 'Setda/DPMD' and take text before it
        cert_number = None
        for line in lines:
            if "Setda/DPMD" in line or "Setda/ DPMD" in line:
                parts = re.split(r"Setda\s*/\s*DPMD", line)
                if parts:
                    cert_number = parts[0].strip().rstrip("/").strip()
                break

        # --- Extract recipient name ---
        # The name is on the line immediately after 'Diberikan Kepada :'
        name = None
        for i, line in enumerate(lines):
            if "Diberikan Kepada" in line:
                if i + 1 < len(lines):
                    name = lines[i + 1].strip()
                break

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
