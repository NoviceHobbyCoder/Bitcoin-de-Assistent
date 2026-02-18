# Bitcoin-de-Assistent

GUI Assistant for Bitcoin.de trading via API.

# vor der installation:
- Die Doku auf bitcoin.de über die API und die geringeren Gebühren lesen.
- Die install Anleitung lesen.
- Maria db installieren.
# nach der Installation:
- Die Programm Anleitung lesen.
- BUY-Order stehen rechts, SELL-Order stehen links (wie bei bitcoin.de).
- bitte nicht mit der Botfunktion übertreiben!
# ich würde mich sehr über ein kleines Dankeschön freuen:
# BTC 17GzEJaFHgif8q3FQK27ZoMzLrV87oib7F

## Features
- Live Orderbook
- Websocket tools
- Analysis tools
- Ledger tools
- Local database
- Local Credentials
- nichts geht raus, alles läuft über API Anfragen
## License
GNU GPLv3

# Tipps
- Analyse-server und Orderbuch-server sollten auf einem extra System laufen damit alle Daten 24/7 gesammelt werden (Orderbuch-syncron).
- Auf dem gleichen System muss Maria db installiert sein.
- es geht auf Raspberry aber kann je nach Model zu Ram swap kommen und einzelne Order werden nicht im Orderbuch angezeigt oder nicht rechtzeitig entfernt.
- Es ist möglich Hauptprogramm und Server tools auf ein und dem selben System zu betreiben (ideal zum ausprobieren, wenn syncronität noch nicht wichtig ist).
- Für Linux einfach die die Skripte laufen lassen oder selbst Kompilieren.
- Hauptanwendung mit main.py starten
- wenn API Schlüssel gespeichert sind kann es beim Starten der Hauptanwendung ein paar sekunden dauern, weil alle informationen von bitcoin.de per API geladen werden.
