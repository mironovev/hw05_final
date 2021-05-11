import datetime as dt


def year(request):
    current_date = dt.datetime.now()
    return {
        'year': current_date.year
    }
