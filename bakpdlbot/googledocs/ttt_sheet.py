from .main import GoogleSheetValues


def findteam(teamname='BAKPDL 1',teamsize=8):
    """
    :param teamname: string, backpedal teamname to lookup in sheet
    :param teamsize: int, team size, default 8
    :return: string with teamname and teammembers, if found
    """
    values = GoogleSheetValues(spreadsheetid='16ip9cd6kpH2fl0dJYlG4UC1VOJL2eYjd8WSSXJMjss4',range='WTRL TTT Signups!A14:N')
    members = []
    if not values:
        return 'No team found with name: ' + teamname
    else:
        for row in values:
            if row[1] == teamname:
                i = values.index(row)
                for j in range(teamsize):
                    members.append(values[i+1+j][3])
                teammembers = list(filter(None, members))
                if len(teammembers) == 0:
                    return '0 riders currently signed up for ' + teamname
                if len(teammembers) > 0:
                    namelist = ', '.join([member for member in teammembers])
                    message = str(len(teammembers)) + ' riders currently signed up for ' + teamname + ': ' + namelist
                    return message

if __name__ == '__main__':
    msg = findteam()
    print(msg)
