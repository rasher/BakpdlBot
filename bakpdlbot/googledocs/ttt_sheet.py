from .main import GoogleSheetValues
from tabulate import tabulate

def ZwiftCatEmoji(zcat=None):
    """
    Return str to emoji for backpedal server
    :param zcat: str A+ A B C D E
    :return: str zcat emoji for backpedal server
    """
    if zcat == None:
        return None
    if zcat == 'A+':
        return ':zcataplus:'
    if zcat in ['A','B','C','D','E']:
        return ':zcat' + zcat.lower() + ':'


def FindTttTeam(teamname='BAKPDL 1',teamsize=8):
    """
    :param teamname: string, backpedal teamname to lookup in sheet
    :param teamsize: int, team size, default 8
    :return: string with teamname and teammembers, if found
    """
    values = GoogleSheetValues(spreadsheetid='16ip9cd6kpH2fl0dJYlG4UC1VOJL2eYjd8WSSXJMjss4',range='WTRL TTT Signups!A14:N')
    members = []
    if not values:
        return 'Something went wrong connecting to the google sheet'
    else:
        for row in values:
            if len(row) > 2:
                if row[1] == teamname:
                    i = values.index(row)
                    for j in range(teamsize):
                        if len(values[i+1+j])>1:
                            if values[i+1+j][1] != '':
                                riderinfo = [values[i+1+j][k] for k in [1, 3, 5, 9, 10, 10]]
                                riderinfo[3] = riderinfo[3] + 's'
                                riderinfo[4] = '@'
                                riderinfo[5] = riderinfo[5] + 'W'
                                members.append(riderinfo)
                        teammembers = list(filter(None, members))
                    if len(teammembers)-1 == 0:
                        return teamname + ': 0 riders'
                    if len(teammembers)-1 > 0:
                        teammembers = [['', 'Rider', 'FTP', 'pull', '', 'Target']] + teammembers
                        namelist = tabulate(teammembers)
                        message = teamname + ' (' + str(len(teammembers)-1) + ' riders):\n' + namelist
                        return message
        return 'No team found with name: ' + teamname

if __name__ == '__main__':
    msg = FindTttTeam()
    print(msg)
