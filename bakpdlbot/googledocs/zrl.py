from .main import GoogleSheetValues

def ZrlSignups():
    """
    :return: integer, amount of zrl signups
    """
    values = GoogleSheetValues(spreadsheetid='16ip9cd6kpH2fl0dJYlG4UC1VOJL2eYjd8WSSXJMjss4',
                               range='ZRL S2 Overview!D22')
    return values[0][0]
