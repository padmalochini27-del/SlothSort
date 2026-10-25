
import hashlib
import shutil
from pathlib import Path
from collections import defaultdict

import requests
import streamlit as st


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="SlothSort",
    page_icon="🦥",
    layout="wide",
)

APP_TITLE = "SlothSort"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:1.5b"

CATEGORIES = {
    "Documents": {
        ".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt",
        ".ppt", ".pptx", ".xls", ".xlsx", ".csv",
    },
    "Images": {
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp",
        ".svg", ".heic", ".tiff",
    },
    "Videos": {
        ".mp4", ".mkv", ".mov", ".avi", ".webm",
    },
    "Audio": {
        ".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a",
    },
    "Code": {
        ".py", ".js", ".ts", ".html", ".css", ".java",
        ".c", ".cpp", ".h", ".cs", ".json", ".xml",
        ".yml", ".yaml", ".sql", ".ipynb", ".md",
    },
    "Archives": {
        ".zip", ".rar", ".7z", ".tar", ".gz",
    },
    "Installers": {
        ".exe", ".msi", ".msix", ".apk",
    },
}


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def categorize(path: Path) -> str:
    """Categorize a file based on its extension."""
    suffix = path.suffix.lower()

    for category, extensions in CATEGORIES.items():
        if suffix in extensions:
            return category

    return "Other"


def sha256_file(path: Path) -> str:
    """Calculate a file's SHA-256 hash in chunks."""
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def unique_destination(path: Path) -> Path:
    """Avoid overwriting an existing file."""
    if not path.exists():
        return path

    counter = 1

    while True:
        candidate = path.with_name(
            f"{path.stem}_{counter}{path.suffix}"
        )

        if not candidate.exists():
            return candidate

        counter += 1


