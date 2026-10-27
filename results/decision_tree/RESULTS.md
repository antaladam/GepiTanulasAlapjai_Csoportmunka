# Döntési fa: módszer és eredmények

Ez a dokumentum leírja, mit csinál a `scripts/decision_tree.py` szkript, milyen eredményeket adott, és mely eredmények érdemesek a beszámolóban külön tárgyalásra. 
Az adatkészletet és az előfeldolgozást a repó gyökerében lévő `DATASET.md` írja le.

A fájlok előállítása (a `scripts/prepare_data.py` lefuttatása után):

```
python scripts/decision_tree.py
```

A szkript rögzített véletlenmaggal (42) fut, így újrafuttatva pontosan ugyanezeket az eredményeket adja.

## 1. Mit csinál a szkript

**Adatok:** a skálázatlan `data/processed/train.csv` (6 828 beteg) és `test.csv` (2 277 beteg). A döntési fa küszöbértékek mentén dönt (például „`aps` ≤ 50,5?”), ezért a skálázás nem befolyásolja.
Jellemzőként az `id` és a `hospdead` kivételével mind a 42 oszlopot használja, a célváltozó a `hospdead`.

**A fa méretének megválasztása:** egy korlátozás nélküli döntési fa addig hoz létre leveleket, amíg minden levélben csak egy osztály marad, így megtanulja a tanító adatokat, de új betegeken rosszul teljesít (túlillesztés). Ezért a fa méretét két beállítással korlátozzuk:

- `max_depth`: legfeljebb hány kérdés mélységű lehet a fa. Kipróbált értékek: 2, 3, 4, 5, 6, 8, 10, 15, korlátlan.
- `min_samples_leaf`: legalább hány beteg legyen egy levélben. Kipróbált értékek: 1, 10, 25, 50, 100, 200, 400.

Ez 9 × 7 = 63 beállítás. Mindegyiket **5-szörös rétegzett keresztvalidációval** értékeljük, kizárólag a tanító halmazon (scikit-learn `GridSearchCV`, `StratifiedKFold`). 
A tanító halmazt 5 részre osztjuk; a fát 4 részen tanítjuk, az 5.-en értékeljük, és ezt mind az 5 résszel megismételjük. 
Egy beállítás pontszáma az 5 AUROC átlaga. A legjobb átlagot adó beállítás lesz a végleges fa.

**Értékelés a teszthalmazon:** a kiválasztott fát egyszer, a végén értékeljük a teszthalmazon: AUROC, pontosság (accuracy), precizitás (precision), érzékenység (recall), F1 és tévesztési mátrix.
Az osztályba sorolás küszöbe a scikit-learn alapértelmezett 0,5-ös valószínűsége.

**Összehasonlítás súlyozott osztályokkal:** ugyanezt a hangolást a `class_weight="balanced"` beállítással is elvégezzük. 
Ez a ritkább osztály (halálozás, 26%) hibáit nagyobb súllyal veszi figyelembe, így a fa jobban figyel az elhunyt betegekre. 
Ez a változat a saját legjobb beállítását kapja a keresztvalidációból.

**Kimeneti fájlok** (ebben a mappában):

| Fájl | Tartalom |
|---|---|
| `cv_results.csv` | Mind a 63 beállítás: átlagos tanító és keresztvalidációs AUROC, a keresztvalidációs AUROC szórása, rangsor |
| `test_metrics.csv` | A két kiválasztott fa (súlyozás nélkül és súlyozva) eredménye a teszthalmazon, a tévesztési mátrix négy értékével |
| `complexity_curve.png` | Tanító és keresztvalidációs AUROC a fa mélysége szerint, két panelen: levélkorlát nélkül és a kiválasztott levélkorláttal |
| `tree_top3.png` | A kiválasztott fa felső 3 szintje |
| `feature_importance.png` | A legfontosabb jellemzők (legfeljebb 15, legalább 0,001 fontosságúak) |

