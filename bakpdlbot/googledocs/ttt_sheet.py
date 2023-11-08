from .main import GoogleSheetValues, MakeSheetConnection
from tabulate import tabulate

SHEET_ID = '16ip9cd6kpH2fl0dJYlG4UC1VOJL2eYjd8WSSXJMjss4'


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


def SignupRider(member, name):
    signups = GoogleSheetValues(spreadsheetid=SHEET_ID, range='WtrlTTTSignupNames')
    signup_length = len(signups)
    discordnames = GoogleSheetValues(spreadsheetid=SHEET_ID, range='DiscordIdNames')
    signups = [r[0] for r in signups if len(r) > 0 and len(str(r[0]).strip()) > 0]
    dn_map = {int(r[0]): r[1:] for r in discordnames}
    if name is not None:
        AddOrUpdateNameMap(member, name)
    elif member.id not in dn_map:
        raise Exception("I don't know who you are - include your name after the command")
    else:
        name = dn_map[member.id][1]
    if name not in signups:
        signups.append(name)
        set_signups(signups, signup_length)


def RemoveSignup(member):
    signups = GoogleSheetValues(spreadsheetid=SHEET_ID, range='WtrlTTTSignupNames')
    signup_length = len(signups)
    discordnames = GoogleSheetValues(spreadsheetid=SHEET_ID, range='DiscordIdNames')
    signups = [r[0] for r in signups if len(r) > 0 and len(str(r[0]).strip()) > 0]
    dn_map = {int(r[0]): r[1:] for r in discordnames}
    if member.id not in dn_map:
        raise Exception("I don't know who you are - include your name after the command")
    name = dn_map[member.id][1]
    if name not in signups:
        raise Exception("You are not signed up")
    else:
        del(signups[signups.index(name)])
        set_signups(signups, signup_length)


def set_signups(signups, signup_length):
    service = MakeSheetConnection()
    while len(signups) < signup_length:
        signups.append('')
    body = {'values': [[signup] for signup in signups]}
    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID, range='WtrlTTTSignupNames', valueInputOption='USER_ENTERED', body=body).execute()


def AddOrUpdateNameMap(member, name):
    discordnames = GoogleSheetValues(spreadsheetid=SHEET_ID, range='DiscordIdNames')
    updated = False
    for row in discordnames:
        if int(row[0]) == member.id:
            row[1] = member.name
            row[2] = name
            updated = True
    if not updated:
        discordnames.append([str(member.id), member.name, name])

    service = MakeSheetConnection()
    body = {'values': discordnames}
    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID, range='DiscordIdNames', valueInputOption='USER_ENTERED', body=body).execute()


def FindTttTeam(teamname='BAKPDL 1',teamsize=8):
    """
    :param teamname: string, backpedal teamname to lookup in sheet
    :param teamsize: int, team size, default 8
    :return: string with teamname and teammembers, if found
    """
    values = GoogleSheetValues(spreadsheetid=SHEET_ID, range='WTRL TTT Signups!F14:S')
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
                    if len(teammembers) == 0:
                        return teamname + ': 0 riders'
                    if len(teammembers) > 0:
                        teammembers = [['', 'Rider', 'FTP', 'pull', '', 'Target']] + teammembers
                        namelist = tabulate(teammembers)
                        message = teamname + ' (' + str(len(teammembers)-1) + ' riders):\n' + namelist
                        return message
        return 'No team found with name: ' + teamname


if __name__ == '__main__':
    msg = FindTttTeam()
    print(msg)
