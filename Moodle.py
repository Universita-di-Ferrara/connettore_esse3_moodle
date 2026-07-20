import logging
from datetime import datetime, timedelta
import time

import requests
from config import GLOBAL_API, GLOBAL_FORMAT, GLOBAL_TOKEN

logger = logging.getLogger('log')

def moodle_request(ws, body):
    apiUrl = GLOBAL_API
    token = GLOBAL_TOKEN
    format = GLOBAL_FORMAT
    wsFunction = f"&wsfunction={ws}"
    url = apiUrl+token+wsFunction+format
    try:
        response_html = requests.post(url, params = body)
        response = response_html.json()
        response_html.raise_for_status()
        logger.info(response)
        if response and 'exception' in response:
            raise Exception(f"Eccezione in {ws} {response['errorcode']}: {response['message']}")
        return response
    except requests.exceptions.HTTPError as e:
        logger.debug(f"Errore durante la chiamata {ws}")
        raise Exception(f"Errore durante la chiamata {ws}: {e}")
    except Exception as e:
        logger.debug(f"Errore durante la chiamata {ws}")
        raise Exception(f"Errore durante la chiamata {ws}: {e}")
    
    
def checkCategoriaMoodle(nomeCategoria, idparent):
    # prima di creare la categoria devo verificare che non esista già con quel nome e dentro la categoria padre
    ws = "core_course_get_categories"
    params = {"criteria[0][key]": "name", "criteria[0][value]": nomeCategoria,
         "criteria[1][key]": "parent", "criteria[1][value]": idparent, "addsubcategories": "0"}
    try:
        response = moodle_request(ws, params)
        # se la categoria esiste la ritorno se no ritorno None
        if response:
            return response
        else:
            return None
    except Exception as e:
        raise Exception(e)



def checkCorsoMoodle(appello, turni):
    
    # dopo aver trovato la categoria o creata devo verificare che non abbia già creato il corso all'interno di essa attraverso la ricerca dello shortname
    shortname = f"Appello {appello['cdsId']}_{appello['adId']}_{appello['dataInizioApp'].split(' ')[0]}_{appello['presidenteCognome']}"
    if (turni):
        shortname+=f"_{appello['appId']}"
    ws = "core_course_get_courses_by_field"
    params = {"field": "shortname", "value": shortname}
    try:
        response = moodle_request(ws, params)
        if response and response['courses']:
            return response['courses'][0]
        else:
            return False
    except Exception as e:
        raise Exception(e)
    
    
def createCategory(nomeCategoria, idCategoriaPadre):
    ws = "core_course_create_categories"
    try:
        #controllo che la categoria non sia già presente
        categoria = checkCategoriaMoodle(nomeCategoria, idCategoriaPadre)
        if categoria is None:
            #creo la categoria
            params = {"categories[0][name]": nomeCategoria,
                 "categories[0][parent]": idCategoriaPadre}
            response = moodle_request(ws, params)
            print(response)
            return response
        else:
            return categoria
    except Exception as e:
        raise Exception(e)
    
    
def createCourse(appello, singolaAttivita, turni, categoriaId):
    
    ws = "core_course_create_courses"
    dataChiusura = datetime.strptime(appello['dataInizioApp'], '%d/%m/%Y %H:%M:%S')+timedelta(days=1)
    dataChiusuraTS = int(datetime.timestamp(dataChiusura))
    dataInizio = datetime.strptime(appello['dataInizioApp'], '%d/%m/%Y %H:%M:%S')
    dataInizioTS = int(datetime.timestamp(dataInizio))
    # setto i parametri per la creazione del corso
    fullname = f"{appello['adDes'].replace(' - NO ESAME', '')} Esame del {appello['dataInizioApp'].split(' ')[0]}"
    shortname = f"Appello {appello['cdsId']}_{appello['adId']}_{appello['dataInizioApp'].split(' ')[0]}_{appello['presidenteCognome']}"
    if (turni):
        shortname+=f"_{appello['appId']}"
    summaryCourse = f"{appello['cdsDes']} \n {appello['desApp']}"
    if singolaAttivita:
        params = {"courses[0][fullname]": fullname, "courses[0][shortname]": shortname, "courses[0][categoryid]": categoriaId, "courses[0][format]": 'singleactivity',
             "courses[0][courseformatoptions][0][name]": "activitytype", "courses[0][courseformatoptions][0][value]": "quiz",
             "courses[0][startdate]": dataInizioTS, "courses[0][enddate]": dataChiusuraTS, "courses[0][summary]": summaryCourse,
             "courses[0][customfields][0][shortname]":"cds_id", "courses[0][customfields][0][value]":appello['cdsId'],
             "courses[0][customfields][1][shortname]":"ad_id", "courses[0][customfields][1][value]":appello['adId'],
             "courses[0][customfields][2][shortname]":"app_id", "courses[0][customfields][2][value]":appello['appId']}
    else:
        params = {"courses[0][fullname]": fullname, "courses[0][shortname]": shortname, "courses[0][categoryid]": categoriaId,
            "courses[0][startdate]": dataInizioTS, "courses[0][enddate]": dataChiusuraTS, "courses[0][summary]": summaryCourse,
            "courses[0][customfields][0][shortname]":"cds_id", "courses[0][customfields][0][value]":appello['cdsId'],
            "courses[0][customfields][1][shortname]":"ad_id", "courses[0][customfields][1][value]":appello['adId'],
            "courses[0][customfields][2][shortname]":"app_id", "courses[0][customfields][2][value]":appello['appId']}
    try:
            # creo il corso
        response = moodle_request(ws, params)      
        return response[0]
    
    except Exception as e:
        raise Exception(e)


