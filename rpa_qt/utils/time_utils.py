from datetime import datetime, timedelta, timezone


def get_now_code():
    now = datetime.now()
    now_code = now.strftime("%Y%m%d%H%M%S%f%z")
    return now_code

def get_last_code(days:int=1):
    now = datetime.now()
    last = now - timedelta(days=days)
    last_code = last.strftime("%Y%m%d%H%M%S%f%z")
    return last_code


def get_now_timestamp(tz:timezone=timezone.utc):
    timestamp = datetime.utcnow().replace(tzinfo=tz).timestamp()
    return str(timestamp)

def timestamp2datetime(ts:str,tz:timezone=timezone.utc):
    ts_float=float(ts)
    dt=datetime.fromtimestamp(ts_float, tz=tz)
    return dt

def is_overtime(ts:str,timeout_hours:int=8,tz:timezone=timezone.utc):
    access_token_expires = timedelta(hours=timeout_hours)
    expire_datetime = timestamp2datetime(ts) + access_token_expires  # 注意是用格林威治時間
    expire_timestamp=expire_datetime.timestamp()
    now_utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).timestamp()
    if now_utc_timestamp > expire_timestamp:
        return True #過期
    else:
        return False #沒有過

if __name__ == '__main__':

    ts=get_now_timestamp()
    print(ts)
    dt=timestamp2datetime(ts=ts)
    print(dt)

    print(get_now_code())