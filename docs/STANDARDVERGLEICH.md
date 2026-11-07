# Standardvergleich und Vollständigkeitsprüfung

**Tarifstichtag:** 2026-11-04 · **Quellenprüfung:** 7. November 2026

Profil: 24 Monate altes Einzelkind, kommunale Betreuung, höchster regulärer Einkommenstarif, ohne Pass- oder Sozialermäßigung; Montag bis Freitag jeweils mindestens acht Stunden durchgehend.

Der Vergleichswert ist der am Stichtag geltende Monatsbeitrag × Beitragsmonate ÷ 12. Das Jahresäquivalent hält diesen Tarif konstant und bildet keine tatsächliche Jahresabrechnung mit unterjährigen Änderungen ab. Die Kennzahl enthält Betreuung; Zusatzkosten stehen separat im JSON-Export. Ein veröffentlichtes Angebot garantiert keinen freien Platz.

| Kommune | Gewähltes Paket | Wochenstunden | Mehrstunden | Monatsbeitrag | Beitragsmonate | Monatsäquivalent | Status |
|---|---|---:|---:|---:|---:|---:|---|
| Böblingen | bis 40 Std./Woche | 40 | 0 | 310,00 € | 12 | 310,00 € | vergleichbar |
| Ditzingen | GT 45 Std./Woche | 45 | 5 | 636,00 € | 12 | 636,00 € | vergleichbar |
| Esslingen am Neckar | Ganztag 40 Std./Woche | 40 | 0 | 1.170,00 € | 12 | 1.170,00 € | vergleichbar |
| Fellbach | GT 45 Std., Mo–Do 9,25 Std./Fr 8 Std. | 45 | 5 | 702,00 € | 12 | 702,00 € | vergleichbar |
| Gerlingen | Ganztag, 7:30–16:00 Uhr | 42,5 | 2,5 | 640,00 € | 12 | 640,00 € | vergleichbar |
| Korntal-Münchingen | Krippe 40 Std./Woche | 40 | 0 | 398,75 € | 11 | 365,52 € | vergleichbar |
| Kornwestheim | GT U3, 9 Std./Tag, 5 Tage | 45 | 5 | 436,00 € | 11 | 399,67 € | vergleichbar |
| Leinfelden-Echterdingen | GT bis 40 Std. | 40 | 0 | 587,20 € | 11 | 538,27 € | vergleichbar |
| Leonberg | verkürzte Krippe 8,5 Std. | 42,5 | 2,5 | 537,00 € | 12 | 537,00 € | vergleichbar |
| Ludwigsburg | GT8, 8 Std. durchgehend | 40 | 0 | 499,00 € | 11 | 457,42 € | vergleichbar |
| Sindelfingen | GT8 | 40 | 0 | 331,80 € | 12 | 331,80 € | vergleichbar |
| Stuttgart | GT, 8 Std./Tag | 40 | 0 | 243,00 € | 11 | 222,75 € | vergleichbar |

## Vollständigkeit der strukturierten Übertragung

Die Zahlen beziehen sich auf gespeicherte Tarifzellen und Angebotsdefinitionen einschließlich ausdrücklich nicht angebotener oder nicht bepreister Varianten mit eigenem Status. Formelbasierte Angebote haben keine künstlich vervielfältigten Preiszeilen. Unklare Regeln bleiben mit Originalquelle dokumentiert. Vollständigkeit des Quellenarchivs bedeutet nicht, dass jede Sonderregel automatisch ausführbar ist.