## 2. Eredmények

### 2.1 A kiválasztott fa

- **Legjobb beállítás:** `min_samples_leaf` = 200, `max_depth` = 10. Keresztvalidációs AUROC: **0,832** (szórás az 5 rész között: 0,005).
- A fa ténylegesen **9 szint mély, 26 levele** van. A 200 betegnyi levélkorlát miatt nem tud mélyebbre nőni, ezért a `max_depth` = 10, 15 és korlátlan beállítás pontosan ugyanazt a fát adja (holtverseny az első helyen). 
  A szkript ezek közül az elsőt választotta, ez az eredményt nem befolyásolja.

A keresztvalidáció legjobb 7 beállítása (`cv_results.csv`):

| Helyezés | `max_depth` | `min_samples_leaf` | Tanító AUROC | Keresztvalidációs AUROC |
|---|---|---|---|---|
| 1 | 10 / 15 / korlátlan | 200 | 0,848 | 0,832 |
| 4 | 8 | 200 | 0,848 | 0,832 |
| 5 | 6 | 200 | 0,846 | 0,832 |
| 6 | 5 | 200 | 0,842 | 0,830 |
| 7 | 6 | 100 | 0,855 | 0,830 |

### 2.2 Túlillesztés: a komplexitási görbe

Tanító és keresztvalidációs AUROC a mélység szerint (`complexity_curve.png`):

| `max_depth` | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 15 | korlátlan |
|---|---|---|---|---|---|---|---|---|---|
| Levélkorlát nélkül (1): tanító | 0,768 | 0,819 | 0,838 | 0,855 | 0,873 | 0,916 | 0,955 | 0,995 | 1,000 |
| Levélkorlát nélkül (1): keresztvalidáció | 0,764 | 0,813 | 0,826 | 0,823 | 0,807 | 0,749 | 0,694 | 0,634 | 0,665 |
| Levélkorlát 200: tanító | 0,768 | 0,819 | 0,834 | 0,842 | 0,846 | 0,848 | 0,848 | 0,848 | 0,848 |
| Levélkorlát 200: keresztvalidáció | 0,764 | 0,816 | 0,826 | 0,830 | 0,832 | 0,832 | 0,832 | 0,832 | 0,832 |

### 2.3 Eredmények a teszthalmazon

A teszthalmazban 2 277 beteg van, ebből 590 halt meg a kórházban (25,9%).

| Modell | Beállítás | Levelek | Keresztval. AUROC | Teszt AUROC | Pontosság | Precizitás | Érzékenység | F1 |
|---|---|---|---|---|---|---|---|---|
| Fa | mélység 10, levél ≥ 200 | 26 | 0,832 | 0,851 | 0,815 | 0,676 | 0,549 | 0,606 |
| Fa, súlyozott osztályok | mélység 6, levél ≥ 100 | 28 | 0,828 | 0,848 | 0,787 | 0,567 | 0,759 | 0,649 |

Tévesztési mátrixok a teszthalmazon:

| | Fa | Fa, súlyozott osztályok |
|---|---|---|
| Túlélt, túlélőnek jelezve (TN) | 1 532 | 1 345 |
| Túlélt, halálozásnak jelezve (FP, téves riasztás) | 155 | 342 |
| Meghalt, túlélőnek jelezve (FN, kihagyott eset) | 266 | 142 |
| Meghalt, halálozásnak jelezve (TP) | 324 | 448 |

### 2.4 A legfontosabb jellemzők

A kiválasztott fában a jellemzők fontossága (a teljes szennyezettség-csökkenésből való
részesedés, `feature_importance.png`):