def retrieveUser(username):
    ws = "core_user_get_users_by_field"
    step = 30
    usersMoodle = []
    try:
        for i in range(0, len(username), step):
            params = {"field": "username", "values[]": username[i:i+step]}
            response = moodle_request(ws, params)
            usersMoodle.extend(response)
            time.sleep(2)
        return usersMoodle
        
    except Exception as ex:
        raise(ex)

def enrollDocente(docente, corsoMoodleId):
    if not docente['userId']:
            # ricavo userId dall'email nel campo eMail userId@unife.it
            docente['userId'] = docente['eMail'].split('@')[0]
    userMoodle = retrieveUser([docente['userId']])
    idCorsoMoodle = corsoMoodleId
    try:
        # preparo i parametri per la prossima chiamata
        ws = "enrol_manual_enrol_users"
        if (not userMoodle): 
            userMoodle = creaDocente(docente)
        # il docente esiste già in moodle e quindi lo iscrivo
        id = userMoodle[0]['id']
        params = {
                "enrolments[0][roleid]": 3,
                "enrolments[0][userid]": id,
                "enrolments[0][courseid]": idCorsoMoodle
        }
        response = moodle_request(ws, params)
        return response
    except Exception as e:
        raise Exception(e)

def creaDocente(docente):
    params = {
        "users[0][createpassword]": 0,
        "users[0][username]": docente['userId'],
        "users[0][auth]": "shibboleth",
        "users[0][firstname]": docente['docenteNome'],
        "users[0][lastname]": docente['docenteCognome'],
        "users[0][email]": docente['eMail']
    }
    
    ws = "core_user_create_users"
    try:
        response = moodle_request(ws, params)
        return response
    except Exception as e:
        raise Exception(e)
    
    

def EnrollStudenti(studentiIscritti, idCorsoMoodle):
    
    arrayUsername = []
    studentiDaCreare = []
    paramsEnrollStudents = {}
    ws = "enrol_manual_enrol_users"
    # posso creare un array di valori con lo username
    for user in studentiIscritti:
        arrayUsername.append(user['userId'])
    
    try:
        studentiMoodle = retrieveUser(arrayUsername)
        print(f"lunghezza utenti trovati su Moodle {len(studentiMoodle)}")
        arrayUsername.clear()
        for user in studentiMoodle:
            arrayUsername.append(user['username'])        
        for studente in studentiIscritti:
            if studente['userId'] not in arrayUsername:
                studentiDaCreare.append(studente)
        if studentiDaCreare: 
            newusers = creaUtentiMoodle(studentiDaCreare)
            print(f"lunghezza utenti trovati da creare {len(newusers)}")
            studentiMoodle += newusers
        counter = 0
        print(f"Lunghezza studentiIScritti:{len(studentiIscritti)}\nlunghezza utentiMoodle:{len(studentiMoodle)}")
        while (counter < len(studentiIscritti)):
            for j in range(1, 20):
                
                if (counter < len(studentiIscritti)):
                    print(j)
                    print(studentiIscritti[counter])
                    studenteMoodle = studentiMoodle[counter]
                    paramsEnrollStudents.update({
                    "enrolments["+str(j)+"][roleid]": 5,
                    "enrolments["+str(j)+"][userid]": studenteMoodle['id'],
                    "enrolments["+str(j)+"][courseid]": idCorsoMoodle
                    })
                    counter += 1
            moodle_request(ws, paramsEnrollStudents)
            paramsEnrollStudents.clear()
            time.sleep(2)
        logger.info(f"Iscritti {counter} studenti")
    except Exception as e:
        raise Exception(e)


def creaUtentiMoodle(utenti):

    ws = "core_user_create_users"
    params = {}
    counter = 0
    allnewusers = []
    while counter < len(utenti):
        for j in range(0,20):
            if counter<len(utenti):
                user = utenti[counter]
                
                if user['nomeStudente'] == "   ":
                    user['nomeStudente'] = "XXX"
                params.update({
                    "users["+str(j)+"][createpassword]": 0,
                    "users["+str(j)+"][username]": user['userId'],
                    "users["+str(j)+"][auth]": "shibboleth",
                    "users["+str(j)+"][firstname]": user['nomeStudente'],
                    "users["+str(j)+"][lastname]": user['cognomeStudente'],
                    "users["+str(j)+"][email]": user['userId']+"@edu.unife.it",
                    "users["+str(j)+"][customfields][0][type]": "esse3Matricola",
                    "users["+str(j)+"][customfields][0][value]": user['matricola']
                })
                counter += 1
        response = moodle_request(ws, params)
        allnewusers.extend(response)
        params.clear()
        time.sleep(2)
    return allnewusers

def creaQuiz(corso, appello):
    #do il nome al quiz come Esame del DATA
    nomequiz = f"Esame del {appello['dataInizioApp'].split(' ')[0]}"
    corsoid = corso['id']
    inizioAppello = appello['dataInizioApp']
    inizioAppello = inizioAppello.split()[0]
    #in base alla tipologiaQuiz decido quale API moodle chiamare
    ws="local_quizapi_create_quiz"

    #imposto i parametri per creare il quiz, id corso in cui inserire, il nome e la data di inizio dell'appello
    # che servirà per settare l'apertura e la chiusura del quiz
    params = {"courseid": corsoid,
                 "namequiz": nomequiz,
                 "datainizio": inizioAppello
                 }

    try:
        moodle_request(ws, params)
    except Exception as e:
        raise Exception(e)