| Kommune | Angebote | Tarifzellen | Einkommensstufen | Kostenbausteine | Regelstatus |
|---|---:|---:|---:|---:|---|
| Böblingen | 16 | 64 | 0 | 2 | Unterstützte Berechnung plus archivierter Satzungstext |
| Ditzingen | 16 | 136 | 4 | 16 | Unterstützte Berechnung plus archivierter Satzungstext |
| Esslingen am Neckar | 8 | 128 | 10 | 802 | Unterstützte Berechnung plus archivierter Satzungstext |
| Fellbach | 14 | 0 | 0 | 1 | Unterstützte Berechnung plus archivierter Satzungstext |
| Gerlingen | 6 | 24 | 0 | 2 | Unterstützte Berechnung plus archivierter Satzungstext |
| Korntal-Münchingen | 9 | 252 | 7 | 2 | Unterstützte Berechnung plus archivierter Satzungstext |
| Kornwestheim | 12 | 42 | 0 | 2 | Unterstützte Berechnung plus archivierter Satzungstext |
| Leinfelden-Echterdingen | 10 | 148 | 0 | 54 | Unterstützte Berechnung plus archivierter Satzungstext |
| Leonberg | 24 | 96 | 0 | 5 | Unterstützte Berechnung plus archivierter Satzungstext |
| Ludwigsburg | 14 | 44 | 0 | 2 | Unterstützte Berechnung plus archivierter Satzungstext |
| Sindelfingen | 12 | 240 | 0 | 2 | Unterstützte Berechnung plus archivierter Satzungstext |
| Stuttgart | 10 | 80 | 0 | 1 | Unterstützte Berechnung plus archivierter Satzungstext |

## Einschränkungen und Quellenhinweise

- Ein numerischer Wert von `0` bedeutet ausdrücklich gebührenfrei; fehlende oder unklare Werte sind `null` im JSON und haben einen eigenen Status.
- Bruttoeinkommen, zu versteuerndes Einkommen und kommunale Einkommensdefinitionen bleiben getrennt. Es gibt keine geschätzte steuerliche Umrechnung.
- Nicht belegte tägliche Verteilungen werden nicht aus Wochenstunden abgeleitet. Das betrifft weiterhin einzelne alternative Stundenmodelle.
- Mahlzeitenpreise werden nur mit bekannten Beitragsmonaten bzw. ausdrücklich eingegebenen Essenstagen umgerechnet. Einrichtungsabhängige Preise bleiben Varianten.
- Passbesitz und Bewilligungsvoraussetzungen müssen für ermäßigte Profile ausdrücklich bestätigt werden. Sonderfälle wie Eingewöhnung, Abwesenheit, Härtefallentscheidungen und anteilige Aufnahmemonate sind im Quellenarchiv erhalten und werden nicht in den regulären Referenzwert eingerechnet.
- Bei FamilienCard-Profilen mit mehreren U3-Kindern bleibt die Verteilung des einmaligen Kleinkindzuschlags offen; die Berechnung verlangt dafür eine gesonderte Klärung.

### Böblingen

