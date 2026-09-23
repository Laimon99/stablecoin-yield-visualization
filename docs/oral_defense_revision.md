# Discussione della versione revisionata

Simone Ragusini, 945119, s.ragusini@campus.unimib.it.

## Percorso di esposizione

1. Apri con la domanda: quanto è persistente un APY elevato, e quale contesto serve
   per interpretarlo? Specifica che il progetto riguarda rendimenti quotati.
2. Spiega unità di analisi, selezione non casuale e soglia inclusiva APY ≥ 10%.
3. Collega distribuzione asimmetrica, episodi brevi e instabilità delle classifiche.
4. Usa meccanismi e depeg per mostrare perché rendimenti nominali simili possono
   avere significati diversi. Non chiamare il TVL “flusso netto”.
5. Chiudi la parte empirica con lo screen congiunto e le verifiche di sensibilità.
6. Usa le nuove slide per chiarire incertezza, strumenti e riproducibilità.
7. In conclusione torna ai due giorni di durata mediana e alla necessità di contesto.

## Demo breve del secondo strumento

Apri l'HTML prima dell'esame. Seleziona “First 30 days”, mostra il tooltip al
giorno 30 e l'intervallo. Poi mostra il churn a 30 giorni con il numero di
confronti validi. Le tabelle in fondo consentono di leggere i dati senza tooltip.
Il file funziona senza connessione. Non trasformare la demo in un tour di pulsanti.

## Domande probabili

**Perché due mediane APY diverse, 4,29% e 4,47%?**
La prima pesa le osservazioni pool-giorno. La seconda è la mediana delle mediane
dei singoli pool e serve allo screen. I pool con più giorni pesano di più solo
nella prima. Nessuna delle due è ponderata per capitale.

**Due giorni è una previsione per un investimento?**
No. È una durata tipica degli episodi osservati nel campione selezionato. Non
include percorso di un portafoglio, costi, slippage o rendimento realizzato.

**Che cosa significa il 6,2% a 30 giorni?**
È S(30), probabilità stimata che un episodio osservato duri oltre 30 giorni,
con trattamento della censura finale. L'intervallo puntuale è circa 5,34–7,19%.
Le ipotesi di indipendenza e censura non informativa sono limiti, non fatti provati.

**La curva include tutto ciò che conta per l'incertezza?**
No. L'intervallo non corregge episodi ripetuti nello stesso pool, selezione del
campione o inizio dell'episodio prima dell'ingresso nel pannello. Per inferenza
più forte servirebbero analisi degli episodi iniziati dopo l'ingresso e bootstrap
per pool. Queste estensioni non vengono dichiarate come già eseguite.

**La robustezza a 90 giorni dimostra che i pool nuovi si comportano allo stesso modo?**
No. La selezione originale richiede almeno 180 osservazioni del provider. La
verifica a 90 giorni non recupera pool esclusi a monte. Descrive un filtro interno.

**Il TVL sale perché l'APY sale?**
Il grafico mostra associazioni temporali. Non c'è gruppo di controllo né un
disegno che identifichi causalità. TVL e APY possono rispondere a fattori comuni;
anche la disponibilità degli eventi nel tempo può cambiare.

**Quali sono i due strumenti di visualizzazione?**
Matplotlib per le figure analitiche statiche, Plotly per tre visualizzazioni
interattive basate sugli stessi aggregati. Seaborn supporta Matplotlib. PowerPoint
è il formato di presentazione, Artifact Tool ne costruisce il layout.

**Un altro studente può riprodurre tutto?**
Può ricostruire e controllare le evidenze aggregate senza API con un comando.
Può ripetere il metodo completo con dati disponibili al momento, soggetti ai
termini dei provider. Non prometto identità del dataset storico non distribuito,
né ricostruzione del PowerPoint senza il runtime opzionale dichiarato.

**Perché non indichi il pool migliore?**
Lo screen visualizza tre dimensioni senza stimare tutti i rischi. Non integra
sicurezza dei contratti, eseguibilità, liquidità effettiva e situazione personale.
La qualificazione di un pool come “migliore” andrebbe oltre l'evidenza.

**Chi può riutilizzare il progetto?**
Codice MIT; presentazione e testi originali CC BY 4.0 con attribuzione a Simone
Ragusini. I dati di DeFiLlama e CoinGecko conservano i loro termini separati.
