import datetime

def GMT_to_AEST_timezone(time):
    reminder = datetime.datetime(2019,4,24,12,0,0,0,tzinfo=None)
    reminder = datetime.datetime(2019,4,24,12,0)
    now = datetime.datetime.now()
    addTenHours = datetime.timedelta(hours=10)
    timeD = now + addTenHours
    print(datetime.datetime.now(), timeD)
    date = datetime.datetime.strptime(time, '%a, %d %b %Y %H:%M:%S %Z')
    #Change the date into local timezone setting AEST
    aestDate = date.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
    time_format = "%d/%m/%Y %H:%M:%S AEST"
    return aestDate.strftime(time_format)
pass    

time = "Mon, 23 Mar 2019 16:33:49 GMT"

print(GMT_to_AEST_timezone(time))