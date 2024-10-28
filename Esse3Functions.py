from datetime import date, timedelta
import requests, logging

from config import GLOBAL_ESSE3, BASIC_AUTH

logger = logging.getLogger('log')

def retrieveAppelliFromEsse3(cds, adid,outputMail):
    url = GLOBAL_ESSE3+'calesa-service-v1/appelli/'
    cds = cds  # li prendo da un foglio Google
    adid = adid  # li prendo da un foglio Google
    # specifico un intervallo di tempo di una settimana a partire da oggi
    minData = date.today().strftime('%d/%m/%Y')
    maxData = (date.today() + timedelta(days=14)).strftime('%d/%m/%Y')
    #minData = "01/06/2024"
    #maxData = "30/06/2024"
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
    today = date.today()
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