- [Originalquelle d1f83ab397ca](https://www.boeblingen.de/site/Boeblingen-Internet/get/params_E-1808561047/25368744/460.1331%20-%20Geb%C3%BChrenverzeichnis%20ab%2001.09.2026%20-%20Anlage%20%28neue%20Schriftart%29.pdf): PDF Seite 1, bis 40 Std./Woche, u3
- [Originalquelle d1f83ab397ca](https://www.boeblingen.de/site/Boeblingen-Internet/get/params_E-1808561047/25368744/460.1331%20-%20Geb%C3%BChrenverzeichnis%20ab%2001.09.2026%20-%20Anlage%20%28neue%20Schriftart%29.pdf): PDF Seite 1, bis 40 Std./Woche, u3
- [Originalquelle 4b99e2929828](https://www.boeblingen.de/site/Boeblingen-Internet/get/params_E-1401717129/24731773/Satzung%20%C3%BCber%20die%20Benutzung%20der%20st%C3%A4dtischen%20Kindertageseinrichtungen%20der%20Stadt%20B%C3%B6blingen,%20g%C3%BCltig%20ab%2001.01.2026.pdf): §§ 14,16: ganzjährig monatlich, auch Ferien; nur Essen im August ausgenommen
- [Originalquelle 6d67ccd75002](https://www.boeblingen.de/site/Boeblingen-Internet/get/params_E1557862559/24731764/Prospekt%20105x210%20Kita%20Betreuungsangebote%20Bo%CC%88blingen.pdf): PDF Seite 1: Betreuungsformen; Seite 2: städtische Angebote

### Ditzingen

- `income_interval_gaps`: Die wörtlichen Einkommensgrenzen lassen einzelne Grenz-/Centwerte offen. Dafür wird keine Gebührenstufe geraten.
- `unpriced_gt50_2027`: Die 2027-Anlagen führen keinen GT50-Preis auf. Daraus wird weder eine Abschaffung noch die gesicherte Fortgeltung des 2026-Betrags abgeleitet.
- [Originalquelle e3a01305341e](https://www.ditzingen.de/fileadmin/Dateien/Cross7/Startseite/Service_%26_Rathaus/Ortsrecht/4.02_Gebuhrensatzung_fur_die_stadtischen_Kindertageseinrichtungen.pdf): PDF Seite 11, GT 45 Std./Woche, u3
- [Originalquelle e3a01305341e](https://www.ditzingen.de/fileadmin/Dateien/Cross7/Startseite/Service_%26_Rathaus/Ortsrecht/4.02_Gebuhrensatzung_fur_die_stadtischen_Kindertageseinrichtungen.pdf): PDF Seite 11, GT 45 Std./Woche, u3
- [Originalquelle e3a01305341e](https://www.ditzingen.de/fileadmin/Dateien/Cross7/Startseite/Service_%26_Rathaus/Ortsrecht/4.02_Gebuhrensatzung_fur_die_stadtischen_Kindertageseinrichtungen.pdf): §3 Abs. 3 und §5: monatliche Erhebung auch ohne tatsächlichen Besuch, keine Ferienausnahme
- [Originalquelle e3a01305341e](https://www.ditzingen.de/fileadmin/Dateien/Cross7/Startseite/Service_%26_Rathaus/Ortsrecht/4.02_Gebuhrensatzung_fur_die_stadtischen_Kindertageseinrichtungen.pdf): Gebührentabelle

### Esslingen am Neckar

- [Originalquelle 55d9e28a62d7](https://www.esslingen.de/site/Esslingen_Layout_2022/get/params_E879676739_Dattachment/24947481/Entgelte%20Ganztagsbetreuung%20ab%2001.03.2026%20Gesamt.pdf): PDF Seite 1, Ganztag 40 Std./Woche, u3
- [Originalquelle 55d9e28a62d7](https://www.esslingen.de/site/Esslingen_Layout_2022/get/params_E879676739_Dattachment/24947481/Entgelte%20Ganztagsbetreuung%20ab%2001.03.2026%20Gesamt.pdf): PDF Seite 1, Ganztag 40 Std./Woche, u3
- [Originalquelle 4d33c02682ef](https://www.esslingen.de/%2CLde/leben-und-lernen/familie-und-bildung/kinderbetreuung/entgeltordnung-gt): III. Entstehen und Fälligkeit: zwölf Monate
- [Originalquelle 55d9e28a62d7](https://www.esslingen.de/site/Esslingen_Layout_2022/get/params_E879676739_Dattachment/24947481/Entgelte%20Ganztagsbetreuung%20ab%2001.03.2026%20Gesamt.pdf): Gebührentabelle

### Fellbach

- `no_uniform_40h_daily_schedule`: Fellbachs belegtes 40-Stunden-Modell hat donnerstags/freitags nur sieben Stunden. Das kleinste geprüfte Paket für acht Stunden an jedem Tag umfasst 45 Stunden (9,25/9,25/9,25/9,25/8). Die Stadt rechnet mit den angebotenen Öffnungsstunden.
- [Originalquelle 772cfcc5d07d](https://www.fellbach.de/ceasy/resource/?download=1&id=1414): PDF Seite 3, §§2–4: Tarif je angebotener Wochenstunde, Familienstaffel und Mindestgebühr
- [Originalquelle 772cfcc5d07d](https://www.fellbach.de/ceasy/resource/?download=1&id=1414): PDF Seite 3, §§2–4: Tarif je angebotener Wochenstunde, Familienstaffel und Mindestgebühr
- [Originalquelle 772cfcc5d07d](https://www.fellbach.de/ceasy/resource/?download=1&id=1414): §2 Abs. 1, §6 Abs. 1 und §7 Abs. 3: monatliche Betreuung auch in Ferien; elf Monate gelten separat nur fürs Essen nach §5
- [Originalquelle e0f7ae696e98](https://www.fellbach.de/ceasy/serve/usage/main.php?view=publish&item=nursery&id=1008): Öffnungszeiten und Altersgruppen auf der städtischen Angebotsseite

### Gerlingen

- `older_u3_price_date`: Die aktuelle Gerlinger Satzung führt weiterhin die U3-Tabelle mit Preisstand September 2025.
- [Originalquelle f9eb066f5901](https://www.gerlingen.de/site/Gerlingen-Internet-2021/get/params_E621822343/25429607/Kindertagesst%C3%A4tten%20-%20Benutzungsgeb%C3%BChren%20ab%2001.09.2026_barrierefrei%20-%20freigegeben%20-%2003.07.2026.pdf): PDF Seite 6, Ganztag, 7:30–16:00 Uhr, u3
- [Originalquelle f9eb066f5901](https://www.gerlingen.de/site/Gerlingen-Internet-2021/get/params_E621822343/25429607/Kindertagesst%C3%A4tten%20-%20Benutzungsgeb%C3%BChren%20ab%2001.09.2026_barrierefrei%20-%20freigegeben%20-%2003.07.2026.pdf): PDF Seite 6, Ganztag, 7:30–16:00 Uhr, u3
- [Originalquelle f9eb066f5901](https://www.gerlingen.de/site/Gerlingen-Internet-2021/get/params_E621822343/25429607/Kindertagesst%C3%A4tten%20-%20Benutzungsgeb%C3%BChren%20ab%2001.09.2026_barrierefrei%20-%20freigegeben%20-%2003.07.2026.pdf): PDF Seite 6, Gebührenverzeichnis: zwölf Monate pro Jahr
- [Originalquelle f9eb066f5901](https://www.gerlingen.de/site/Gerlingen-Internet-2021/get/params_E621822343/25429607/Kindertagesst%C3%A4tten%20-%20Benutzungsgeb%C3%BChren%20ab%2001.09.2026_barrierefrei%20-%20freigegeben%20-%2003.07.2026.pdf): Gebührentabelle

### Korntal-Münchingen

- `income_interval_gaps`: Die wörtlichen Einkommensgrenzen lassen einzelne Grenz-/Centwerte offen. Dafür wird keine Gebührenstufe geraten.
- [Originalquelle e534e1399550](https://www.korntal-muenchingen.de/ceasy/serve/usage/main.php?id=1111&item=statute&view=publish): PDF Seite 8, Anlage 1, 2.7
- [Originalquelle e534e1399550](https://www.korntal-muenchingen.de/ceasy/serve/usage/main.php?id=1111&item=statute&view=publish): PDF Seite 8, Anlage 1, 2.7
- [Originalquelle e534e1399550](https://www.korntal-muenchingen.de/ceasy/serve/usage/main.php?id=1111&item=statute&view=publish): PDF Seite 7, Anlage 1 Ziff. 1: elf Monatsbeiträge, August frei
- [Originalquelle d9080549f5ae](https://www.korntal-muenchingen.de/de/Leben-Lernen/Kindertageseinrichtungnen/Alle-KITAs/Kindertageseinrichtungen?view=publish&item=nursery&id=1009): Öffnungszeiten: Montag bis Freitag 7:30–13:30 oder 7:00–15:00 Uhr

### Kornwestheim

- [Originalquelle ecb1d09b1939](https://www.kornwestheim.de/site/Kornwestheim_Internet/get/params_E-1204246672/25201515/Satzung%20mit%20Geb%C3%BChren%20ab%201.9.2026.pdf): PDF Seite 6, GT U3, 9 Std./Tag, 5 Tage, u3
- [Originalquelle ecb1d09b1939](https://www.kornwestheim.de/site/Kornwestheim_Internet/get/params_E-1204246672/25201515/Satzung%20mit%20Geb%C3%BChren%20ab%201.9.2026.pdf): PDF Seite 6, GT U3, 9 Std./Tag, 5 Tage, u3
- [Originalquelle ecb1d09b1939](https://www.kornwestheim.de/site/Kornwestheim_Internet/get/params_E-1204246672/25201515/Satzung%20mit%20Geb%C3%BChren%20ab%201.9.2026.pdf): PDF Seite 2, §3 Abs. 2: elf Monate, August gebührenfrei
- [Originalquelle ecb1d09b1939](https://www.kornwestheim.de/site/Kornwestheim_Internet/get/params_E-1204246672/25201515/Satzung%20mit%20Geb%C3%BChren%20ab%201.9.2026.pdf): Gebührentabelle

### Leinfelden-Echterdingen

- `adult_child_application`: Die Berücksichtigung kindergeldberechtigter volljähriger Kinder in Leinfelden-Echterdingen erfordert einen Antrag; das persönliche Profil muss die genehmigte Haushaltskonstellation wiedergeben.
- `published_pass_rounding`: Die veröffentlichten Stadtpassbeträge haben Vorrang vor der Prozentrechnung; die Quelle weist gerundete Beträge aus.
- [Originalquelle 3edbd30ca2f4](https://www.leinfelden-echterdingen.de/site/Leinfelden-Echterdingen-Internet/get/documents_E-476817934/leinfelden-echterdingen/Datenquelle_LE/stadtrecht/Stadtrecht-4_1_2.pdf): PDF Seite 6, GT bis 40 Std., u3
- [Originalquelle 3edbd30ca2f4](https://www.leinfelden-echterdingen.de/site/Leinfelden-Echterdingen-Internet/get/documents_E-476817934/leinfelden-echterdingen/Datenquelle_LE/stadtrecht/Stadtrecht-4_1_2.pdf): PDF Seite 6, GT bis 40 Std., u3
- [Originalquelle 3edbd30ca2f4](https://www.leinfelden-echterdingen.de/site/Leinfelden-Echterdingen-Internet/get/documents_E-476817934/leinfelden-echterdingen/Datenquelle_LE/stadtrecht/Stadtrecht-4_1_2.pdf): PDF Seite 2, Ziff. 3.4: September bis Juli, elf Monate
- [Originalquelle 03bd8c4fc8b1](https://www.leinfelden-echterdingen.de/site/Leinfelden-Echterdingen-Internet/get/params_E920696249/25379400/Stadtrecht-4_1_2.pdf): PDF Seite 6: Wochenpakete mit Endzeiten 13/14/15/16/17 Uhr, Frühdienst vor 8 Uhr

### Leonberg

- [Originalquelle ca8ce11d0b8f](https://www.leonberg.de/PDF/Geb%C3%BChrentabelle_Kindertageseinrichtungen_g%C3%BCltig_ab_01_10_2026_.PDF?ObjSvrID=2691&ObjID=2369&ObjLa=1&Ext=PDF&WTR=1&_ts=1791804947): PDF Seite 1, verkürzte Krippe 8,5 Std., u3
- [Originalquelle ca8ce11d0b8f](https://www.leonberg.de/PDF/Geb%C3%BChrentabelle_Kindertageseinrichtungen_g%C3%BCltig_ab_01_10_2026_.PDF?ObjSvrID=2691&ObjID=2369&ObjLa=1&Ext=PDF&WTR=1&_ts=1791804947): PDF Seite 1, verkürzte Krippe 8,5 Std., u3
- [Originalquelle adc2c4902240](https://www.leonberg.de/output/download.php?fid=2691.7659.1.PDF): § 5 Ziff. 2: monatlich, auch während der Ferien
- [Originalquelle ca8ce11d0b8f](https://www.leonberg.de/PDF/Geb%C3%BChrentabelle_Kindertageseinrichtungen_g%C3%BCltig_ab_01_10_2026_.PDF?ObjSvrID=2691&ObjID=2369&ObjLa=1&Ext=PDF&WTR=1&_ts=1791804947): Gebührentabelle

### Ludwigsburg

- `unpriced_gt11`: GT11 ist definiert, aber in der Gebührenanlage nicht bepreist.
- [Originalquelle 29969ba83249](https://www.ludwigsburg.de/site/Ludwigsburg-Internet-2020/get/params_E-995498330/24269351/Stammsatzung_Kitageb%C3%BChren_2026_August_07.pdf): PDF Seite 6, GT8, 8 Std. durchgehend, u3
- [Originalquelle 29969ba83249](https://www.ludwigsburg.de/site/Ludwigsburg-Internet-2020/get/params_E-995498330/24269351/Stammsatzung_Kitageb%C3%BChren_2026_August_07.pdf): PDF Seite 6, GT8, 8 Std. durchgehend, u3
- [Originalquelle 29969ba83249](https://www.ludwigsburg.de/site/Ludwigsburg-Internet-2020/get/params_E-995498330/24269351/Stammsatzung_Kitageb%C3%BChren_2026_August_07.pdf): PDF Seite 2, §4 Abs. 1: elf Monate, August gebührenfrei
- [Originalquelle 29969ba83249](https://www.ludwigsburg.de/site/Ludwigsburg-Internet-2020/get/params_E-995498330/24269351/Stammsatzung_Kitageb%C3%BChren_2026_August_07.pdf): Gebührentabelle

### Sindelfingen

- [Originalquelle 8552e155f7fe](https://www.sindelfingen.de/fileadmin/Website/01_Sindelfingen/Dateien/Bildung_und_Betreuung/Kindertagesst%C3%A4tten/Satzung_Benutzung_st%C3%A4dtische_Betreuungsangebote_Kinder_neu.pdf): PDF Seite 13, GT8, u3
- [Originalquelle 8552e155f7fe](https://www.sindelfingen.de/fileadmin/Website/01_Sindelfingen/Dateien/Bildung_und_Betreuung/Kindertagesst%C3%A4tten/Satzung_Benutzung_st%C3%A4dtische_Betreuungsangebote_Kinder_neu.pdf): PDF Seite 13, GT8, u3
- [Originalquelle 8552e155f7fe](https://www.sindelfingen.de/fileadmin/Website/01_Sindelfingen/Dateien/Bildung_und_Betreuung/Kindertagesst%C3%A4tten/Satzung_Benutzung_st%C3%A4dtische_Betreuungsangebote_Kinder_neu.pdf): PDF Seite 10, §11: zwölf Monatsgebühren
- [Originalquelle 8552e155f7fe](https://www.sindelfingen.de/fileadmin/Website/01_Sindelfingen/Dateien/Bildung_und_Betreuung/Kindertagesst%C3%A4tten/Satzung_Benutzung_st%C3%A4dtische_Betreuungsangebote_Kinder_neu.pdf): Gebührentabelle

### Stuttgart

- [Originalquelle 535c7b4c86f8](https://www.stuttgart.de/medien/ibs/4-6-anlage-1-ab-01-08-2026.pdf): PDF Seite 1, GT, 8 Std./Tag, u3
- [Originalquelle 535c7b4c86f8](https://www.stuttgart.de/medien/ibs/4-6-anlage-1-ab-01-08-2026.pdf): PDF Seite 1, GT, 8 Std./Tag, u3
- [Originalquelle 535c7b4c86f8](https://www.stuttgart.de/medien/ibs/4-6-anlage-1-ab-01-08-2026.pdf): PDF Seite 1: elf Monatsbeiträge, August beitragsfrei
- [Originalquelle 535c7b4c86f8](https://www.stuttgart.de/medien/ibs/4-6-anlage-1-ab-01-08-2026.pdf): Gebührentabelle

