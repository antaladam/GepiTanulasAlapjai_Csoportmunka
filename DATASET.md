# A SUPPORT2 adatkészlet: leírás és előfeldolgozás

Ez a dokumentum bemutatja a projektben használt adatkészletet és annak minden eredeti oszlopát.
Leírja, mely oszlopok lettek megtartva jellemzőként, a többi miért lett kizárva, és pontosan hogyan készültek a modellek bemeneti fájljai. Mindez a `scripts/prepare_data.py` szkriptben van megvalósítva; az alábbi számok a szkript futtatásából származnak.

A CSV-fájlokban és a kódban a tizedesjel pont.

A fájlok előállítása:

```
pip install -r requirements.txt
python scripts/download_data.py
python scripts/prepare_data.py
```

## 1. Forrás

- **Adatkészlet:** SUPPORT2, UCI Machine Learning Repository, azonosító: 880
  (<https://archive.ics.uci.edu/dataset/880/support2>), DOI: 10.3886/ICPSR02957.v2.
- **Készítő:** Frank Harrell. A változók leírását tartalmazó dokumentáció:
  <https://hbiostat.org/data/repo/csupport2>.
- **Vizsgálat:** SUPPORT (Study to Understand Prognoses and Preferences for Outcomes and Risks of Treatments). Súlyos állapotú, kórházban kezelt felnőtt betegek 5 amerikai egészségügyi központból. 
                 Az I. fázis (1989–1991) prospektív megfigyeléses vizsgálat volt, a II. fázis (1992–1994) egy ápolók által vezetett beavatkozás kontrollált vizsgálata. 
				 Az adatok kórlapokból, interjúkból, kérdőívekből és az amerikai Nemzeti Halálozási Indexből (National Death Index) származnak.
- **Bemutató cikk:** The SUPPORT Principal Investigators, *JAMA* 1995;274(20):1591–1598.
- **Licenc:** a UCI az eredeti forrásra hivatkozik; az adatkészletet a hbiostat.org oldalon leírt módon kell feltüntetni és hivatkozni.
- **Méret:** 9 105 beteg (sor), 48 oszlop. A `scripts/download_data.py` SHA-256 ellenőrzőösszeggel ellenőrzi, hogy mindenki pontosan ugyanazt a fájlt használja.

A UCI metaadatai szerint az adatkészletben nincs hiányzó érték, valójában azonban sok van; az oszloponkénti számok a 3. fejezetben szerepelnek.

## 2. Feladat

**A kórházi halálozás bináris osztályozása:** a célváltozó a `hospdead` oszlop (1 = a kórházban meghalt, 0 = élve távozott). A 9 105 betegből 2 360 (25,9%) halt meg a kórházban.

A modell csak olyan információt használhat, amely a kórházi tartózkodás elején már ismert. A vizsgálat a legtöbb klinikai értéket **a vizsgálatba lépés utáni 3. napon** méri, ahogy a dokumentáció megnevezései is jelzik („Day 3”, „D3”). 
Az eredeti SUPPORT prognosztikai modell ezeket a 3. napi értékeket használta kiinduló prediktorként, és ez a projekt is így tesz.

## 3. Az összes oszlop és a döntés mindegyikről

A leírások Harrell dokumentációját követik. A „Hiányzó” oszlop a nyers fájl mind a 9 105 betegére vonatkozik.

**A döntések jelentése**

| Döntés | Jelentés |
|---|---|
| **Célváltozó** | Az előrejelzendő érték |
| **Azonosító** | A fájlokban megmarad a betegek azonosításához, de jellemzőként soha nem használjuk |
| **Jellemző** | A modell bemenete |
| **Kizárva: szivárgás** | A kimenetelből származik, használatukkal a modell „belelátna” a válaszba (adatszivárgás, angolul data leakage) |
| **Kizárva: redundáns / hiányos** | Nem szivárgás, de egy másik jellemzőt duplikál, vagy nagyrészt hiányzik |

| # | Oszlop | Leírás (a kódkönyv alapján) | Típus | Hiányzó | Döntés | Indoklás |
|---|---|---|---|---|---|---|
| 1 | `id` | Sorazonosító | egész | 0 | Azonosító | A sorszám semmit nem mond a betegről. Követheti a beválasztás sorrendjét (a vizsgálati fázist), ami hamis mintázatokat okozhat, és torzítaná a modelleket |
| 2 | `age` | Életkor (év) | numerikus | 0 | Jellemző | |
| 3 | `death` | Halálozás bármikor 1994. december 31-ig | 0/1 | 0 | Kizárva: szivárgás | Minden kórházi halálesetnél `death` = 1, így szinte tartalmazza a célváltozót |
| 4 | `sex` | Nem: female (nő), male (férfi) | kategória | 0 | Jellemző | |
| 5 | `hospdead` | Kórházi halálozás | 0/1 | 0 | **Célváltozó** | |
| 6 | `slos` | A vizsgálatba lépéstől a távozásig eltelt napok | numerikus | 0 | Kizárva: szivárgás | Csak a távozáskor vagy a halálkor ismert |
| 7 | `d.time` | A követés napjainak száma | numerikus | 0 | Kizárva: szivárgás | Kórházi halálesetnél pontosan egyenlő a vizsgálatba lépéstől a halálig eltelt napok számával |
| 8 | `dzgroup` | Betegség-alcsoport (8 csoport) | kategória | 0 | Jellemző | |
| 9 | `dzclass` | Betegségkategória (4 csoport) | kategória | 0 | Kizárva: redundáns | A `dzgroup` durvább csoportosítása; minden `dzgroup` érték pontosan egy `dzclass` értékhez tartozik |
| 10 | `num.co` | Társbetegségek száma | egész | 0 | Jellemző | |
| 11 | `edu` | Iskolai végzettség (évek száma) | numerikus | 1 634 (17,9%) | Jellemző | |
| 12 | `income` | Jövedelemsáv: under $11k, $11–$25k, $25–$50k, >$50k | rendezett kategória | 2 982 (32,8%) | Jellemző | |
| 13 | `scoma` | SUPPORT kómapontszám a Glasgow-skála alapján, 3. nap | numerikus | 1 | Jellemző | |
| 14 | `charges` | Kórházi díjak | numerikus | 172 (1,9%) | Kizárva: szivárgás | Csak a távozás után ismert; attól is függ, hogy a beteg meghalt-e és mikor |
| 15 | `totcst` | Teljes költség (RCC-módszerrel) | numerikus | 888 (9,8%) | Kizárva: szivárgás | Ugyanaz, mint a `charges` esetében |
| 16 | `totmcst` | Teljes mikroköltség | numerikus | 3 475 (38,2%) | Kizárva: szivárgás | Ugyanaz, mint a `charges` esetében |
| 17 | `avtisst` | Átlagos TISS (a kezelés intenzitását mérő pontszám), 3–25. nap | numerikus | 82 (0,9%) | Kizárva: szivárgás | A vizsgálatba lépés utáni napokra átlagolt érték; a korán meghaló betegeknél csak néhány nap számít bele, ezért irreális értéket adhat |
| 18 | `race` | Rassz: white, black, asian, hispanic, other | kategória | 42 (0,5%) | Jellemző | |
| 19 | `sps` | SUPPORT fiziológiai pontszám, 3. nap | numerikus | 1 | Jellemző | |
| 20 | `aps` | APACHE III fiziológiai pontszám (kóma nélkül), 3. nap | numerikus | 1 | Jellemző | |
| 21 | `surv2m` | A SUPPORT modell 2 hónapos túlélési előrejelzése a 3. napon | numerikus | 1 | Kizárva: szivárgás | Egy másik prognosztikai modell kimenete, amelyet a vizsgálat ugyanennek a betegcsoportnak az adataiból fejlesztett ki |
| 22 | `surv6m` | A SUPPORT modell 6 hónapos túlélési előrejelzése a 3. napon | numerikus | 1 | Kizárva: szivárgás | Ugyanaz, mint a `surv2m` esetében |
| 23 | `hday` | A kórházi tartózkodás hányadik napján lépett be a vizsgálatba | egész | 0 | Jellemző | |
| 24 | `diabetes` | Cukorbetegség (társbetegség) | 0/1 | 0 | Jellemző | |
| 25 | `dementia` | Demencia (társbetegség) | 0/1 | 0 | Jellemző | |
| 26 | `ca` | Daganat: no (nincs), yes (van), metastatic (áttétes) | kategória | 0 | Jellemző | |
| 27 | `prg2m` | Az orvos becslése a 2 hónapos túlélésre | numerikus | 1 649 (18,1%) | Kizárva: szivárgás | Egy orvos előrejelzése a kimenetelre, nem a betegen mért érték |
| 28 | `prg6m` | Az orvos becslése a 6 hónapos túlélésre | numerikus | 1 633 (17,9%) | Kizárva: szivárgás | Ugyanaz, mint a `prg2m` esetében |
| 29 | `dnr` | Újraélesztés mellőzésére vonatkozó (DNR) utasítás: nincs, a vizsgálatba lépés előtt, a vizsgálatba lépés után | kategória | 30 (0,3%) | Kizárva: szivárgás | A vizsgálatba lépés utáni utasítást gyakran akkor adják ki, amikor a beteg állapota súlyosan romlik |
| 30 | `dnrday` | A DNR utasításig eltelt napok (< 0: a vizsgálat előtt) | numerikus | 30 (0,3%) | Kizárva: szivárgás | Ugyanaz, mint a `dnr` esetében |
| 31 | `meanbp` | Artériás középnyomás, 3. nap | numerikus | 1 | Jellemző | |
| 32 | `wblc` | Fehérvérsejtszám (ezerben), 3. nap | numerikus | 212 (2,3%) | Jellemző | |
| 33 | `hrt` | Pulzusszám, 3. nap | numerikus | 1 | Jellemző | |
| 34 | `resp` | Légzésszám, 3. nap | numerikus | 1 | Jellemző | |
| 35 | `temp` | Testhőmérséklet (°C), 3. nap | numerikus | 1 | Jellemző | |
| 36 | `pafi` | PaO2/FiO2 arány, 3. nap | numerikus | 2 325 (25,5%) | Jellemző | |
| 37 | `alb` | Szérum albumin, 3. nap | numerikus | 3 372 (37,0%) | Jellemző | |
| 38 | `bili` | Bilirubin, 3. nap | numerikus | 2 601 (28,6%) | Jellemző | |
| 39 | `crea` | Szérum kreatinin, 3. nap | numerikus | 67 (0,7%) | Jellemző | |
| 40 | `sod` | Szérum nátrium, 3. nap | numerikus | 1 | Jellemző | |
| 41 | `ph` | Artériás vér pH-ja, 3. nap | numerikus | 2 284 (25,1%) | Jellemző | |
| 42 | `glucose` | Vércukor, 3. nap | numerikus | 4 500 (49,4%) | Jellemző | |
| 43 | `bun` | Vér karbamid-nitrogén (BUN), 3. nap | numerikus | 4 352 (47,8%) | Jellemző | |
| 44 | `urine` | Vizeletmennyiség, 3. nap | numerikus | 4 862 (53,4%) | Jellemző | |
| 45 | `adlp` | Mindennapi tevékenységek (ADL) indexe, a beteg válaszai alapján, 3. nap | numerikus | 5 641 (62,0%) | Kizárva: hiányos | A betegek 62%-ánál hiányzik. Ahol az `adls` hiányzik, ott az `adlsc` az `adlp`-ből kalibrált érték, így az `adlp` információja benne van az `adlsc`-ben |
| 46 | `adls` | Mindennapi tevékenységek (ADL) indexe, hozzátartozó válaszai alapján, 3. nap | numerikus | 2 867 (31,5%) | Kizárva: redundáns | Az `adlsc` ennek a vizsgálat által pótolt, hiánytalan változata: ahol az `adls` ismert, a két érték megegyezik |
| 47 | `sfdm2` | Funkcionális károsodás 2 hónap után (5 szint, ezek egyike „<2 mo. follow-up”) | kategória | 1 400 (15,4%) | Kizárva: szivárgás | 2 hónappal később mérik; a „<2 mo. follow-up” szinten lévő mind a 3 123 beteg 2 hónapon belül meghalt, így ez a szint gyakorlatilag a korai halálozást jelöli |
| 48 | `adlsc` | Pótolt ADL index, a hozzátartozói értékekhez kalibrálva | numerikus | 0 | Jellemző | |

**Összesítés:** 1 célváltozó, 1 azonosító, **29 jellemző** (25 numerikus, 4 kategorikus), 14 oszlop szivárgás miatt kizárva, 3 redundancia vagy hiányosság miatt kizárva.

Megjegyzések a megtartott jellemzőkhöz:

- Az `sps` és az `aps` összetett súlyossági pontszám, amelyek nagyrészt a 3. napi fiziológiai oszlopokból állnak össze, így átfednek velük. Azért maradnak benne, mert jogos, 3. napi mérések.
- A 3. napi időpont miatt a modell „a vizsgálat 3. napjától kezdve” jelez előre, nem a kórházi felvétel pillanatától. Ezt a beszámolóban korlátként említjük.

## 4. Rögzített tisztítási szabályok (minden betegre)

Az eredmény a `data/processed/support2_clean.csv` fájl (azonosító, célváltozó, 29 jellemző, a megmaradt hiányok üresen), amely az adatok bemutatására szolgál.

1. **Oszlopok kiválasztása:** a 3. fejezetben kizárt 17 oszlop eltávolításra kerül.
2. **Normál értékek a hiányzó laboreredmények helyére.** Az adatkészlet készítője azt javasolja, hogy ezeket a laborértékeket hiány esetén egy normál értékkel pótoljuk, mert a hiányzó vizsgálat általában azt jelenti, hogy nem kérték, mivel normál eredményt vártak (az értékek a UCI adatkészlet oldaláról származnak):

   | Oszlop | Kitöltő érték | Kitöltött betegek |
   |---|---|---|
   | `alb` | 3,5 | 3 372 |
   | `pafi` | 333,3 | 2 325 |
   | `bili` | 1,01 | 2 601 |
   | `crea` | 1,01 | 67 |
   | `bun` | 6,51 | 4 352 |
   | `wblc` | 9 | 212 |
   | `urine` | 2502 | 4 862 |

3. **A jövedelem mint rangszám.** A jövedelemsávok rendezettek, ezért számokra cserélhetők: under $11k → 0, $11–$25k → 1, $25–$50k → 2, >$50k → 3. A hiányzó jövedelem itt még hiányzó marad.

## 5. Tanító és teszt halmaz

- 75% tanító, 25% teszt, egyszeri felosztás a scikit-learn `train_test_split` függvényével.
- Mindkét halmazban a célváltozó ugyanolyan arányban szerepel
- Rögzített random seed: 42, így újrafuttatáskor a script ugyanazt az eredményt hozza létre.

| Rész | Betegek | Kórházban meghalt |
|---|---|---|
| Tanító | 6 828 | 25,9% |
| Teszt | 2 277 | 25,9% |

## 6. A megmaradt hiányok kitöltése

A 4. fejezet után 13 jellemzőben maradnak hiányok. Ezeket **kizárólag a tanító halmaz betegeiből számolt** értékkel töltjük ki, és ugyanezt az értéket használjuk a tanító és a teszt halmazban is, így a teszt betegek soha nem befolyásolják:

- numerikus jellemzők: a tanító betegek **mediánja**;
- `race`: a tanító betegek körében **leggyakoribb érték**.

| Oszlop | Hiányzó (tanító) | Hiányzó (teszt) | Kitöltő érték |
|---|---|---|---|
| `edu` | 1 237 | 397 | 12 (medián) |
| `income` | 2 231 | 751 | 1 (a rangszám mediánja, azaz $11–$25k) |
| `ph` | 1 731 | 553 | 7,42 (medián) |
| `glucose` | 3 371 | 1 129 | 135 (medián) |
| `race` | 33 | 9 | white (leggyakoribb) |
| `scoma`, `sps`, `aps`, `meanbp`, `hrt`, `resp`, `temp`, `sod` | oszloponként 1 (két beteg: az egyiknél a három pontszám, a másiknál az öt életjel hiányzik) | 0 | az adott oszlop mediánja |

Az egyetlen hiánnyal rendelkező oszlopok mediánjai: `scoma` 0, `sps` 23,90, `aps` 34, `meanbp` 78, `hrt` 100, `resp` 24, `temp` 36,70, `sod` 137.

## 7. A kategóriák kódolása

A négy szöveges jellemzőből 0/1 értékű oszlopok lesznek, kategóriánként egy: az oszlop értéke 1, ha a beteg az adott kategóriába tartozik, egyébként 0. Ezt a `pandas.get_dummies` függvény végzi.

| Jellemző | Új oszlopok | Darab |
|---|---|---|
| `sex` | `sex_male` (1 = férfi, 0 = nő). Csak egy oszlop, mert a második csupán az ellentéte lenne | 1 |
| `dzgroup` | `dzgroup_ARF/MOSF w/Sepsis`, `dzgroup_CHF`, `dzgroup_COPD`, `dzgroup_Cirrhosis`, `dzgroup_Colon Cancer`, `dzgroup_Coma`, `dzgroup_Lung Cancer`, `dzgroup_MOSF w/Malig` | 8 |
| `race` | `race_asian`, `race_black`, `race_hispanic`, `race_other`, `race_white` | 5 |
| `ca` | `ca_metastatic`, `ca_no`, `ca_yes` | 3 |

A 25 numerikus jellemző változatlan marad, így **a 29 jellemzőből 42 oszlop lesz**.

## 8. Skálázás (standardizálás)

A numerikus jellemzők tartománya nagyon eltérő (például a `ph` 7,4 körüli, az `urine` ezres nagyságrendű). 
A távolság- és gradiensalapú modellek (logisztikus regresszió, kNN, SVM, neurális hálók) érzékenyek erre, ezért a skálázott fájlokban a 23 mért numerikus oszlopot standardizáljuk (a 0/1 értékű `diabetes` és `dementia` kivételével):

```
skálázott érték = (érték − tanító átlag) / tanító szórás
```

Az átlagot és a szórást **kizárólag a tanító betegekből**, a hiányok kitöltése után számoljuk, és ugyanezeket az értékeket alkalmazzuk a teszt betegekre. 
A tanító oszlopok átlaga így pontosan 0, szórása pontosan 1; a teszt oszlopoké ehhez közeli, de nem pontosan ennyi. A 17 kategorizált oszlop, valamint a `diabetes` és a `dementia` 0/1 marad, ezeket nem skálázzuk. 

| Oszlop | Tanító átlag | Tanító szórás | | Oszlop | Tanító átlag | Tanító szórás |
|---|---|---|---|---|---|---|
| `age` | 62,74 | 15,61 | | `resp` | 23,30 | 9,49 |
| `num.co` | 1,87 | 1,34 | | `temp` | 37,10 | 1,25 |
| `edu` | 11,79 | 3,11 | | `pafi` | 263,19 | 103,26 |
| `income` | 0,95 | 0,85 | | `alb` | 3,15 | 0,76 |
| `scoma` | 12,22 | 24,73 | | `bili` | 2,11 | 4,56 |
| `sps` | 25,55 | 10,03 | | `crea` | 1,77 | 1,69 |
| `aps` | 37,56 | 19,89 | | `sod` | 137,59 | 6,02 |
| `hday` | 4,37 | 9,05 | | `ph` | 7,416 | 0,070 |
| `adlsc` | 1,89 | 2,02 | | `glucose` | 147,81 | 63,74 |
| `meanbp` | 84,72 | 27,54 | | `bun` | 19,93 | 23,30 |
| `wblc` | 12,33 | 9,31 | | `urine` | 2 360,96 | 1 003,14 |
| `hrt` | 97,05 | 31,06 | | | | |

A skálázatlan adatokat kezelni tudó modellek (pl. döntési fák) érdekében a skálázatlan adatok is elérhetőek.

## 9. Kimeneti fájlok

Mind a `data/processed/` mappában:

| Fájl | Betegek | Tartalom | Mire való |
|---|---|---|---|
| `support2_clean.csv` | 9 105 | azonosító, `hospdead`, 29 jellemző a 4. fejezet szerint; a megmaradt hiányok üresek, a kategóriák szövegként | Az adatok bemutatása (táblázatok, ábrák, hiányzó értékek) |
| `train.csv` | 6 828 | azonosító, `hospdead`, 42 jellemzőoszlop; hiányok kitöltve, one-hot kódolva, **nem skálázva** | Döntési fák, véletlen erdő, boosting |
| `test.csv` | 2 277 | ugyanaz, mint a `train.csv` | A modellek végső kiértékelésére |
| `train_scaled.csv` | 6 828 | ugyanaz, mint a `train.csv`, de a 23 mért numerikus oszlop **standardizálva** (a 0/1 oszlopok változatlanok) | Logisztikus regresszió, kNN, SVM, perceptron/MLP |
| `test_scaled.csv` | 2 277 | ugyanaz, mint a `train_scaled.csv` | A modellek végső kiértékelésére |

Minden modell számára a `hospdead` a célváltozó, jellemzőként pedig az `id` és a `hospdead` kivételével minden oszlop használandó.

## 10. Az előfeldolgozás korlátai

- **A normálértékkel való kitöltés sok azonos értéket hoz létre.** A kitöltés után a tanító betegek 48%-ánál `bun` = 6,51, 53%-ánál pedig `urine` = 2502, így ezek az oszlopok részben azt jelzik, hogy „a vizsgálatot nem végezték el”. 
- **A `glucose` (49% hiányzik) és az `income` (33% hiányzik) mediánnal való kitöltése** a betegek nagy részének ugyanazt az értéket adja, ami gyengíti ezeket a jellemzőket.
- **3. napi mérések:** az előrejelzés a vizsgálat 3. napjától készül, nem a kórházi felvételtől.
