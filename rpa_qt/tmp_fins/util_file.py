import datetime
import os


def get_file_mtime(file_path):
    return os.path.getmtime(file_path)



def get_csv_files(dir_path):
    files = []
    for file in os.listdir(dir_path):
        if file.endswith(".csv"):
            # skip file name include "(1)"
            if "(1)" in file:
                continue

            # file modify time in today
            mtime = get_file_mtime(os.path.join(dir_path, file))
            dt_mtime = datetime.datetime.fromtimestamp(mtime)
            if dt_mtime.date() == datetime.date.today():
                files.append(file)
    return files

def delete_today_csv(dir_path):
    for file in os.listdir(dir_path):
        if file.endswith(".csv"):
            mtime = get_file_mtime(os.path.join(dir_path, file))
            dt_mtime = datetime.datetime.fromtimestamp(mtime)
            if dt_mtime.date() == datetime.date.today():
                os.remove(os.path.join(dir_path, file))

if __name__ == '__main__':
    file_path = "D:/00近期工作/2024/20241209(企劃)長庚個案研討/0118湯民哲教授個案/個案01_膠囊咖啡定價策略.docx"
    print(get_file_mtime(file_path))

    dt_c = datetime.datetime.fromtimestamp(get_file_mtime(file_path))
    print(dt_c)

    download_path="C:/Users/n000000930/Downloads"