def suggest_filename_with_ai(
    filename: str,
    category: str,
) -> str:
    """
    Ask the locally running Ollama model for a filename suggestion.
    The model receives the filename and category, not file contents.
    """

    original = Path(filename)
    extension = original.suffix

    prompt = f"""
You are a careful file organization assistant.

Suggest one short, descriptive filename based only on the
existing filename and category. Do not pretend you know the
file contents.

Current filename: {filename}
Category: {category}
Original extension: {extension}

Rules:
- Return only one filename.
- Preserve the original extension exactly.
- Do not return a folder path.
- Use simple, readable words.
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=90,
    )

    response.raise_for_status()

    suggestion = response.json().get(
        "response", ""
    ).strip()

    if not suggestion:
        return filename

    suggestion = (
        suggestion
        .strip(" \"'`")
        .splitlines()[0]
        .strip()
    )

    # Never trust model-generated paths or unsafe names.
    if (
        not suggestion
        or suggestion in {".", ".."}
        or Path(suggestion).name != suggestion
        or "/" in suggestion
        or "\\" in suggestion
        or any(ord(char) < 32 for char in suggestion)
        or any(char in '<>:"|?*' for char in suggestion)
        or suggestion.endswith((" ", "."))
        or Path(suggestion).suffix.lower()
        != extension.lower()
    ):
        return filename

    return suggestion


def scan_folder(folder: Path) -> list:
    """Scan files directly inside the chosen folder."""
    result = []

    try:
        entries = list(folder.iterdir())
    except OSError:
        return result

    for path in sorted(
        entries,
        key=lambda item: item.name.lower(),
    ):
        if not path.is_file():
            continue

        try:
            size = path.stat().st_size

            result.append({
                "Name": path.name,
                "Category": categorize(path),
                "Size (KB)": round(size / 1024, 2),
                "Extension": path.suffix.lower() or "(no extension)",
                "Path": str(path),
            })

        except OSError:
            continue

    return result


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("🦥 SlothSort")

st.subheader(
    "Too lazy to organize files? "
    "Let SlothSort do the boring work."
)

st.markdown(
    """
    Your local-first file organizer.

    **Scan. Categorize. Find duplicates. Get AI suggestions.**

    Your files stay on your computer. SlothSort does not
    automatically delete or rename files.
    """
)


# --------------------------------------------------
# SIDEBAR: FOLDER SELECTION
# --------------------------------------------------

with st.sidebar:
    st.header("📂 Choose a folder")

    default_folder = str(
        Path.home() / "Downloads"
    )

    folder_text = st.text_input(
        "Folder path",
        value=st.session_state.get(
            "folder_path",
            default_folder,
        ),
        help="Example: C:\\Users\\YourName\\Downloads",
    )

    st.session_state["folder_path"] = folder_text

    st.caption(
        "For your first test, choose a folder containing "
        "sample files."
    )

folder = Path(folder_text).expanduser()

if not folder.exists() or not folder.is_dir():
    st.error(
        "The selected folder does not exist. "
        "Enter a valid folder path."
    )
    st.stop()

# Avoid rescanning automatically on every interaction.
if st.session_state.get("active_scan_path") != str(folder):
    st.session_state["scanned"] = False
    st.session_state["active_scan_path"] = str(folder)

if st.button("🔍 Scan folder", type="primary"):
    st.session_state["scanned"] = True
    st.session_state["scan_rows"] = scan_folder(folder)
    st.session_state.pop("duplicate_scan_path", None)

if not st.session_state.get("scanned", False):
    st.info("Click **Scan folder** to start.")
    st.stop()

rows = st.session_state.get("scan_rows", [])

st.success(f"Selected folder: `{folder}`")

if not rows:
    st.info(
        "No files found directly inside this folder. "
        "Choose another folder or add test files."
    )
    st.stop()


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

counts = defaultdict(int)

for row in rows:
    counts[row["Category"]] += 1

total_mb = sum(
    row["Size (KB)"] for row in rows
) / 1024

col1, col2, col3 = st.columns(3)

col1.metric("📄 Files found", len(rows))
col2.metric("🗂️ Categories", len(counts))
col3.metric("💾 Total size", f"{total_mb:.2f} MB")

st.divider()

st.header("📊 Folder overview")

category_columns = st.columns(3)

for index, (category, count) in enumerate(
    sorted(counts.items())
):
    with category_columns[index % 3]:
        st.metric(category, count)

st.subheader("📋 File inventory")

st.dataframe(
    [
        {
            "Name": row["Name"],
            "Category": row["Category"],
            "Size (KB)": row["Size (KB)"],
            "Extension": row["Extension"],
        }
        for row in rows
    ],
    use_container_width=True,
    hide_index=True,
)


# --------------------------------------------------
# LOCAL AI FILENAME ASSISTANT
# --------------------------------------------------

st.divider()

st.header("✨ Local AI filename assistant")

st.write(
    "Get a clearer filename suggestion from your local "
    "Ollama model. The model receives only the filename "
    "and category, not the file contents."
)

selected_file = st.selectbox(
    "Choose a file",
    [row["Name"] for row in rows],
    key="ai_filename_choice",
)

if st.button("✨ Suggest a better filename"):
    chosen_row = next(
        row for row in rows
        if row["Name"] == selected_file
    )

    with st.spinner("Asking your local AI..."):
        try:
            suggestion = suggest_filename_with_ai(
                selected_file,
                chosen_row["Category"],
            )

            st.write("**Current filename:**")
            st.code(selected_file)

            st.write("**AI suggestion:**")
            st.code(suggestion)

            if suggestion == selected_file:
                st.info(
                    "The model kept the original filename. "
                    "Try another file if you want."
                )
            else:
                st.success(
                    "Suggestion generated! "
                    "No file has been renamed."
                )

        except requests.exceptions.ConnectionError:
            st.error(
                "Cannot connect to Ollama. Make sure Ollama "
                "is running and the model is installed."
            )

        except requests.exceptions.Timeout:
            st.error(
                "The AI took too long to respond. "
                "Try again after the model finishes loading."
            )

        except requests.exceptions.RequestException as error:
            st.error(f"Ollama request failed: {error}")

        except (ValueError, IndexError) as error:
            st.error(f"Could not process the AI response: {error}")


# --------------------------------------------------
# DUPLICATE DETECTION
# --------------------------------------------------

st.divider()

st.header("🔎 Exact duplicate detection")

st.write(
    "Files are compared using SHA-256 hashes. "
    "Identical hashes indicate matching file contents."
)

if st.button("Check for duplicates"):
    groups = defaultdict(list)
    errors = []

    progress = st.progress(0)

    for index, row in enumerate(rows):
        path = Path(row["Path"])

        try:
            groups[sha256_file(path)].append(path)

        except OSError as error:
            errors.append(
                f"{path.name}: {error}"
            )

        progress.progress(
            (index + 1) / len(rows)
        )

    duplicate_groups = [
        paths for paths in groups.values()
        if len(paths) > 1
    ]

    st.session_state["duplicate_groups"] = [
        [str(path) for path in group]
        for group in duplicate_groups
    ]

    st.session_state["duplicate_scan_path"] = str(folder)
    st.session_state["duplicate_errors"] = errors

if st.session_state.get("duplicate_scan_path") == str(folder):
    duplicate_groups = st.session_state.get(
        "duplicate_groups", []
    )

    if duplicate_groups:
        st.warning(
            f"Found {len(duplicate_groups)} duplicate group(s)."
        )

        for number, group in enumerate(
            duplicate_groups,
            start=1,
        ):
            st.write(f"**Duplicate group {number}**")

            for path in group:
                st.write(f"- `{Path(path).name}`")

    else:
        st.info("No exact duplicate files found.")

    for error in st.session_state.get(
        "duplicate_errors", []
    ):
        st.warning(error)


# --------------------------------------------------
# SAFE FILE ORGANIZATION
# --------------------------------------------------

st.divider()

st.header("🧹 Organize files safely")

st.write(
    "Choose categories, review the proposed moves, "
    "and confirm before any file is moved."
)

available_categories = sorted(counts.keys())

selected_categories = st.multiselect(
    "Select categories to organize",
    options=available_categories,
    default=[],
    key="organization_categories",
)

plan = []

for row in rows:
    if row["Category"] not in selected_categories:
        continue

    source = Path(row["Path"])
    destination_folder = folder / row["Category"]

    # Skip files already in their category folder.
    if source.parent == destination_folder:
        continue

    plan.append({
        "Name": source.name,
        "Category": row["Category"],
        "Source": str(source),
        "Destination": str(
            destination_folder / source.name
        ),
    })

st.write(f"**Files in proposed move plan:** {len(plan)}")

if plan:
    st.dataframe(
        [
            {
                "File": item["Name"],
                "Category folder": item["Category"],
                "Proposed destination": item["Destination"],
            }
            for item in plan
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.warning(
        "Moving files can affect shortcuts or applications "
        "that expect files to remain in their original location."
    )

    confirm = st.checkbox(
        "I reviewed the plan and want to move these files.",
        key="confirm_organization",
    )

    if st.button(
        "✅ Confirm and organize",
        type="primary",
        disabled=not confirm,
    ):
        moved = 0
        errors = []

        for item in plan:
            source = Path(item["Source"])
            category_folder = folder / item["Category"]

            try:
                # Recheck the source before moving.
                if (
                    not source.is_file()
                    or source.parent != folder
                ):
                    errors.append(
                        f"Skipped {source.name}: "
                        "source changed since the scan."
                    )
                    continue

                category_folder.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                destination = unique_destination(
                    category_folder / source.name
                )

                shutil.move(
                    str(source),
                    str(destination),
                )

                moved += 1

            except (OSError, shutil.Error) as error:
                errors.append(
                    f"{source.name}: {error}"
                )

        st.success(f"Moved {moved} file(s).")

        for error in errors:
            st.warning(error)

        # Refresh the inventory after moving files.
        st.session_state["scan_rows"] = scan_folder(folder)
        st.session_state["duplicate_scan_path"] = None

        st.rerun()

else:
    st.info(
        "Select at least one category to prepare a move preview."
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "🦥 SlothSort | Python + Streamlit + optional local AI "
    "| Built for the DEV Community's Slow and Steady theme"
)
