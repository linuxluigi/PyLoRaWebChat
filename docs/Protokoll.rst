Protokoll
=========

Funk Richtlinien
----------------

+----------------------------+-----------+
| Feld                       | Wert      |
+----------------------------+-----------+
| Trägerfrequenz             | 433000000 |
+----------------------------+-----------+
| Leistung                   | 20        |
+----------------------------+-----------+
| Bandbreite                 | 6         |
+----------------------------+-----------+
| Spreizfaktor               | 10        |
+----------------------------+-----------+
| Fehlerkorrekturcode        | 1         |
+----------------------------+-----------+
| CRC- Prüfung               | 1         |
+----------------------------+-----------+
| impliziter Header          | 0         |
+----------------------------+-----------+
| einmaliger Empfang         | 0         |
+----------------------------+-----------+
| Frequenzmodulation         | 0         |
+----------------------------+-----------+
| Frequenzmodulationsperiode | 0         |
+----------------------------+-----------+
| Empfangszeitlimitzeit      | 3000      |
+----------------------------+-----------+
| Benutzerdatenlänge         | 8         |
+----------------------------+-----------+
| Präambellänge              | 4         |
+----------------------------+-----------+


``HIMO-01P`` Befehl zur Gerät Konfiguration::

    AT+CFG=433000000,20,6,10,1,1,0,0,0,0,3000,8,4

Gerät Adresse
--------------

Jeder Node erhält eine eigene Adresse, die Adresse ist auf jedes ``HIMO-01P`` Modul aufgeklept.

``HIMO-01P`` Befehl zur Adressen eingabe für Gerät ``10``::

    AT+ADDR=0010

Anwesenheit im Netzwerk senden
------------------------------

Jeder Netzwerk Teilnehmer (Node) soll alle 30 bis 60 Sekunden ein ``RTI`` zum Broadcast senden. Um dauerhafte Kollisionen
zu vermeiden, soll das ``RTI`` jede Übertragung in unregelmäßigen Abständen gesendet werden.

``RTI`` steht hierbei für Routing Table Information. Der Befehl für das ``HIMO-01P`` Modul ist::

    AT+DEST=FFFF
    AT+SEND=3
    RTI

Jeder Teilnehmer erhält nun ``LR,0010,03,RTI``:

- ``LR`` Nachrichten eingang
- ``0010`` Adresse des Absenders, absender Adresse ist immer 4 Stellen groß
- ``03`` Länge der Nachricht
- ``RTI`` RTI Nachricht

Jeder Teilnehmer kann nun neue Nodes im Netzwerk finden und diese zu ihrer eigenen Routing Information Table hinzufügen.

Nachricht an anderen Node senden & empfangen
--------------------------------------------

Die maximale Nachrichten Länge beträgt 250 Zeichen, diese muss den ``HIMO-01P`` Modul vor dem Senden mitgeteil werden,
sowie die Ziel Adresse. Der Befehl zum senden der Nachricht ``Hallo``, welche ``5`` Zeichen lang ist, an der Adresse
``0001`` von dem Absender ``0010`` ist::

    AT+DEST=0001
    AT+SEND=5
    Hallo

Der Empfänger erhält dadurch ``LR,0010,05,Hallo``:

- ``LR`` Nachrichten eingang
- ``0010`` Adresse des Absenders, absender Adresse ist immer 4 Stellen groß
- ``05`` Länge der Nachricht
- ``Hallo`` Nachricht

