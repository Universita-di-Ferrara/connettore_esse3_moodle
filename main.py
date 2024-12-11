from datetime import date, datetime
import logging
import logging.config
import os
import time

import yaml

import GSheetFunctions as Google
import Esse3Functions as Esse3
import Moodle as Moodle_ref
from config import LINK_CORSO_MOODLE

# Store current working directory
pwd = os.path.dirname(os.path.abspath(__file__))
os.chdir(pwd)

with open(("logging.yaml")) as fileConfig:
    config = yaml.load(fileConfig, Loader=yaml.FullLoader)

logging.config.dictConfig(config)
logger = logging.getLogger('log')

def recuperaAppelliEsse3():
    try:
        outputemail = []
        batchRequest = {"requests":[]}
        Google.sortAppelli()
        Google.clearAppelli()
        datiSS = Google.getDatiEsse3()
        listaAppelli = Google.getListaAppelli()
        sheetIdListaAppelli = Google.getSheetId("ListaAppelli")
        if datiSS is None:
            logger.error("Non è stato possibile recuperare i dati dal foglio Google")
            return -1
        #per ogni riga del foglio vado a vedere gli esami
        columns = Google.lookup(datiSS[0])
        for index,row in enumerate(datiSS[1:],2):
            if (not row):
                logger.info(f"Terminato alla riga {index+1}")
                break
            
            logger.info(row)
            cdsId = row[columns['cdsid']]
            adId = row[columns['adid']]
            dipartimento = row[columns['dipartimento']]
            attivitàSingola = eval(row[columns['attivitàsingola']].capitalize())
            turni = eval(row[columns['turni']].capitalize())
            docente = row[columns['docente']]
            appelli = Esse3.retrieveAppelliFromEsse3(cdsId, adId, outputemail)
            rowsValues = []
            if not appelli:
                continue
            for appello in appelli:
                #recupero alcuni campi utili
                rowValues = []
                cdsDes = appello['cdsDes']
                adDes = appello['adDes']
                appId = appello['appId']
                dataAppello = appello['dataInizioApp'].split(" ")[0]
                dataFineIscrizioni = appello['dataFineIscr'].split(" ")[0]
                #prendo solo gli appelli del docente indicato
                trovato = Google.trovaInListaAppelli([str(cdsId), str(adId), str(appId)], listaAppelli)
                if not trovato:
                    if (appello['presidenteCognome'] != docente.upper()):
                        print(f"docente esse3: {appello['presidenteCognome']} non corrisponde con il nome nel foglio: {docente}")
                        continue
                    if (appello['tipoEsaCod'] and appello['tipoEsaCod']['value'] == "O"):
                        print(f"esame {appello['adDes']} del {appello['dataInizioApp']} è orale")
                        continue                 
                    categoriaDipartimento = Moodle_ref.createCategory(dipartimento, 0)[0]
                    categoriaCds = Moodle_ref.createCategory(cdsDes, categoriaDipartimento['id'])[0]
                    categoriaAd = Moodle_ref.createCategory(adDes, categoriaCds['id'])[0]
                    #controllo se l'esame ha i turni (1appello = 1corso / turni di esse3)
                    corso = Moodle_ref.checkCorsoMoodle(appello, turni)
                    if not corso:
                        corso = Moodle_ref.createCourse(appello, attivitàSingola, turni, categoriaAd['id'])
                        Moodle_ref.creaQuiz(corso, appello)
                    #inserisco id corso Moodle
                    rowValues = [
                        str(cdsId), 
                        str(adId), 
                        str(appId), 
                        datetime.strptime(dataAppello, "%d/%m/%Y"),
                        dataFineIscrizioni,
                        str(corso['id']),
                        False,
                        False,
                        f"{LINK_CORSO_MOODLE}{corso['id']}",
                        appello['cdsDes'],
                        appello['adDes'],
                        f"{appello['presidenteCognome']}_{appello['presidenteId']}"]
                    rowsValues.append(rowValues)

            Google.createBatchUpdates(rowsValues, batchRequest, sheetIdListaAppelli)
        Google.insertBatchUpdates(batchRequest)
        Google.sortAppelli()
    except Exception as e:
        logger.error(e)

            

def iscrizione_utenti():
    
    listaAppelli = Google.getListaAppelli()
    if listaAppelli is None:
        logger.error("Non è stato possibile recuperare i dati dal foglio Google")
        return -1
    #per ogni riga del foglio vado a vedere gli esami
    columns = Google.lookup(listaAppelli[0])
    for index,row in enumerate(listaAppelli[1:],2):
        if (not row):
            logger.info(f"Terminato alla riga {index}")
            return index
        cdsId = row[columns['cdsid']]
        adId = row[columns['adid']]
        appId = row[columns['appid']]
        idCorsoMoodle = row[columns['idcorsomoodle']]
        dataFineIscrizioni = row[columns['datafineiscr']]
        docenteIscritto = eval(row[columns['docenteiscritto']].capitalize())
        studentiIscritti = eval(row[columns['studentiiscritti']].capitalize())
        docenteId = row[columns['docente']].split("_")[1]
        print(cdsId, adId, appId, idCorsoMoodle, dataFineIscrizioni, docenteIscritto, studentiIscritti, docenteId)
        try:
            if not docenteIscritto:
                docenteEsse3 = Esse3.trovaDocente(docenteId)
                Moodle_ref.enrollDocente(docenteEsse3, idCorsoMoodle)
                Google.insertValue(f"ListaAppelli!G{index}",[[True]])
            if not studentiIscritti and date.today() > datetime.strptime(dataFineIscrizioni, "%d/%m/%Y").date():
                studentiIscrittiEsse3 = Esse3.listaStudenti(cdsId, adId, appId)
                if studentiIscrittiEsse3:
                    Moodle_ref.EnrollStudenti(studentiIscrittiEsse3,idCorsoMoodle)
                    Google.insertValue(f"ListaAppelli!H{index}",[[True]])
        except Exception as ex:
            message = f"An exception of type {type(ex).__name__} occurred. Arguments:\n{ex.args}"
            print (message)
            continue

   
if __name__ == '__main__':
    
    recuperaAppelliEsse3()
    time.sleep(3)
    iscrizione_utenti() 
