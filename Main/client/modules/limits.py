# 2024 © Idan Hazay

class Limits:
    """
    Users networking and files limitations, based on subscription
    """
    def __init__(self, level):
        level = int(level)
        if (level == 0):
            self.max_storage = 100_000
            self.max_file_size = 50
            self.max_upload_speed = 5
            self.max_download_speed = 10
        elif (level == 1):
            self.max_storage = 250_000
            self.max_file_size = 100
            self.max_upload_speed = 10
            self.max_download_speed = 20
        elif (level == 2):
            self.max_storage = 500_000
            self.max_file_size = 250
            self.max_upload_speed = 15
            self.max_download_speed = 30
        elif (level == 3):
            self.max_storage = 1_000_000
            self.max_file_size = 500
            self.max_upload_speed = 25
            self.max_download_speed = 50
        else:
            raise Exception
