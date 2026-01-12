#!/usr/bin/env python3
"""
dedupe_flatten.py

Flattens a folder tree into the root folder and deduplicates files by CONTENT (SHA-256).
- Keeps ONE copy of each unique file content.
- Moves duplicates into a _duplicates/ folder (does NOT delete).
- Moves remaining files from subfolders into the root folder.
- Removes empty subfolders (except _duplicates).

Usage:
  python dedupe_flatten.py /path/to/root_folder
"""

import os
import sys
import hashlib
import shutil


def hash_file(path: str, blocksize: int = 1024 * 1024) -> str:
    """Return SHA-256 hex digest for file at path."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(blocksize), b""):
            h.update(chunk)
    return h.hexdigest()


def unique_target_path(directory: str, filename: str, suffix: str = "", max_tries: int = 10_000) -> str:
    """
    Return a non-colliding filepath in `directory`.
    If filename exists, appends _1, _2, ... before the extension.
    Optionally adds `suffix` before numbering.
    """
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(directory, f"{base}{suffix}{ext}")
    if not os.path.exists(candidate):
        return candidate

    for i in range(1, max_tries + 1):
        candidate = os.path.join(directory, f"{base}{suffix}_{i}{ext}")
        if not os.path.exists(candidate):
            return candidate

    raise RuntimeError(f"Could not find unique name for {filename} in {directory} after {max_tries} tries.")


def is_within(path: str, folder: str) -> bool:
    """True if path is within folder (after resolving)."""
    path_abs = os.path.abspath(path)
    folder_abs = os.path.abspath(folder)
    return os.path.commonpath([path_abs, folder_abs]) == folder_abs


def main(root: str) -> int:
    root = os.path.abspath(root)

    if not os.path.isdir(root):
        print(f"ERROR: Not a folder: {root}")
        return 2

    duplicates_dir = os.path.join(root, "_duplicates")
    os.makedirs(duplicates_dir, exist_ok=True)

    print(f"Root folder: {root}")
    print(f"Duplicates folder: {duplicates_dir}\n")

    # Pass 1: Deduplicate by content (hash). Move duplicates into _duplicates.
    seen_hashes: dict[str, str] = {}

    print("1) Scanning for duplicates by file content (SHA-256)...")
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip walking into _duplicates
        dirnames[:] = [d for d in dirnames if os.path.abspath(os.path.join(dirpath, d)) != os.path.abspath(duplicates_dir)]

        for filename in filenames:
            full_path = os.path.join(dirpath, filename)

            # Skip files already in _duplicates
            if is_within(full_path, duplicates_dir):
                continue

            try:
                file_hash = hash_file(full_path)
            except (OSError, PermissionError) as e:
                print(f"  [SKIP] Could not read: {full_path} ({e})")
                continue

            if file_hash in seen_hashes:
                # Duplicate content found -> move to _duplicates
                target = unique_target_path(duplicates_dir, filename, suffix="_dup")
                print(f"  DUPLICATE:\n    {full_path}\n    -> {target}")
                try:
                    shutil.move(full_path, target)
                except (OSError, PermissionError) as e:
                    print(f"  [ERROR] Could not move duplicate: {full_path} ({e})")
            else:
                seen_hashes[file_hash] = full_path

    # Pass 2: Flatten - move remaining files in subfolders into root.
    print("\n2) Flattening: moving remaining files into root folder...")
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip root and _duplicates
        if os.path.abspath(dirpath) == os.path.abspath(root):
            continue
        if os.path.abspath(dirpath) == os.path.abspath(duplicates_dir):
            continue
        if is_within(dirpath, duplicates_dir):
            continue

        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            if is_within(full_path, duplicates_dir):
                continue

            target = os.path.join(root, filename)
            if os.path.abspath(full_path) == os.path.abspath(target):
                continue

            # Avoid overwriting if same name exists in root
            if os.path.exists(target):
                target = unique_target_path(root, filename)

            print(f"  MOVE:\n    {full_path}\n    -> {target}")
            try:
                shutil.move(full_path, target)
            except (OSError, PermissionError) as e:
                print(f"  [ERROR] Could not move: {full_path} ({e})")

    # Pass 3: Remove empty directories (except root and _duplicates)
    print("\n3) Removing empty folders...")
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        if os.path.abspath(dirpath) in (os.path.abspath(root), os.path.abspath(duplicates_dir)):
            continue
        if is_within(dirpath, duplicates_dir):
            continue
        try:
            if not os.listdir(dirpath):
                print(f"  RMDIR: {dirpath}")
                os.rmdir(dirpath)
        except OSError:
            # Ignore folders that aren't empty or can't be removed
            pass

    print("\nDone.")
    print(f"- Unique files are in: {root}")
    print(f"- Duplicates were moved to: {duplicates_dir}")
    print("If everything looks correct, you can delete the _duplicates folder manually.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python dedupe_flatten.py PATH_TO_MAIN_FOLDER")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
