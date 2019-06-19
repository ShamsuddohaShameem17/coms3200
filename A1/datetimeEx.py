import datetime
def GMT_to_AEST_timezone(time):
    date = datetime.datetime.strptime(time, '%a, %d %b %Y %H:%M:%S %Z')
    utcdate = date.replace(tzinfo=datetime.timezone.utc)
    aestTimeZoneInfo = datetime.datetime.now().astimezone().tzinfo
    # print(utcdate.tzname())
    # print(aestTimeZoneInfo)
    #date = utcdate
    time_format = "%d/%m/%Y %H:%M:%S GMT"
    print(date.strftime(time_format))

    # aestDate = datetime.datetime(year = date.year, month = date.month, day = date.day,
    #     hour = date.hour, minute = date.minute, second = date.second)
    aestDate = utcdate.astimezone(tz=aestTimeZoneInfo)
    time_format = "%d/%m/%Y %H:%M:%S AEST"
    newDate = date.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
    print("HELLO",newDate.strftime(time_format))
    return aestDate.strftime(time_format)
pass    

time = "Mon, 11 Mar 2019 4:33:49 GMT"


print(GMT_to_AEST_timezone(time))