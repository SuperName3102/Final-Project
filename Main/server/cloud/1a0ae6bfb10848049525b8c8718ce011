import os
import shutil
import subprocess
import zipfile

# Define file and folder names
current_folder = os.getcwd()
dist_folder = os.path.join(current_folder, 'dist')
build_folder = os.path.join(current_folder, 'build')
spec_file = os.path.join(current_folder, 'client.spec')
old_exe = os.path.join(current_folder, 'IdanCloud.exe')
client_exe_in_dist = os.path.join(dist_folder, 'client.exe')
new_exe = os.path.join(current_folder, 'IdanCloud.exe')

# Define the folders to be zipped
folders_to_include = ['assets', 'gui']
zip_file = os.path.join(current_folder, 'IdanCloud.zip')

# Run PyInstaller to package client.pyw
subprocess.run(['pyinstaller', '--onefile', 'client.pyw'])

# Remove old IdanCloud.exe if it exists
if os.path.exists(old_exe):
    os.remove(old_exe)

# Move and rename client.exe
if os.path.exists(client_exe_in_dist):
    shutil.move(client_exe_in_dist, new_exe)

# Delete dist and build folders, and client.spec file
if os.path.exists(dist_folder):
    shutil.rmtree(dist_folder)

if os.path.exists(build_folder):
    shutil.rmtree(build_folder)

if os.path.exists(spec_file):
    os.remove(spec_file)

# Delete old IdanCloud.zip if it exists
if os.path.exists(zip_file):
    os.remove(zip_file)

# Create a new zip file containing IdanCloud.exe, assets, and gui folders
with zipfile.ZipFile(zip_file, 'w') as zipf:
    # Add IdanCloud.exe to the zip file
    if os.path.exists(new_exe):
        zipf.write(new_exe, os.path.basename(new_exe))

    # Add the 'assets' and 'gui' folders to the zip file
    for folder in folders_to_include:
        folder_path = os.path.join(current_folder, folder)
        if os.path.exists(folder_path):
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, current_folder)  # Preserve folder structure in the zip
                    zipf.write(file_path, arcname)

print("Process complete! New IdanCloud.zip created.")