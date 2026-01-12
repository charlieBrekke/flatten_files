# Dedupe + Flatten Folder Script

This repo contains a small Python script that:

- **Deduplicates files by content** (SHA-256 hash)
- **Flattens** a folder tree by moving files from all subfolders into the **root folder**
- Moves duplicates into a `_duplicates/` folder (so nothing is permanently deleted by accident)
- Removes now-empty folders after moving files

## What it does

Given a folder like:

RootFolder/
A/
photo.jpg
B/
photo.jpg (same content)
C/
notes.txt


After running:

- One copy of each unique file content ends up directly inside `RootFolder/`
- Extra copies are moved into `RootFolder/_duplicates/`
- Empty subfolders are removed (except `_duplicates/`)

## Safety notes

- This script **does not delete duplicates** — it moves them to `_duplicates/`.
- Still: **make a backup** of your folder before running if the data matters.
- If different files have the same name but different content, the script will rename using `_1`, `_2`, etc. to avoid overwriting.

## Requirements

- Python 3.8+ recommended (older versions may still work)

## How to run

### Windows (Command Prompt / PowerShell)

```bash
python dedupe_flatten.py "C:\path\to\RootFolder"
