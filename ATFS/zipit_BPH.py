import os
import platform
import subprocess
import sys
import shutil

# Script directory and zip name
cdir = os.path.dirname(os.path.abspath(__file__))
zipn = os.path.basename(cdir)

# Detect 7z location
if platform.system() == "Windows":
    seven_zip = r"C:\Program Files\7-Zip\7z.exe"
else:
    seven_zip = shutil.which("7z") or "/opt/homebrew/bin/7z" or "/usr/local/bin/7z"

if not os.path.isfile(seven_zip):
    print(f"❌ 7z not found: {seven_zip}")
    sys.exit(1)

# Targets to include
target_file = "6_append_treefarm.py"
target_dir = "tmp_treefarm"
found_files = []

# Validate and collect paths
target_file_path = os.path.join(cdir, target_file)
if os.path.isfile(target_file_path):
    found_files.append(target_file)

target_dir_path = os.path.join(cdir, target_dir)
if os.path.isdir(target_dir_path):
    found_files.append(target_dir)

# Check for missing items
if not found_files:
    print("❌ Neither target file nor folder found.")
    sys.exit(1)

print("📦 Creating archive:", f"{zipn}.7z")
print("🔧 Command:", [seven_zip, "a", "-t7z", "-bd", f"{zipn}.7z"] + found_files)

# Run 7z
try:
    subprocess.run([seven_zip, "a", "-t7z", "-bd", f"{zipn}.7z"] + found_files, cwd=cdir, check=True)
    print("✅ Archive created successfully.")
except subprocess.CalledProcessError as e:
    print("❌ Archive creation failed:", e)

# Pause if terminal
if sys.stdin.isatty():
    input("Press Enter to exit...")
