# Connettore Esami Esse3 > Moodle

## Indice
* Requisiti e configurazioni iniziali:
  * Server Python;
  * Plugin Moodle per la creazione di Quiz tramite API;
  * Account Tecnico Esse3 per chiamare le API (Rilasciato da Cineca);
  * Abilitazione e configurazione delle API su Moodle;
  * Preparazione dello spreasheet di raccordo;
  * Policy utente e campi personalizzati.
* Far girare il connettore.

## Requisiti e configurazioni iniziali

### Server Python
* Versione Python 3.10
* Pipfile in repository per le altre specifiche del progetto.

### Plugin Moodle
Questo plugin serve per esporre un endpoint Moodle che permette di creare i quiz vuoti per gli esami.
* https://github.com/Universita-di-Ferrara/PluginMoodle_API_Quiz
Le funzioni extra introdotte da questo plugin sono tra quelle che andremo a specificare quando configuriamo i webservice su Moodle.
Quando il connettore diventerà un plugin non servirà più.

### Account Tecnico Esse3
Serve per interrogare Esse3 via API. Occorre sentire direttamente Cineca per ottenere queste credenziali.
Una volta ottenute possono essere testate sullo Swagger delle API di Cineca.

### Configurazione Webservice su Moodle
Nella sezione admin/settings.php?section=webservicesoverview
* Abilitare Webservice
* Abilitare REST
* Creare un servizio
* Attribuire le funzioni al servizio: 
  * core_course_create_categories
  * core_course_create_courses
  * core_course_get_categories
  * core_course_get_courses_by_field
  * core_customfield_create_category
  * core_user_create_users
  * core_user_get_users_by_field
  * enrol_manual_enrol_users
  * local_quizapi_create_offlinequiz
  * local_quizapi_create_quiz

### Spreadsheet di raccordo

Come facciamo a specificare quali esami di quali insegnamenti vogliamo sincronizzati su Moodle?
Noi attualmente usiamo uno spreadsheet in mano agli amministratori delle piattaforme Moodle nel quale vengono inseriti
i dati degli insegnamenti su Esse3.
Qui trovate il nostro modello di foglio: [Modello](https://docs.google.com/spreadsheets/d/1EnFae5TMrcLrQ5bS8x__9CWxQk9s_v1mUzONxtZzCnU/edit?usp=sharing])

Per sincronizzare un esame è necessario specificare 
* Cds ID (nella url dell'appello d'esame della bacheca appelli pubblica di Esse3)
* Ad ID (nella url dell'appello d'esame della bacheca appelli pubblica di Esse3)
* Dipartimento - Serve per collocare l'esame nella corretta categoria Moodle. Se la categoria indicata non esiste viene creata.
* Singola / Container - Tipologia di Corso Moodle. Corso attività singola o corso normale?
* Turni - Se un esame è composto da più appelli nella stessa giornata e voglio quindi avere esami separati per ogni appello
* Docente - Solo cognome

### Policy utente e campi personalizzati
* Di default gli utenti vengono creati con **auth Shibboleth** dalle funzioni in Moodle.py.
* Di default viene mappato il campo matricola di Esse3 su un campo personalizzato Moodle Esse3Matricola.
 * Questo avviene nella funzione creaUtentiMoodle in Moodle.py
 * È dunque necessario creare un campo personalizzato utente esse3Matricola su Moodle. 


## Far girare il connettore
Svolti tutti passaggi precedenti è possibile mettere in cron le operazioni di sincronizzazione con la cadenza che valutate più opportuna.
La chiamata da mettere in cron è Python3 main.py.
