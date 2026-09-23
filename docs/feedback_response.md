# Revisione dopo il feedback del docente

Autore: Simone Ragusini, matricola 945119, s.ragusini@campus.unimib.it.
Revisione: 23 settembre 2026. Campione analizzato: invariato, fino all'8 luglio 2026.

Il feedback riconosce come eccellenti domande, comprensione dei dati, insight,
narrazione e qualità grafica. Le criticità riguardano soprattutto la documentazione
tecnica visibile nelle slide. Non richiedono una nuova tesi né più risultati a ogni costo.
Nessuna revisione può assicurare un voto: l'obiettivo è eliminare le lacune verificabili.

## Risposta punto per punto

| Osservazione | Intervento applicato | Evidenza |
| --- | --- | --- |
| Autore assente | Nome, matricola e indirizzo universitario sulla copertina | Slide 1 della versione revisionata |
| Strumenti analitici non dichiarati | Python, pandas, NumPy, lifelines, SciPy, scikit-learn; separazione fra analisi e impaginazione | Slide 15, appendice al report, lockfile |
| Due strumenti di visualizzazione non dimostrati | Matplotlib per le figure statiche; nuova analisi interattiva Plotly con tre grafici reali | Slide 15, `scripts/reproduce_published.py`, HTML autonomo |
| Repository non indicato | URL leggibile e cliccabile, repository pubblico verificato | Slide 16, conclusione, README |
| Riproducibilità troppo generica | Percorso senza API dagli aggregati pubblicati, controlli sui risultati e percorso separato di raccolta live | Slide 16, `docs/reproduction.md` |
| Licenza non esplicita | MIT per il codice; CC BY 4.0 per presentazione e testi originali, come scelto dall'autore | LICENSE, NOTICE, slide 16–17 |
| Proprietà dei dati | Esclusione esplicita dei dati dei provider dalle licenze del progetto | NOTICE, slide 16 |
| Precisione statistica | Intervallo al giorno 30, definizione di S(t), dipendenza intra-pool e limiti delle osservazioni | Slide 14 e companion |
| Accessibilità | Intervalli e valori nel tooltip, etichette oltre al colore, tabelle HTML alternative ai grafici | Companion interattivo |
| Preparazione alla discussione | Dimostrazione pratica e domande metodologiche con risposte precise | `docs/oral_defense_revision.md` |

## Correzioni delle rappresentazioni

- Slide 6: curva Kaplan–Meier a gradini con banda puntuale al 95% e dettaglio della coda.
- Slide 9–10: assi temporali numerici con tutti i giorni osservati, eliminando le distanze
  artificialmente uguali tra -7, 0, +7 e +30 giorni. Titolo dello studio eventi reso descrittivo.
- Slide 12: nota finale accorciata per evitare il testo troppo vicino al bordo.

## Migliorie metodologiche ulteriori

- S(30) = 6,2247%, con intervallo puntuale al 95% 5,3434–7,1938%. La curva indica
  la probabilità stimata di durare **oltre** t giorni, non la probabilità di rendimento futuro.
- L'intervallo di lifelines assume episodi indipendenti. Episodi ripetuti nello stesso pool
  possono essere dipendenti: non presentarlo come intervallo corretto per clustering.
- Se un pool entra nel pannello già sopra soglia, l'inizio reale dell'episodio può precedere
  l'osservazione. I grandi vuoti interrompono un episodio osservato, senza dimostrare una
  cessazione economica. La sensibilità ai gap non risolve da sola questa limitazione.
- I controlli a 90 e 180 giorni operano su pool già selezionati con almeno 180 osservazioni
  del provider. Non ricostituiscono l'universo dei pool esclusi inizialmente.
- Le 2.669, 2.657 e 2.612 comparazioni del churn contano coppie data × top-k valide, non
  pool indipendenti. Il valore principale pesa ogni confronto, non ogni cella allo stesso modo.
- Il confronto temporale APY/TVL non identifica causalità. Anche il cambio di composizione
  dei pool disponibili può modificare le mediane nei vari giorni dell'event study.

## Cosa consegnare

Consegnare soltanto `outputs/submission/Simone_Ragusini_945119.pdf`.
Il PDF mantiene 17 pagine e l'analisi estesa: i vincoli di numero di slide del
modello non sono applicati, secondo le istruzioni dell'autore. Il riferimento
prioritario è il feedback ricevuto, insieme alle linee guida sulla consegna PDF
asincrona. La pagina 7 contiene il grafico Plotly esportato, mentre le pagine
6, 9 e 10 contengono grafici Matplotlib. La pagina 15 documenta i due strumenti.
Il docente non deve aprire un HTML né assistere a una demo per leggere i risultati.
Report, PowerPoint, HTML, ZIP e guida orale sono materiali di supporto e non
ulteriori file da caricare per la consegna. Il repository è una risorsa collegata
per verificare il codice, come richiesto dal feedback.

La voce “Draft share before the exam: No” descrive una procedura già avvenuta.
Non è un dato da correggere retroattivamente. L'eventuale invio del nuovo materiale
al docente e il rispetto delle scadenze restano azioni dell'autore.
