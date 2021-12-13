from .main import GoogleSheetValues
from tabulate import tabulate

def ZrlSignups():
    """
    :return: integer, amount of zrl signups
    """
    values = GoogleSheetValues(spreadsheetid='16ip9cd6kpH2fl0dJYlG4UC1VOJL2eYjd8WSSXJMjss4',
                               range='ZRL S2 Overview!D22')
    return values[0][0]

def ZrlTeam(teamtag=None,teamsize=12,full=False):
    """

    :param teamtag: string teamtag i.e. 'A1'
    :param teamsize: int teamsize of the team
    :param availability: boolean to show the timezones or not
    :return: message string containing team info
    """
    if full:
        maxrange = 18
        minrange = 2
        tableheader = ["cat", "Name", "FTP", "wkg", "", "AP", "AT", "ME", "E", "C", "S", "W", "N", "AE"]
    else:
        maxrange = 6
        minrange = 3
        tableheader = [teamtag + " Name","FTP","wkg"]

    values = GoogleSheetValues(spreadsheetid='16ip9cd6kpH2fl0dJYlG4UC1VOJL2eYjd8WSSXJMjss4',
                               range='ZRLS2 Team Builder!A:V')

    if not values:
        return 'Something went wrong connecting to the google sheet'
    else:

        for row in values:
            if len(row) > 2:
                if row[1] == 'Team:' and row[2] == teamtag:
                    i = values.index(row)
                    teaminfo = []
                    for j in range((minrange-2), teamsize+1):
                        if values[i + j][3] != '':
                            info = [values[i + j][k] for k in [x for x in range(minrange, maxrange) if x != 7 and x != 8]]
                            teaminfo.append(info)
                    if full:
                        teaminfo[0][1] = ""
                    message = tabulate(teaminfo, headers=tableheader)
                    return message
        return 'Team ' + teamtag + ' not found'
