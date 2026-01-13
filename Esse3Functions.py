from datetime import date, timedelta
import requests
import logging

from config import GLOBAL_ESSE3, BASIC_AUTH

logger = logging.getLogger('log')

def retrieveAppelliFromEsse3(cds, adid,outputMail):
    url = GLOBAL_ESSE3+'calesa-service-v1/appelli/'
    cds = cds  # li prendo da un foglio Google
    adid = adid  # li prendo da un foglio Google
    # specifico un intervallo di tempo di una settimana a partire da oggi
    minData = date.today().strftime('%d/%m/%Y')
    maxData = (date.today() + timedelta(days=14)).strftime('%d/%m/%Y')
    #minData = "01/01/2025"
    #maxData = "31/01/2025"
    urlRequest = url+cds+'/'+adid+'/?'
    param = {'minDataApp': minData, 'maxDataApp': maxData}
    headers = {'accept': 'application/json',
               'authorization': BASIC_AUTH,
               'X-Esse3-permit-invalid-jsessionid': 'true'}
    try:
        response = requests.get(url=urlRequest, params=param, headers=headers)
        response.raise_for_status()
        appelli = response.json()
        return appelli
    except requests.exceptions.HTTPError as e:
        stringaErr = " Errore nel prendere gli appelli da esse3 per il cds:" + \
            str(cds)+" e adID:"+str(adid)+"; Errore:"+str(e)
        print(stringaErr)
        logger.error(stringaErr)
        outputMail.append(stringaErr)
        return None


def listaStudenti(cdsId, adId, appId):
    url = f"{GLOBAL_ESSE3}calesa-service-v1/appelli/{cdsId}/{adId}/{appId}/iscritti"
    # condizione: se l'iscrizione all'esame è conclusa e l'esame non è ancora iniziato
    #if datetime.strptime(appello['dataFineIscr'], '%d/%m/%Y %H:%M:%S').date() <= today and today <= datetime.strptime(appello['dataInizioApp'], '%d/%m/%Y %H:%M:%S').date():
        # API che ritorna lista degli studenti
    headers = {'accept': 'application/json',
                   'authorization': BASIC_AUTH,
                   'X-Esse3-permit-invalid-jsessionid': 'true'}
    params = {'attoreCod': 'STU'}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        if (response.json() != []):
            studentiIscritti = response.json()
            #ora devo aggiornare i dati degli studenti, sostituendo lo userId con l'alias
            for studente in studentiIscritti:
                anagrafica_studente = anagrafica(studente['codFisStudente'])
                alias_userId = anagrafica_studente['emailAte'].split("@")[0]
                studente['userId'] = alias_userId
            return studentiIscritti
    except requests.HTTPError as ex:
        raise ex


def trovaDocente(presidenteId):
    
    url = f"{GLOBAL_ESSE3}docenti-service-v1/docenti/{presidenteId}"
    # API che ritorna il docente
    headers = {'accept': 'application/json',
               'authorization': BASIC_AUTH,
               'X-Esse3-permit-invalid-jsessionid': 'true'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        docente = response.json()[0]

        return docente
    except requests.HTTPError as ex:
        raise ex
    
def anagrafica(codice_fiscale :str):
    
    url = f"{GLOBAL_ESSE3}anagrafica-service-v2/persone"
        
    headers = {'accept': 'application/json',
               'authorization': BASIC_AUTH,
               'X-Esse3-permit-invalid-jsessionid': 'true'}
    params = {'codFis': codice_fiscale}
    try:
        response = requests.get(url, headers=headers, params=params)
        if (response.json() != []):
            utente = response.json()[0]
            return utente
    except Exception as e:
        stringaErr = f"Errore: utente non trovato {codice_fiscale} --> eccezione: {e} "
        logger.error(stringaErr)
        
        return None
    
    
def getCommissioneAppello(cdsId, adId, appId):
    url = f"{GLOBAL_ESSE3}calesa-service-v1/appelli/{cdsId}/{adId}/{appId}/comm"
    headers = {'accept': 'application/json',
               'authorization': BASIC_AUTH,
               'X-Esse3-permit-invalid-jsessionid': 'true'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        commissione = response.json()
        return commissione
    except requests.HTTPError as ex:
        raise ex
    
    
if __name__ == "__main__":
    # Esempio di utilizzo
    cds = "10881"
    adid = "47305"
    appId = "120"
    commissione = getCommissioneAppello(cds, adid, appId)
    if commissione:
        for docente in commissione:
            print(f"Docente: {docente['docenteNome']} {docente['docenteCognome']}, ID: {docente['docenteId']}")
            docenteEsse3 = trovaDocente(docente['docenteId'])
            print(f"Docente trovato: {docenteEsse3}")
            if not docenteEsse3['userId']:
                print('docente senza userId, non posso iscriverlo')
            # ricavo userId dall'email nel campo eMail userId@unife.it
            userId = docenteEsse3['eMail'].split('@')[0]
            print(f"UserId del docente: {userId}")
          
        print("Commissione trovata:", commissione)
    else:
        print("Nessuna commissione trovata.")