from smb import SMBConnection

try:
    conn = SMBConnection(username,password,'name',system_name,domain,use_ntlm_v2=True,
                         sign_options=SMBConnection.SIGN_WHEN_SUPPORTED,
                         is_direct_tcp=True) 
    connected = conn.connect(system_name,445)

    try:
        Response = conn.listShares(timeout=30)  # obtain a list of shares
        print('Shares on: ' + system_name)

        for i in range(len(Response)):  # iterate through the list of shares
            print("  Share[",i,"] =", Response[i].name)

            try:
                # list the files on each share
                Response2 = conn.listPath(Response[i].name,'/',timeout=30)
                print('    Files on: ' + system_name + '/' + "  Share[",i,"] =",
                                       Response[i].name)
                for i in range(len(Response2)):
                    print("    File[",i,"] =", Response2[i].filename)
            except:
                print('### can not access the resource')
    except:
        print('### can not list shares')    
except:
    print('### can not access the system')