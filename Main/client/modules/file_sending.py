from PyQt6.QtCore import QThread, pyqtSignal
import time, uuid, traceback, os
from modules.config import *
from modules.limits import Limits

class FileSending():
    def __init__(self, window):
        self.window = window
        self.active_threads = []
        self.file_queue = []

    def send_files(self, cmd = "FILS", file_id = None, resume_file_id = None, location_infile = 0):
        if len(self.active_threads) >= 1: return
        try: self.window.file_upload_progress.show()
        except: pass
        try:
            self.window.stop_button.setEnabled(True)
            self.window.stop_button.show()
        except: pass
        thread = FileSenderThread(cmd, file_id, resume_file_id, location_infile, self.window, self.file_queue)

        self.active_threads.append(thread)


        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self.active_threads.remove(thread))
        thread.finished.connect(self.window.finish_sending)
        
        thread.progress.connect(self.window.update_progress)
        thread.progress_reset.connect(self.window.reset_progress)# Connect progress signal to progress bar
        thread.message.connect(self.window.set_message)
        thread.error.connect(self.window.set_error_message)
        
        thread.start()


    
    def resume_files_upload(self, id, progress):
        uploading_files = self.window.json.get_files_uploading_data()
        # Iterate through the dictionary and print file_id and file_path
        for file_id, details in uploading_files.items():
            if id == file_id:
                file_path = details.get("file_path")
                if not os.path.exists(file_path): continue
                self.file_queue.extend([file_path])
                self.window.protocol.send_files(resume_file_id=file_id, location_infile=int(progress))
                break
    
    

class FileSenderThread(QThread):
        finished = pyqtSignal()  # Signal to notify that file sending is done
        error = pyqtSignal(str)  # Signal to notify error messages
        progress = pyqtSignal(int)  # Signal to update progress bar
        progress_reset = pyqtSignal(int)
        message = pyqtSignal(str)  # Signal to update the message

        def __init__(self, cmd, file_id, resume_file_id, location_infile, window, file_queue):
            super().__init__()
            self.files_uploaded = []
            self.cmd = cmd
            self.file_id = file_id
            self.resume_file_id = resume_file_id
            self.running = True
            self.location_infile = location_infile
            self.window = window

        def run(self):
            try:
                for file_path in self.file_queue:
                    start = time.time()
                    bytes_sent = 0
                    
                    try: self.window.stop_button.setEnabled(True)
                    except: pass
                    if self.file_id != None:
                        file_name = self.file_id
                    else:
                        file_name = file_path.split("/")[-1]  # Extract the file name
                    file_id = uuid.uuid4().hex
                    uploading_file_id = file_id
                    if self.resume_file_id == None:
                        print("start upload:", file_id)
                        start_string = f"{self.cmd}|{file_name}|{self.window.user["cwd"]}|{os.path.getsize(file_path)}|{file_id}"
                        self.window.protocol.send_data(start_string.encode())
                        self.window.json.update_json(True, file_id, file_path)
                    else: file_id = self.resume_file_id
                    
                    if not os.path.isfile(file_path):
                        self.error.emit("File path was not found")
                        return

                    size = os.path.getsize(file_path)
                    left = size % chunk_size
                    sent = self.location_infile
                    self.progress.emit(sent)
                    self.progress_reset.emit(size)
                    self.message.emit(f"{file_name} is being uploaded")
                    try:
                        with open(file_path, 'rb') as f:
                            f.seek(self.location_infile)
                            for i in range((size - self.location_infile) // chunk_size):
                                if self.running == False:
                                    break

                                location_infile = f.tell()
                                data = f.read(chunk_size)
                                
                                current_time = time.time()
                                elapsed_time = current_time - start

                                if elapsed_time >= 1.0:
                                    start = current_time
                                    bytes_sent = 0
                                    
                                self.window.protocol.send_data(f"FILD|{file_id}|{location_infile}|".encode() + data)
                                bytes_sent += len(data)

                                sent += chunk_size
                                self.progress_reset.emit(size)
                                self.message.emit(f"{file_name} is being uploaded")
                                self.progress.emit(sent)  # Update progress bar
                                
                                if bytes_sent >= (Limits(self.window.user["subscription_level"]).max_upload_speed - 1) * 1_000_000:
                                    time_to_wait = 1.0 - elapsed_time
                                    if time_to_wait > 0:
                                        time.sleep(time_to_wait)
                            if self.running == False:
                                self.running = True
                                continue
                            location_infile = f.tell()
                            data = f.read(left)
                            if data != b"":
                                self.window.protocol.send_data(f"FILE|{file_id}|{location_infile}|".encode() + data)
                                self.progress_reset.emit(size)
                                self.message.emit(f"{file_name} is being uploaded")
                                self.progress.emit(sent)  # Final progress update
                                
                    except:
                        print(traceback.format_exc())
                        return
                    finally:
                        self.window.json.update_json(True, file_id, file_path, remove=True)
                if self.file_id != None: os.remove(file_path.split("/")[-1])
                self.finished.emit() 
            except:
                print(traceback.format_exc())
                print(type(self.file_queue))


class File():
    def __init__(self, window, save_location, id, size, is_view = False, file_name = None):
        self.save_location = save_location
        self.id = id
        self.size = size
        self.is_view = is_view
        self.file_name = file_name
        self.start_download()
        self.window = window
    
    def start_download(self):
        if not os.path.exists(self.save_location):
            with open(self.save_location, 'wb') as f:
                f.write(b"\0")
                f.flush()

    def add_data(self, data, location_infile):
        try: self.window.file_upload_progress.show()
        except: pass
        self.window.update_progress(location_infile)
        self.window.reset_progress(self.size) 
        self.window.set_message(f"File {self.file_name} is downloading")
        try:
            with open(self.save_location, 'r+b') as f:
                f.seek(location_infile)
                f.write(data)
                f.flush()
                self.window.json.update_json(False, self.id, self.save_location, remove=True)
                self.window.json.update_json(False, self.id, self.save_location, file=self, progress=location_infile)
        except:
            self.uploading = False
    
    def delete(self):
        if os.path.exists(self.save_location): os.remove(self.save_location)