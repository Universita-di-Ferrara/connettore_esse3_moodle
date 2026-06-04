from datetime import date, timedelta
import requests
import logging
import time

import config
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import GLOBAL_ESSE3, BASIC_AUTH

logger = logging.getLogger('log')

ESSE3_TIMEOUT_SECONDS = getattr(config, "ESSE3_TIMEOUT_SECONDS", (5, 30))
ESSE3_RETRIES = getattr(config, "ESSE3_RETRIES", 2)
ESSE3_BACKOFF_FACTOR = getattr(config, "ESSE3_BACKOFF_FACTOR", 0.5)
ESSE3_SLOW_REQUEST_SECONDS = getattr(config, "ESSE3_SLOW_REQUEST_SECONDS", 10)
ESSE3_RETRY_STATUS_CODES = getattr(
    config,
    "ESSE3_RETRY_STATUS_CODES",
    (429, 500, 502, 503, 504),
)


class Esse3RequestError(RuntimeError):
    """Errore leggibile per le chiamate HTTP verso Esse3."""


class Esse3TimeoutError(Esse3RequestError):
    """Timeout di connessione o lettura verso Esse3."""


def _esse3_session():
    session = requests.Session()
    retry = Retry(
        total=ESSE3_RETRIES,
        connect=ESSE3_RETRIES,
        read=ESSE3_RETRIES,
        status=ESSE3_RETRIES,
        backoff_factor=ESSE3_BACKOFF_FACTOR,
        status_forcelist=ESSE3_RETRY_STATUS_CODES,
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


_SESSION = _esse3_session()


def _timeout_label():
    if isinstance(ESSE3_TIMEOUT_SECONDS, tuple):
        return f"connect={ESSE3_TIMEOUT_SECONDS[0]}s, read={ESSE3_TIMEOUT_SECONDS[1]}s"
    return f"{ESSE3_TIMEOUT_SECONDS}s"


def _headers():
    return {
        'accept': 'application/json',
        'authorization': BASIC_AUTH,
        'X-Esse3-permit-invalid-jsessionid': 'true',
    }


def _request_esse3(url, params=None, descrizione="chiamata Esse3"):
    started_at = time.monotonic()
    try:
        response = _SESSION.get(
            url,
            headers=_headers(),
            params=params,
            timeout=ESSE3_TIMEOUT_SECONDS,
        )
        elapsed = time.monotonic() - started_at
        if elapsed >= ESSE3_SLOW_REQUEST_SECONDS:
            logger.warning(
                "Chiamata lenta a Esse3 durante %s. URL=%s; params=%s; durata=%.2fs",
                descrizione,
                response.url,
                params,
                elapsed,
            )
        response.raise_for_status()
        try:
            return response.json()
        except ValueError as ex:
            message = (
                f"Esse3 ha risposto con JSON non valido durante {descrizione}. "
                f"URL={response.url}; status={response.status_code}; "
                f"durata={elapsed:.2f}s; risposta={response.text[:500]!r}"
            )
            logger.error(message)
            raise Esse3RequestError(message) from ex
    except requests.exceptions.Timeout as ex:
        elapsed = time.monotonic() - started_at
        message = (
            f"Timeout nella chiamata a Esse3 durante {descrizione}. "
            f"URL={url}; params={params}; timeout={_timeout_label()}; "
            f"retries={ESSE3_RETRIES}; durata={elapsed:.2f}s"
        )
        logger.error(message)
        raise Esse3TimeoutError(message) from ex
    except requests.exceptions.HTTPError as ex:
        elapsed = time.monotonic() - started_at
        response = ex.response
        body = response.text[:500] if response is not None else ""
        status_code = response.status_code if response is not None else "N/D"
        final_url = response.url if response is not None else url
        message = (
            f"Errore HTTP da Esse3 durante {descrizione}. "
            f"URL={final_url}; status={status_code}; params={params}; "
            f"durata={elapsed:.2f}s; risposta={body!r}"
        )
        logger.error(message)
        raise Esse3RequestError(message) from ex
    except requests.exceptions.RequestException as ex:
        elapsed = time.monotonic() - started_at
        message = (
            f"Errore di rete nella chiamata a Esse3 durante {descrizione}. "
            f"URL={url}; params={params}; timeout={_timeout_label()}; "
            f"durata={elapsed:.2f}s; dettaglio={ex}"
        )
        logger.error(message)
        raise Esse3RequestError(message) from ex


def retrieveAppelliFromEsse3(cds, adid,outputMail):
    url = GLOBAL_ESSE3+'calesa-service-v1/appelli/'
    cds = cds  # li prendo da un foglio Google
    adid = adid  # li prendo da un foglio Google
    # specifico un intervallo di tempo di una settimana a partire da oggi
    minData = date.today().strftime('%d/%m/%Y')
    maxData = (date.today() + timedelta(days=14)).strftime('%d/%m/%Y')
    #minData = "17/06/2026"
    #maxData = "17/06/2026"
    urlRequest = url+cds+'/'+adid+'/?'
    param = {'minDataApp': minData, 'maxDataApp': maxData}
    try:
        return _request_esse3(
            urlRequest,
            params=param,
            descrizione=f"recupero appelli cds={cds}, adId={adid}",
        )
    except Esse3RequestError as e:
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
    params = {'attoreCod': 'STU'}
    studentiIscritti = _request_esse3(
        url,
        params=params,
        descrizione=f"recupero iscritti cds={cdsId}, adId={adId}, appId={appId}",
    )
    if (studentiIscritti != []):
        #ora devo aggiornare i dati degli studenti, sostituendo lo userId con l'alias
        for studente in studentiIscritti:
            codice_fiscale = studente['codFisStudente']
            anagrafica_studente = anagrafica(codice_fiscale)
            if not anagrafica_studente or not anagrafica_studente.get('emailAte'):
                message = (
                    "Studente senza emailAte recuperabile da Esse3. "
                    f"codFisStudente={codice_fiscale}; cds={cdsId}; "
                    f"adId={adId}; appId={appId}"
                )
                logger.error(message)
                raise Esse3RequestError(message)
            alias_userId = anagrafica_studente['emailAte'].split("@")[0]
            studente['userId'] = alias_userId
        return studentiIscritti


def trovaDocente(presidenteId):
    
    url = f"{GLOBAL_ESSE3}docenti-service-v1/docenti/{presidenteId}"
    # API che ritorna il docente
    docenti = _request_esse3(
        url,
        descrizione=f"recupero docente presidenteId={presidenteId}",
    )
    if not docenti:
        message = f"Nessun docente trovato su Esse3 per presidenteId={presidenteId}"
        logger.error(message)
        raise Esse3RequestError(message)

    return docenti[0]
    
def anagrafica(codice_fiscale :str):
    
    url = f"{GLOBAL_ESSE3}anagrafica-service-v2/persone"
        
    params = {'codFis': codice_fiscale}
    utenti = _request_esse3(
        url,
        params=params,
        descrizione=f"recupero anagrafica codFis={codice_fiscale}",
    )
    if (utenti != []):
        utente = utenti[0]
        return utente

    logger.warning(f"Utente non trovato su Esse3. codFis={codice_fiscale}")
    return None
    
    
def getCommissioneAppello(cdsId, adId, appId):
    url = f"{GLOBAL_ESSE3}calesa-service-v1/appelli/{cdsId}/{adId}/{appId}/comm"
    return _request_esse3(
        url,
        descrizione=f"recupero commissione cds={cdsId}, adId={adId}, appId={appId}",
    )
    
    
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