| Jellemző | Fontosság |
|---|---|
| `aps` (APACHE III fiziológiai pontszám, 3. nap) | 0,537 |
| `sps` (SUPPORT fiziológiai pontszám, 3. nap) | 0,203 |
| `scoma` (SUPPORT kómapontszám, 3. nap) | 0,190 |
| `dzgroup_ARF/MOSF w/Sepsis` | 0,026 |
| `hday` | 0,023 |
| `age` | 0,011 |
| `pafi` | 0,007 |
| `meanbp` | 0,002 |
| `dzgroup_CHF` | 0,001 |

A fa első vágása: `aps` ≤ 50,5. Az ennél nagyobb `aps` értékű betegek (a tanító halmaz 22,6%-a)
körében 59,5% a halálozás, a többiek körében 16,1% (`tree_top3.png`).

## 3. A beszámolóban érdemes tárgyalni

1. **A túlillesztés jól látható.** Levélkorlát nélkül a tanító AUROC a mélységgel 1,000-ig nő, a keresztvalidációs AUROC viszont 4-es mélységnél 0,826-os csúcsot ér el, majd 0,634–0,665-ig esik. 
   A fa egyre inkább a tanító betegeket „magolja be”, nem általánosítható mintázatokat tanul.
   200 betegnyi levélkorláttal a két görbe együtt marad (0,848 és 0,832), és a mélység növelése nem rontja az eredményt. 
   Ez a modellkomplexitás és a regularizáció (4. hét) szemléletes példája.

2. **Súlyozott osztályok: érzékenység kontra téves riasztás.** Súlyozás nélkül a fa a halálesetek 55%-át ismeri fel (324 / 590), súlyozva 76%-át (448 / 590). 
   Ennek ára a több téves riasztás: 155 helyett 342 túlélőt jelez halálozásnak, a precizitás 0,68-ról 0,57-re csökken. 
   Az AUROC szinte azonos (0,851 és 0,848), vagyis a két fa nagyjából egyformán jól rangsorolja a betegeket; a különbség főleg abból adódik, hol húzódik a döntési küszöb. 
   Hogy melyik a jobb, az alkalmazástól függ: egy szűrő jellegű riasztásnál a kihagyott haláleset drágább, mint a téves riasztás.

3. **Három jellemző végzi szinte az egész munkát.** Az `aps`, az `sps` és a `scoma` adja a fontosság 93%-át. 
   Klinikailag ez érthető, hiszen ezek összetett súlyossági pontszámok, amelyeket éppen a halálozási kockázat becslésére fejlesztettek ki. 
   Ugyanakkor ez azt is jelenti, hogy a fa alig használja az egyes laborértékeket, mert ezek információja nagyrészt már benne van a pontszámokban (lásd `DATASET.md`, 3. fejezet).

4. **Sok beállítás gyakorlatilag egyformán jó.** A legjobb beállítások közötti különbség (0,830 és 0,832 között) kisebb, mint a keresztvalidációs AUROC szórása (kb. 0,005). 
   A „legjobb” beállítás tehát nem egyértelműen jobb a többinél; a következtetés inkább az, hogy kb. 100–200 betegnyi levélkorláttal és legalább 5-ös mélységgel a fa stabilan kb. 0,83-as AUROC-ot ér el.

5. **A fa értelmezhető.** A `tree_top3.png` szabályként olvasható, például: ha `aps` > 50,5 és `sps` > 45,7, a halálozás aránya 91,2% (a tanító betegek 3,5%-a). 

6. **A pontosság önmagában félrevezető.** Ha a modell minden betegre azt mondaná, hogy túléli, a pontossága már 74,1% lenne (1 687 / 2 277), miközben egyetlen halálesetet sem ismerne fel. 
   Ezért az AUROC, az érzékenység, a precizitás és az F1 a mérvadó.

7. **A teszt AUROC kissé magasabb, mint a keresztvalidációs** (0,851 és 0,832). Ez a véletlen ingadozás része egyetlen, 2 277 betegből álló teszthalmazon, nem hiba; a modellt nem a teszthalmaz alapján választottuk ki.
