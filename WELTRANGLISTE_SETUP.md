# FROSTY – weltweite Rangliste einrichten

FROSTY läuft weiterhin als statisches Spiel auf GitHub Pages. Für eine **echte öffentliche Weltrangliste** müssen Namen und Rekorde zusätzlich in einer zentralen Datenbank gespeichert werden. Das ist mit den in diesem Repository enthaltenen Supabase-Dateien vorbereitet; die Verbindung ist **nicht** bereits aktiv.

## Einmalige Einrichtung (Supabase)

1. Supabase-Projekt anlegen bzw. mit dem Supabase-Plugin verbinden.
2. SQL aus `supabase/migrations/20261112000000_frosty_leaderboard.sql` im Projekt ausführen, um die Tabelle für Spieler und Rekorde zu erstellen.
3. Die Edge Function in `supabase/functions/frosty-leaderboard/index.ts` deployen. Die Datei `supabase/config.toml` setzt `verify_jwt = false`, da Spieler ein eigenes zufällig erzeugtes Geheimnis erhalten. Der Datenbank-Schlüssel bleibt **ausschließlich auf dem Server**.
4. In `assets/leaderboard-config.js` die Funktion-URL eintragen, z. B.:

   ```js
   window.FROSTY_LEADERBOARD_API = 'https://DEIN-PROJEKT.supabase.co/functions/v1/frosty-leaderboard';
   ```

5. Die Änderung zu GitHub pushen. Die Weltrangliste erscheint dann bei allen Spielern und aktualisiert sich bei jedem Aufruf.

Bei einer CLI-basierten Einrichtung: `supabase link --project-ref PROJEKT-ID`, `supabase db push` und `supabase functions deploy frosty-leaderboard --no-verify-jwt`.

## Vorhandene Funktionen

- Bei der ersten Runde wird ein Spielername abgefragt und lokal gespeichert.
- Ein zufälliger 48-stelliger Browser-Schlüssel schützt den Namen vor versehentlicher Übernahme. Die Datenbank speichert nur seinen SHA-256-Hash.
- Spielername ist eindeutig (ohne Unterscheidung zwischen Groß- und Kleinschreibung). Derselbe Spieler kann seinen Namen später ändern.
- Nur der persönliche Bestwert eines Spielers wird veröffentlicht.
- Die 50 höchsten Rekorde werden öffentlich sortiert angezeigt.
- Das Admin-/Datenbank-Geheimnis wird nie an den Browser ausgeliefert.
- Vor Einrichtung der Datenbank zeigt das Spiel **ausdrücklich**, dass die Weltrangliste noch nicht online ist; es zeigt keine fiktiven Spieler.

## Fairness und Grenzen

Wie bei jedem rein clientseitigen Spiel können technisch versierte Spieler Werte manipulieren. Die Server-Funktion prüft Zahlenbereiche, fordert einen Spieler-Schlüssel an und begrenzt zu häufige Einreichungen, ist aber **kein vollständiger Anti-Cheat**. Für ein wettbewerbsorientiertes Ranking sind signierte Spielsitzungen und serverseitige Plausibilitätsprüfungen ein möglicher weiterer Schritt.

## API

- `GET /functions/v1/frosty-leaderboard`: `{entries:[{name,score}],total}`
- `POST` `{action:"register",name,token}`: `{ok:true,name}`
- `POST` `{action:"score",token,score}`: `{ok:true,best}`

Erlaubte Browser-Herkunft: `https://oyamakuro.github.io`; Entwickler-Lokalhost ist ebenfalls erlaubt.
