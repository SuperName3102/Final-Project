# 2024 © Idan Hazay

from enum import Enum


class Errors(Enum):
    GENERAL = f"ERRR|001|General error"
    UNKNOWN = f"ERRR|002|Code not supported"
    LOGIN_DETAILS = f"ERRR|003|Please check your password and email/username and try again."
    USER_REGISTERED = f"ERRR|004|Username already registered"
    EMAIL_REGISTERED = f"ERRR|005|Email address already registered"
    EMAIL_NOT_REGISTERED = f"ERRR|006|Email is not registered"
    NOT_MATCHING_CODE = f"ERRR|007|Code not matching try again"
    CODE_EXPIRED = f"ERRR|008|Code has expired"
    NOT_VERIFIED = f"ERRR|009|User not verified"
    ALREADY_VERIFIED = f"ERRR|010|Already verified"
    FILE_UPLOAD = f"ERRR|011|File didnt upload correctly"
    NO_DELETE_PERMS = f"ERRR|012|Can't delete this user"
    INVALID_DIRECTORY = f"ERRR|013|Invalid directory"
    FILE_NOT_FOUND = f"ERRR|014|File not found"
    FILE_DOWNLOAD = f"ERRR|015|File didnt download correctly"
    FOLDER_EXISTS = f"ERRR|016|This folder already exists"
    EXISTS = f"ERRR|017|File/Folder with same name already exists"