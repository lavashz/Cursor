import tkinter as tk
from tkinter import font as tkfont
import os
import sys
import json

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    import pygame
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
    PYGAME_OK = True
except Exception:
    PYGAME_OK = False

BG_COLOR    = "#0d0d12"
PANEL_COLOR = "#13131c"
TEXT_BOX_BG = "#0a0a10"
ACCENT      = "#c8a96e"
TEXT_COLOR  = "#e8e0d0"
NAME_COLOR  = "#c8a96e"
DIM         = "#555566"
BORDER      = "#2a2a3a"
CHAR_DELAY  = 30
IMAGES_DIR  = "images"

# ══════════════════════════════════════════════════════════════════════════════
#  SCENY — system etykiet (LABEL-BASED)
#
#  Zamiast kruchych numerycznych indeksów, każda scena może mieć pole "id"
#  (string), które służy jako CEL skoku. Wszystkie pola wskazujące cel:
#      - choices[i]["next"]
#      - "_goto"
#      - "_branch"        (wartości słownika)
#      - "_branch_rep"    ("default" + każdy próg w "thresholds")
#      - "_branch_var"    ("default" + każdy próg w "thresholds")
#  mogą być stringami (etykiety) lub intami (indeksy, kompatybilność wstecz).
#
#  Dodatkowe dyrektywy mutujące stan:
#      - "_set":  {var: value, ...}        — ustawia (nadpisuje)
#      - "_inc":  {var: delta, ...}        — inkrementuje liczbowo
#      - "_rep_add": {char: delta, ...}    — inkrementuje rep_{char} + toast
#
#  Sekwencyjny przepływ: jeśli scena nie ma _goto/_branch*/choices,
#  gra przechodzi do następnego elementu w SCENES (idx + 1).
# ══════════════════════════════════════════════════════════════════════════════

SCENES_BY_DAY = {

    # ── META (intro, koniec, game over) ─────────────────────────────────────
    0: [
        {"id": "title", "speaker": None, "text": "COLLEGE WITH SZYMON",
         "effect": "flash"},
    ],

    # ── DZIEŃ 1 ─────────────────────────────────────────────────────────────
    1: [
        {"speaker": None, "text": "Dzień 1"},
        {"speaker": None,
         "text": "Obudziłeś się na 7, żeby przyjść na swoje pierwsze w życiu zajęcia "
                 "na studiach. Bardzo się tym stresujesz..."},
        {"speaker": None,
         "text": "... Spotykasz jakiegoś gościa w korytarzu.",
         "image": "korytarz.png"},
        {"speaker": "Nieznajomy", "text": "Hej! Jak się nazywasz?",
         "image": "szymon_ukw_neutral.png"},
        {"speaker": None, "text": "Jak masz na imię?", "input": "mojeimie"},
        {"speaker": "Szymon",
         "text": "Bardzo miło cię poznać, {mojeimie}! Ja jestem Szymon — "
                 "dla kolegów po prostu Pecik haha ;)",
         "image": "szymon_ukw_happy.png"},

        # — Pytanie kolegi — pętla z licznikiem "Nie" odblokowuje Dzień 2115 —
        {"id": "ask_friend", "speaker": "Szymon",
         "text": "Może byś też chciał zostać moim kolegą?",
         "image": "szymon_ukw_happy.png",
         "choices": [
             {"label": "Tak, jasne!",  "next": "day1_friend"},
             {"label": "Nie, dzięki.", "next": "say_no"},
         ]},

        # Niewidoczny licznik klikniec "Nie" — 5 razy odblokowuje sekret.
        # Z perspektywy gracza kazde "Nie" wyglada na zwykla smierc + restart.
        {"id": "say_no", "speaker": None, "text": "",
         "_inc": {"no_count": 1},
         "_branch_var": {"var": "no_count",
                         "thresholds": [(5, "day2115_unlock")],
                         "default": "kill_screen"}},

        # Jeden ekran smierci dla klikniec 1-4 — wyglada identycznie, zeby
        # gracz nie podejrzewal ze cos sie pod spodem dzieje.
        {"id": "kill_screen", "speaker": None,
         "text": "SZYMON CIĘ ZABIŁ\n\n— GAME OVER —",
         "effect": "shake",
         "image": "szymon_ukw_neutral.png"},
        {"speaker": None,
         "text": "Czy chcesz rozpocząć grę od nowa?",
         "choices": [
             {"label": "Tak, od nowa", "next": "title"},
             {"label": "Nie, wyjdź",   "next": "true_game_over"},
         ]},

        # — 5te "Nie" — odblokowanie sekretu —
        {"id": "day2115_unlock", "speaker": "Szymon",
         "text": "Mam dziwne déjà vu... Jakbym... juz to mówiłem.",
         "image": "szymon_ukw_neutral.png"},
        {"speaker": "Szymon",
         "text": "Coś tu pęka. Stary, ja czuję jakąś dziurę w rzeczywistości.",
         "image": "szymon_ukw_neutral.png"},
        {"speaker": None,
         "text": "Korytarz się rozmywa. Światła migają.",
         "effect": "flash"},
        {"speaker": None,
         "text": "Czas się składa jak akordeon. Minęły sekundy. Albo lata. "
                 "Trudno powiedzieć.",
         "effect": "flash",
         "_goto": "day2115"},

        # — Normalna ścieżka (zostalismy kolegami) —
        {"id": "day1_friend", "speaker": "Szymon",
         "text": "Ale SUPEEEEERRRR! Dobra, muszę uciekać — nara!",
         "image": "szymon_happy.png",
         "_set": {"szymon": 1}, "_rep_add": {"szymon": 3}},
    ],

    # ── DZIEŃ 2 ─────────────────────────────────────────────────────────────
    2: [
        {"speaker": None, "text": "Dzień 2"},
        {"speaker": None,
         "text": "Idziesz do biblioteki, wziąć literaturę na ten semestr, "
                 "ale niechcący popchnąłeś kogoś plecami."},
        {"speaker": "Szymon",
         "text": "AŁAAAAAAA!!!!! Moje książki... Wszystkie wypadły :((((",
         "image": "szymon_neutral.png"},
        {"speaker": None, "text": "Co robisz?",
         "choices": [
             {"label": "Pomagasz pozbierać książki", "next": "lib_help"},
             {"label": "Sprzedajesz mu kopa",        "next": "lib_kick"},
         ]},

        {"id": "lib_help", "speaker": None,
         "text": "Szymon delikatnie się uśmiechnął, zarumienił się "
                 "i czule pocałował cię w policzek, po czym szybko uciekł.",
         "image": "szymon_happy.png", "_rep_add": {"szymon": 8},
         "_goto": "lib_done"},

        {"id": "lib_kick", "speaker": None,
         "text": "Zauważyłeś nawilżone oczy Szymona, poczułeś z tego satysfakcję, "
                 "nawet dostałeś nieoczekiwanej erekcji, a Szymon uciekł "
                 "ze łzami na oczach.",
         "image": "szymon_neutral.png", "_rep_add": {"szymon": -5}},

        {"id": "lib_done", "speaker": None,
         "text": "Wróciłeś do domu i słyszysz dźwięk powiadomienia w telefonie."},
        {"speaker": None,
         "text": "Dostajesz sprośną wiadomość na Messengerze od Szymusia."},
        {"speaker": "Szymon",
         "text": "Hejka, masz jakieś plany na dzisiejszy wieczór mistrzu?",
         "image": "szymon_happy.png"},
        {"speaker": "{mojeimie}",
         "text": "Hej Pecik! W suuuumie to nic przystojniaczku..."},
        {"speaker": "Szymon",
         "text": "A nie chciałbyś może ze mną wyjść na jakąś kawkę?",
         "image": "szymon_happy.png",
         "choices": [
             {"label": "Jasne, z przyjemnością!",  "next": "coffee_yes"},
             {"label": "Tylko jeśli ty płacisz ;)", "next": "coffee_yes",
              "_req_rep": ("szymon", 8)},
             {"label": "Nie mam czasu.",           "next": "coffee_refusal"},
         ]},

        {"id": "coffee_yes", "speaker": "Szymon",
         "text": "Super! Będzie bomba! :D", "image": "szymon_happy.png"},
        {"speaker": None, "text": "..."},
        {"speaker": None, "text": "19:00"},
        {"speaker": None,
         "text": "Ubrałeś się elegancko, ogoliłeś się wszędzie gdzie trzeba, "
                 "wypsikałeś pół butli Diora, a w autobusie każda babka się dusiła "
                 "która siedziała obok ciebie."},
        {"speaker": None,
         "text": "Stoisz już pod kawiarnią i widzisz jak pewnym krokiem idzie "
                 "bohater twoich marzeń.",
         "image": "szymon_happy.png"},
        {"speaker": "Szymon", "text": "Hej, przystojniaku, wyśmienicie pachniesz!",
         "image": "szymon_happy.png"},
        {"speaker": None, "text": "Co odpowiadasz?",
         "choices": [
             {"label": "Dzięki, ty też spoczko",                              "next": "coffee_nice"},
             {"label": "A ty byś się przynajmniej umył, śmierdzisz jak kupa", "next": "coffee_insult"},
             {"label": "Jeszcze lepiej smakuje",                              "next": "coffee_smooth"},
         ]},

        {"id": "coffee_nice", "speaker": "Szymon",
         "text": "Szymon się uśmiechnął.",
         "image": "szymon_happy.png", "_rep_add": {"szymon": 3},
         "_goto": "after_coffee_chat"},

        {"id": "coffee_insult", "speaker": "Szymon",
         "text": "Szymon spojrzał z zażenowaniem, ale zmilczał "
                 "i udał że nic nie usłyszał.",
         "image": "szymon_neutral.png", "_rep_add": {"szymon": -3}},
        {"speaker": None,
         "text": "Reszta spotkania odbyła się w bardzo niezręcznej atmosferze "
                 "i już chciałeś wracać do domu, ale nagle...",
         "_goto": "after_coffee_chat"},

        {"id": "coffee_smooth", "speaker": "Szymon",
         "text": "Szymon się speszył i dostał niechcianej erekcji.",
         "image": "szymon_happy.png", "_rep_add": {"szymon": 11}},
        {"speaker": None, "text": "..."},

        {"id": "after_coffee_chat", "speaker": None,
         "text": "Zauważyłeś że za stolikiem obok siedzi przystojny dżentelmen "
                 "z Rolexem na nadgarstku i setką cytrynówki w łapie."},
        {"speaker": None,
         "text": "Odważyłeś się do niego podejść i się przywitać."},
        {"speaker": "{mojeimie}",
         "text": "Cześć, jestem {mojeimie}, skądś cię kojarzę!"},
        {"speaker": "Światas",
         "text": "No tak, razem na wydziale jesteśmy, na szlugu często cię "
                 "widziałem. Jestem Światas, haha, miło cię poznać!"},
        {"speaker": None, "text": "Światas chce cię poczęstować setką."},
        {"speaker": None, "text": "Zgadzasz się?",
         "choices": [
             {"label": "Tak, chętnie!", "next": "swiati_yes"},
             {"label": "Nie, dzięki.",  "next": "swiati_no"},
         ]},

        {"id": "swiati_yes", "speaker": "Światas",
         "text": "Światas spojrzał na ciebie z dumą i zbił ci piątkę.",
         "_set": {"swiati": 1}, "_rep_add": {"swiatas": 5}},
        {"speaker": None,
         "text": "Po chwili poczułeś się słabo i Szymon odprowadził cię do domu.",
         "_goto": "day2_end"},

        {"id": "swiati_no", "speaker": "Światas",
         "text": "Światas spojrzał na ciebie z załamaniem i samotnie wypił "
                 "tę setkę na strzała.",
         "_rep_add": {"swiatas": -3}},
        {"speaker": None, "text": "Nie sprawiłeś na nim dobrego pierwszego wrażenia."},

        {"id": "day2_end", "speaker": None,
         "text": "Wróciłeś do domu i od razu zasnąłeś.",
         "_goto": "day3_start"},

        # ── ŚCIEŻKA BOCZNA: odmowa kawki ────────────────────────────────────
        {"id": "coffee_refusal", "speaker": "Szymon",
         "text": "O... rozumiem.",
         "image": "szymon_neutral.png", "_rep_add": {"szymon": -4}},
        {"speaker": None,
         "text": "Szymon wyraźnie się zmieszał. Przez chwilę milczał, "
                 "wpatrując się w ekran."},
        {"speaker": "Szymon",
         "text": "Okej, następnym razem może... no nic, nara.",
         "image": "szymon_neutral.png"},
        {"speaker": None,
         "text": "Odłożyłeś telefon i poczułeś jakiś dziwny niesmak."},
        {"speaker": None,
         "text": "Dzień 3 spędziłeś sam — bez kawy, bez Szymona, bez Światasa."},
        {"speaker": None,
         "text": "Wieczorem dostałeś powiadomienie na Messengerze od Szymona."},
        {"speaker": "Szymon",
         "text": "Byłem dzisiaj sam w tej kawiarni. Zamówiłem dwie kawy. "
                 "Jedną wypiłem. Drugą... zostawiłem.",
         "image": "szymon_neutral.png"},
        {"speaker": None, "text": "Co odpisujesz?",
         "choices": [
             {"label": "Przepraszam Pecik, następnym razem na pewno.",
              "next": "refusal_apology"},
             {"label": "Każdy ma prawo do własnego czasu.",
              "next": "refusal_dismiss"},
             {"label": "Hej, może jutro wyjdziemy razem? Mój treat.",
              "next": "refusal_invite", "_req_rep": ("szymon", 3)},
         ]},

        {"id": "refusal_apology", "speaker": "Szymon",
         "text": "Naprawdę? :) Trzymam cię za słowo!",
         "image": "szymon_happy.png", "_rep_add": {"szymon": 3},
         "_goto": "day4_start"},

        {"id": "refusal_dismiss", "speaker": "Szymon",
         "text": "Jasne... dobranoc.",
         "image": "szymon_neutral.png", "_rep_add": {"szymon": -2},
         "_goto": "day4_start"},

        {"id": "refusal_invite", "speaker": "Szymon",
         "text": "SERIO?! No to jutro o 18:00 pod tą samą kawiarnią, okej?! :D",
         "image": "szymon_happy.png", "_rep_add": {"szymon": 10}},
        {"speaker": None,
         "text": "Zasnąłeś z uśmiechem. Może nie wszystko stracone.",
         "_goto": "day4_start"},
    ],

    # ── DZIEŃ 3 — uniwersytet, ekipa Friki/Nate/Juras, Dima ─────────────────
    3: [
        {"id": "day3_start", "speaker": None, "text": "Dzień 3"},
        {"speaker": None,
         "text": "Przyszedłeś na zajęcia o czasie, ale wykładowca ewidentnie się spóźnia."},
        {"speaker": None,
         "text": "Stoisz pod salą już dobre 10 minut, a tłum studentów rośnie."},
        {"speaker": None,
         "text": "Pod ścianą widzisz ekipę chłopaków z roku: Nate, Juras "
                 "i Friki. Słyszysz strzępy ich rozmowy."},
        {"speaker": "Nate",
         "text": "No friki, no nie no, chodź z nami jutro do Pointa, zajebiście będzie!"},
        {"speaker": "Juras",
         "text": "No właśnie wbijaj z nami friki, cała grupa kierunku tam będzie."},
        {"speaker": "Friki",
         "text": "Kurna panowie, nie jestem takim klubowiczem, nie przepadam za tym, "
                 "sorki naprawdę."},
        {"speaker": "Nate",
         "text": "Stary, no nie bądź taki — jeden raz w życiu, na zdrowie się napijemy, "
                 "potańczymy, laski się popatrzą."},
        {"speaker": "Juras",
         "text": "No widzisz Friki, nawet Pecik ma większego cojonesa od ciebie."},
        {"speaker": None,
         "text": "Wszyscy patrzą na Szymona — który właśnie z plecakiem przerzuconym "
                 "przez jedno ramię przechodzi obok grupy.",
         "_branch_rep": {"char": "szymon",
                         "thresholds": [(0, "day3_szymon_friendly")],
                         "default": "day3_szymon_cold"}},

        # — Szymon w dobrej relacji z graczem —
        {"id": "day3_szymon_friendly", "speaker": "Szymon",
         "text": "{mojeimie}, hej! Co tam u ciebie?",
         "image": "szymon_happy.png"},
        {"speaker": None,
         "text": "Szymon podchodzi do ciebie z uśmiechem i przybija piątkę."},
        {"speaker": "Nate",
         "text": "Eee Pecik, słuchaj — jutro do Pointa wbijasz, nie? Cała grupa będzie!"},
        {"speaker": "Szymon",
         "text": "Eee... ja nie wiem chłopaki. Nie lubię takich miejsc, jest głośno, "
                 "ludzie głupieją, lampy migają...",
         "image": "szymon_neutral.png"},
        {"speaker": "Juras",
         "text": "No stary, raz w życiu! Jak nie spróbujesz to nigdy się nie przekonasz."},
        {"speaker": "Szymon",
         "text": "Nie wiem... {mojeimie}, a ty co o tym myślisz?",
         "image": "szymon_neutral.png",
         "choices": [
             {"label": "Idziemy razem, dam ci radę!", "next": "day3_player_push"},
             {"label": "To twoja decyzja Pecik.",     "next": "day3_player_neutral"},
             {"label": "Daj spokój, nie musisz.",     "next": "day3_player_against"},
         ]},

        {"id": "day3_player_push", "speaker": "Szymon",
         "text": "...no dobra, skoro ty idziesz, to ja też. Ale trzymaj się mnie!",
         "image": "szymon_happy.png", "_rep_add": {"szymon": 2},
         "_goto": "day3_dima"},

        {"id": "day3_player_neutral", "speaker": None,
         "text": "Szymon nadal niezdecydowany. Patrzy na podłogę i obraca pasek "
                 "plecaka w dłoni.",
         "_goto": "day3_dima"},

        {"id": "day3_player_against", "speaker": "Friki",
         "text": "O widzicie, mądry chłop! Nie każdy musi być stadnym zwierzęciem."},
        {"speaker": "Nate",
         "text": "Eee no co ty {mojeimie}, ty też z nami nie idziesz?"},
        {"speaker": None,
         "text": "Szymon spojrzał na ciebie z wdzięcznością — doceniasz że nie naciskasz.",
         "_rep_add": {"szymon": 1},
         "_goto": "day3_dima"},

        # — Szymon w złej relacji z graczem —
        {"id": "day3_szymon_cold", "speaker": None,
         "text": "Szymon przechodzi obok ciebie udając że cię nie widzi. "
                 "Twarz ma zaciśniętą.",
         "image": "szymon_neutral.png"},
        {"speaker": "Nate",
         "text": "Pecik, hej! Chodź z nami jutro do Pointa!"},
        {"speaker": None,
         "text": "Szymon przystaje. Wzrok wbity w podłogę. Wygląda jakby nie miał "
                 "siły walczyć z całym światem."},
        {"speaker": "Szymon",
         "text": "Nie wiem chłopaki... Sam się tam czuję trochę dziwnie.",
         "image": "szymon_neutral.png"},

        # — POJAWIA SIĘ DIMA —
        {"id": "day3_dima", "speaker": None,
         "text": "Z końca korytarza nadchodzi Dima — wraca z papierowym kubkiem "
                 "z automatu, irish cappuccino parzy mu palce."},
        {"speaker": "Dima",
         "text": "Co tam chłopaki, o czym gadka?"},
        {"speaker": "Nate",
         "text": "Próbujemy Pecika namówić na Pointa, ale jakoś nie idzie."},
        {"speaker": "Dima",
         "text": "Szymi, no co ty, co ty taki spięty. To tylko klub, "
                 "nie kopalnia."},
        {"speaker": "Szymon",
         "text": "Ja po prostu nie czuję tych miejsc... lampy migają, ludzie głupieją...",
         "image": "szymon_neutral.png"},
        {"speaker": "Dima",
         "text": "No dobra, posłuchaj mnie. Powiem ci tak. "
                 "Laski w Poincie są jak Bitcoin w 2010 roku."},
        {"speaker": "Dima",
         "text": "Kto teraz nie kupuje, ten za 10 lat będzie tylko żałował. "
                 "A ty młody jesteś, masz teraz okno."},
        {"speaker": "Nate", "text": "Hahaha no Dima dobre, zapisuję sobie!"},
        {"speaker": "Friki", "text": "Kurde, w sumie... ma sens."},
        {"speaker": "Juras",
         "text": "Słyszysz Pecik? Nawet Friki łapie o co chodzi."},
        {"speaker": "Szymon",
         "text": "...kurczę. Dobra. Idę. Ale tylko z {mojeimie}!",
         "image": "szymon_happy.png", "_rep_add": {"szymon": 1},
         "_set": {"day3_done": 1}},
        {"speaker": "Nate", "text": "ZAJEBIŚCIE PECIK! No to widzimy się jutro!"},
        {"speaker": "Friki",
         "text": "Eeeh, dobra, też wbijam. Jak Pecik daje radę to ja tym bardziej."},
        {"speaker": "Juras",
         "text": "Robi się ekipa! Jutro o 22:00 pod Pointem!"},
        {"speaker": "Dima",
         "text": "No widzicie. A teraz wybaczcie, idę dopić tę kawę zanim "
                 "wystygnie. Nara chłopaki."},
        {"speaker": None,
         "text": "Wykładowca w końcu przyszedł, ale reszta dnia minęła ci w napięciu — "
                 "myślisz tylko o jutrzejszym wieczorze."},
    ],

    # ── DZIEŃ 4 — POINT ─────────────────────────────────────────────────────
    4: [
        {"id": "day4_start", "speaker": None, "text": "Dzień 4"},
        {"speaker": None,
         "text": "Dzisiaj jest czwartek, a to oznacza czwartek studencki!"},
        {"speaker": None,
         "text": "Cała twoja grupa kierunku zbiera się do klubu Point — "
                 "i ty oczywiście też nie zamierzasz przegapić tej okazji."},
        {"speaker": None,
         "text": "Wybrałeś sobie luźny strój, nastawienie bojowe — "
                 "jesteś gotowy na dzisiejsze wyzwania."},
        {"speaker": None,
         "text": "Po drodze do klubu spotykasz grupkę groźnie wyglądających bandytów."},
        {"speaker": None,
         "text": "Okazuje się że to twój znajomy z roku — Oliwier ze swoim gangiem "
                 "Chomików: Stryjakiem, Urbanem i Lipskim."},
        {"speaker": None, "text": "Podchodzisz i witasz się z każdym..."},
        {"speaker": None,
         "text": "Zauważasz że jeden z nich — Lipski — ma mundur żołnierza SS."},
        {"speaker": None, "text": "Co robisz?",
         "choices": [
             {"label": "Chwalisz jego wygląd",      "next": "lipski_praise"},
             {"label": "Mówisz że wygląda jak debil","next": "lipski_insult"},
         ]},

        {"id": "lipski_praise", "speaker": "Lipski",
         "text": "Lipski kiwnął tobie z uśmieszkiem.",
         "_goto": "oliwier_drugs"},

        {"id": "lipski_insult", "speaker": "Lipski",
         "text": "Scheise, pilnuj języka chłopcze."},
        {"speaker": None,
         "text": "Lipski się zdenerwował i cała ekipa spojrzała na ciebie z pogardą."},

        {"id": "oliwier_drugs", "speaker": None,
         "text": "Widzisz że Oliwier ma ze sobą skórzaną teczkę — "
                 "ciekawość zwyciężyła i pytasz go co tam ma."},
        {"speaker": "Oliwier",
         "text": "Oliwier dumnie lecz stanowczo odpowiada że ma tam twarde narkotyki "
                 "i oferuje ci MDMA."},
        {"speaker": None, "text": "Co robisz?",
         "choices": [
             {"label": "Bierzesz",            "next": "drugs_branch"},
             {"label": "Grzecznie odmawiasz", "next": "drugs_branch"},
         ]},

        {"id": "drugs_branch", "speaker": None, "text": "...",
         "_branch_rep": {"char": "szymon",
                         "thresholds": [(0, "szymon_saves")],
                         "default": "point_solo"}},

        # ── PATH A: SZYMON RATUJE ──────────────────────────────────────────
        {"id": "szymon_saves", "speaker": None,
         "text": "Nie zdążyłeś nawet odpowiedzieć — zza pleców podbiega Szymon "
                 "i odprowadza cię od tych bandytów.",
         "image": "szymon_neutral.png"},
        {"speaker": "Szymon",
         "text": "{mojeimie}, no chyba cię pogrzało z nimi gadać — nawet nie wiesz "
                 "w co byś mógł wbrnąć.",
         "image": "szymon_neutral.png"},
        {"speaker": "{mojeimie}",
         "text": "Przepraszam Szymus, chciałem po prostu się poznać z chłopakami."},
        {"speaker": None, "text": "... Podbijacie już pod Pointa ..."},
        {"speaker": "Ochroniarz",
         "text": "Poproszę dowodzik, oj... paszport! Kurcze... legitymację!"},
        {"speaker": "{mojeimie}",
         "text": "Ej, kojarzę cię! Jesteś Krystian... Krystian Gaweł! Jesteśmy razem "
                 "na kierunku! Nie pracujesz przypadkiem w Chińskiej firmie?"},
        {"speaker": "Krystian",
         "text": "A wiesz co, firma zbankrutowała, teraz dorabiam w klubach."},
        {"speaker": None,
         "text": "Pokazujecie legitymacje, wchodzicie do klubu i od razu widzicie "
                 "znajome twarze."},
        {"speaker": None,
         "text": "Jest i ekipka Bully: Chomski z jego gangiem, ekipka dziewczyn KKK: "
                 "Karolina, Klaudia i Kinga, ekipka nerdów: Krystian, Marika i kochany "
                 "Maciej Reszka, i oczywiście też Chłopaki z Baraków. "
                 "W kącie Nate, Juras i Friki — kiwają do ciebie głową.",
         "_branch": {"swiati": "club_szymon_known_swiati",
                     None: "club_szymon_meet_swiati"}},

        # — Szymon + już znasz Światasa —
        {"id": "club_szymon_known_swiati", "speaker": None,
         "text": "Wszyscy razem dobrze spędzacie czas — tańczycie, pijecie "
                 "i się śmiejecie."},
        {"speaker": "Szymon",
         "text": "Chodź, {mojeimie}, postawię ci drinka!",
         "image": "szymon_happy.png"},
        {"speaker": None,
         "text": "Siedzicie za barem, dobrze się bawicie — lecz nagle Szymon gdzieś znika."},
        {"speaker": None,
         "text": "Po jakimś czasie widzisz jak wychodzi z toalety razem z Maciejem Reszką.",
         "_goto": "club_reszka_fight"},

        # — Szymon + pierwsze spotkanie Światasa w klubie —
        {"id": "club_szymon_meet_swiati", "speaker": None,
         "text": "Wszyscy razem dobrze spędzacie czas — tańczycie, pijecie "
                 "i się śmiejecie."},
        {"speaker": "Szymon",
         "text": "Chodź, {mojeimie}, postawię ci drinka!",
         "image": "szymon_happy.png"},
        {"speaker": None,
         "text": "Gdy Szymon odchodzi po drinka, przy barze zauważasz znajomą twarz — "
                 "facet z Rolexem, sam, z setką w łapie. Światas."},
        {"speaker": None,
         "text": "Masz chwilę zanim Szymon wróci. Co robisz?",
         "choices": [
             {"label": "Podchodzisz i zagadujesz do Światasa",
              "next": "meet_swiati_at_club"},
             {"label": "Zostajesz i czekasz na Szymona",
              "next": "club_reszka_setup"},
         ]},

        {"id": "meet_swiati_at_club", "speaker": "{mojeimie}",
         "text": "Hej, kojarzę cię z wydziału. Jestem {mojeimie}."},
        {"speaker": "Światas",
         "text": "No tak, widziałem cię parę razy. Światas. Siadaj na chwilę."},
        {"speaker": None,
         "text": "Rozmawiacie krótko — Światas jest konkretny, bez owijania w bawełnę."},
        {"speaker": "Światas", "text": "Mam tu setkę. Dasz radę?"},
        {"speaker": None, "text": "Co odpowiadasz?",
         "choices": [
             {"label": "Jasne, za znajomość!",  "next": "meet_swiati_drink"},
             {"label": "Dzięki, ale nie teraz.","next": "meet_swiati_pass"},
         ]},
        {"id": "meet_swiati_drink", "speaker": None,
         "text": "Stuknęliście kieliszki. Setka poszła w dół.",
         "_rep_add": {"swiatas": 4}, "_set": {"swiati": 1}},
        {"speaker": "Światas",
         "text": "Dobry jesteś. Trzymaj się, {mojeimie}.",
         "_rep_add": {"swiatas": 1},
         "_goto": "club_reszka_setup"},
        {"id": "meet_swiati_pass", "speaker": "Światas",
         "text": "Spoko, szanuję. Każdy ma swoje granice.",
         "_rep_add": {"swiatas": 1}},
        {"speaker": None,
         "text": "Wymieniliście kilka słów i Szymon wrócił z drinkami.",
         "_goto": "club_reszka_setup"},

        {"id": "club_reszka_setup", "speaker": None,
         "text": "Szymon wrócił z drinkami i siedzicie chwilę razem przy barze."},
        {"speaker": None,
         "text": "Po jakimś czasie Szymon znowu znika i widzisz jak wychodzi "
                 "z toalety razem z Maciejem Reszką."},

        {"id": "club_reszka_fight", "speaker": None,
         "text": "Podbiegasz wściekły do Szymona.",
         "image": "szymon_neutral.png"},
        {"speaker": "{mojeimie}",
         "text": "Pecie, co to ma znaczyć? — zapytałeś z drżącym głosem."},
        {"speaker": "Szymon",
         "text": "Nie, {mojeimie}, to nie jest tak jak myślisz.",
         "image": "szymon_neutral.png"},
        {"speaker": "Reszka", "text": "To prawda, my nic nie ro..."},
        {"speaker": "{mojeimie}",
         "text": "Zamknij się Reszka, myślicie że głupi jestem?"},
        {"speaker": None,
         "text": "Dochodzi do rękoczynów między tobą a Reszką."},
        {"speaker": None,
         "text": "Sprzedajesz mu liścia, ale Reszka stoi twardo.", "effect": "shake",
         "_branch_rep": {"char": "swiatas",
                         "thresholds": [(4, "reszka_swiati_helps")],
                         "default": "reszka_alone"}},

        {"id": "reszka_swiati_helps", "speaker": None,
         "text": "Tę sytuację zauważył Światas. Podbiega i też sprzedaje liścia Maciejowi.",
         "image": "swiatas.png"},
        {"speaker": None,
         "text": "Razem kopiecie go, a Szymon zaczyna płakać.",
         "image": "szymon_neutral.png",
         "_goto": "club_aftermath"},

        {"id": "reszka_alone", "speaker": "Szymon",
         "text": "Jesteś szalony!",
         "image": "szymon_neutral.png"},
        {"speaker": None,
         "text": "Razem z Szymonem patrzycie na Reszkę. Szymon zaczyna płakać.",
         "image": "szymon_neutral.png"},

        {"id": "club_aftermath", "speaker": None,
         "text": "Wypad do Pointa nie był udany."},
        {"speaker": None,
         "text": "Na drzwiach wejściowych Pointa wisi twoje zdjęcie oraz Światasa "
                 "z napisem:\n\n\"TYCH PANÓW NIE WPUSZCZAMY!!!\"",
         "effect": "flash",
         "_goto": "club_end"},

        # ── PATH B: SOLO DO POINTA ─────────────────────────────────────────
        {"id": "point_solo", "speaker": None,
         "text": "Oliwier próbuje wciskać ci narkotyki dalej, ale w końcu odpuszcza. "
                 "Idziesz sam pod Pointa."},
        {"speaker": None,
         "text": "... Stajesz przy wejściu sam. Bez Szymona. Trochę głupio."},
        {"speaker": "Ochroniarz",
         "text": "Poproszę dowodzik, oj... paszport! Kurcze... legitymację!"},
        {"speaker": "{mojeimie}",
         "text": "Ej, kojarzę cię! Jesteś Krystian... Krystian Gaweł! "
                 "Jesteśmy razem na kierunku!"},
        {"speaker": "Krystian",
         "text": "A wiesz co, firma zbankrutowała, teraz dorabiam w klubach. Wejdź, ziom."},
        {"speaker": None,
         "text": "Wchodzisz do środka sam. W klubie głośno, tłoczno — widzisz znajome "
                 "twarze, ale czujesz się trochę zagubiony."},
        {"speaker": None,
         "text": "Siadasz przy barze, zamawiasz drinka i rozglądasz się."},
        {"speaker": None,
         "text": "Nagle zauważasz przy końcu baru znajomą twarz — facet z Rolexem, "
                 "sam, z setką w łapie. Światas."},
        {"speaker": None, "text": "Co robisz?",
         "choices": [
             {"label": "Podchodzisz i zagadujesz", "next": "solo_swiati_approach"},
             {"label": "Siedzisz dalej sam",       "next": "solo_swiati_waits"},
         ]},

        {"id": "solo_swiati_approach", "speaker": "{mojeimie}",
         "text": "Hej, kojarzę cię z wydziału. Jestem {mojeimie}. Mogę się dosiąść?"},
        {"speaker": "Światas",
         "text": "Światas zmierzył cię wzrokiem przez chwilę, potem kiwnął głową. — "
                 "Czemu nie. Światas. Siadaj."},
        {"speaker": None,
         "text": "Siedzisz chwilę w milczeniu. Światas popija setkę, ty drinka."},
        {"speaker": "Światas", "text": "Sam dziś przyszedłeś?",
         "_rep_add": {"swiatas": 1}},
        {"speaker": None, "text": "Co odpowiadasz?",
         "choices": [
             {"label": "Tak, mój kumpel dziś nie mógł.",                "next": "solo_swiati_ans1"},
             {"label": "Lubię czasem sam sobie.",                        "next": "solo_swiati_ans2"},
             {"label": "Miałem iść z Szymonem, ale coś nie wyszło.",     "next": "solo_swiati_ans3"},
         ]},

        {"id": "solo_swiati_ans1", "speaker": "Światas",
         "text": "Aha, rozumiem. Ja też wolę czasem sam — łatwiej obserwować.",
         "_rep_add": {"swiatas": 2},
         "_goto": "solo_swiati_setka"},

        {"id": "solo_swiati_ans2", "speaker": "Światas",
         "text": "Światas uśmiechnął się lekko. — Człowiek z charakterem. Szanuję.",
         "_rep_add": {"swiatas": 3},
         "_goto": "solo_swiati_setka"},

        {"id": "solo_swiati_ans3", "speaker": "Światas",
         "text": "Szymon? Znam go. Dobry koleś, tylko trochę... skomplikowany.",
         "_rep_add": {"swiatas": 2}},

        {"id": "solo_swiati_setka", "speaker": None,
         "text": "Przez chwilę milczycie, obaj patrząc przed siebie."},
        {"speaker": "Światas",
         "text": "Słuchaj, mam tu jeszcze jedną setkę. Dasz radę?"},
        {"speaker": None, "text": "Co robisz?",
         "choices": [
             {"label": "Jasne, zdrowie!",          "next": "solo_swiati_drink"},
             {"label": "Dzięki, ale nie piję mocnych.","next": "solo_swiati_nodrink"},
         ]},

        {"id": "solo_swiati_drink", "speaker": None,
         "text": "Światas nalał, stuknęliście. Setka poszła w dół.",
         "_rep_add": {"swiatas": 4}, "_set": {"swiati": 1}},
        {"speaker": "Światas",
         "text": "Ha! Dobrze poszło. Lubię cię, {mojeimie}.",
         "_rep_add": {"swiatas": 1},
         "_goto": "solo_swiati_after"},

        {"id": "solo_swiati_nodrink", "speaker": "Światas",
         "text": "Światas wzruszył ramionami. — Szanuję. Każdy ma swoje granice."},
        {"speaker": None,
         "text": "Światas wypił sam, ale atmosfera nie była niezręczna — po prostu inaczej.",
         "_rep_add": {"swiatas": 1}},

        {"id": "solo_swiati_after", "speaker": None,
         "text": "Wymieniliście numery. Niezbyt wiele, ale jednak."},
        {"speaker": None,
         "text": "Reszta wieczoru minęła zaskakująco przyjemnie — "
                 "Światas okazał się dobrym rozmówcą."},
        {"speaker": None,
         "text": "Wracałeś do domu sam, ale z uczuciem że jednak coś dziś zyskałeś.",
         "_goto": "club_end"},

        {"id": "solo_swiati_waits", "speaker": None,
         "text": "Siedzisz przy barze sam przez jakiś czas. Muzyka gra, ludzie tańczą — "
                 "ty patrzysz w szklankę."},
        {"speaker": None,
         "text": "Nagle ktoś siada obok bez zaproszenia. Facet z Rolexem.",
         "_goto": "solo_swiati_setka"},

        # ── KLUB END ───────────────────────────────────────────────────────
        {"id": "club_end", "speaker": None,
         "text": "Wracasz w końcu do domu. Wieczór za tobą, klucz do drzwi w drżącej dłoni.",
         "_goto": "day5_start"},
    ],

    # ── DZIEŃ 5 — STOŁÓWKA PO POINTIE (wprowadzenie Nataniela + Kamila) ─────
    5: [
        {"id": "day5_start", "speaker": None, "text": "Dzień 5"},
        {"speaker": None,
         "text": "Rano. Głowa pęka. Wpadłeś do uniwersyteckiej stołówki "
                 "po kawę i kanapkę, modląc się żeby świat się ułożył."},
        {"speaker": None,
         "text": "Powoli przy długim stole zaczyna się zbierać ekipa."},

        # — Światas wchodzi pierwszy —
        {"speaker": None,
         "text": "Pierwszy wpada Światas — w okularach przeciwsłonecznych, "
                 "mimo że jesteśmy w środku budynku."},
        {"speaker": "Światas",
         "text": "Eee... {mojeimie}... ktoś mi pamięta jak się wczoraj dostałem do domu?"},
        {"speaker": None, "text": "Co mu odpowiadasz?",
         "choices": [
             {"label": "Spokojnie, odprowadziłem cię.", "next": "swiati_kac_help"},
             {"label": "Sam doszedłeś, kurwa nie wiem jak.","next": "swiati_kac_no"},
         ]},
        {"id": "swiati_kac_help", "speaker": "Światas",
         "text": "Hahaha dzięki ziom, jesteś legenda. Stawiam ci kawę.",
         "_rep_add": {"swiatas": 2},
         "_goto": "day5_friki"},
        {"id": "swiati_kac_no", "speaker": "Światas",
         "text": "Kurde no... Tata mówił że nie skończe dobrze. Tata miał rację."},

        # — Friki —
        {"id": "day5_friki", "speaker": None,
         "text": "Drzwi wybijają się i wbija Friki — z telefonem w ręce, "
                 "śmiejąc się sam do siebie."},
        {"speaker": "Friki",
         "text": "PANOWIE patrzcie! Patrzcie patrzcie, to jest ona, kurwa, "
                 "to jest 11/10, no powiedzcie sami!"},
        {"speaker": None,
         "text": "Friki podtyka ci telefon pod nos i jednocześnie kładzie ci "
                 "rękę na ramieniu, jakby to była najbardziej naturalna rzecz na świecie."},
        {"speaker": "Światas", "text": "Friki, łapy. Mam kaca."},
        {"speaker": "Friki",
         "text": "Sorka sorka, ale serio popatrzcie. Wczoraj na Tinderze. Match!"},

        # — Nataniel (Nate) z sushi —
        {"speaker": None,
         "text": "Siada Nataniel — z plastikowym pudełkiem sushi w jednej ręce, "
                 "kluczykami od auta w drugiej."},
        {"speaker": "Nataniel",
         "text": "Spóźniłem się chłopaki, sorka. Wczoraj zamykałem knajpę o północy, "
                 "potem 90 km z powrotem do Bydzi Passatem."},
        {"speaker": "Friki", "text": "Nat, masz coś z sushi? Głodny jestem jak pies!"},
        {"speaker": "Nataniel",
         "text": "Mam jeszcze rolki z wczoraj. Częstuj się {mojeimie}, ty pierwszy."},
        {"speaker": None, "text": "Bierzesz?",
         "choices": [
             {"label": "Jasne, dzięki Nat!",        "next": "nat_sushi_yes"},
             {"label": "Nie, kac mi nie pozwala.", "next": "nat_sushi_no"},
         ]},
        {"id": "nat_sushi_yes", "speaker": "Nataniel",
         "text": "Spoko ziom. Smakuje? Sam sklejam.",
         "_rep_add": {"nataniel": 3},
         "_goto": "day5_kamil"},
        {"id": "nat_sushi_no", "speaker": "Nataniel",
         "text": "Spoko spoko, rozumiem. Jak będziesz w Bydzi w Sushi Mura, "
                 "to powiedz że jesteś moim ziomkiem — dam ci zniżkę.",
         "_rep_add": {"nataniel": 1}},

        # — Kamil z notatkami —
        {"id": "day5_kamil", "speaker": None,
         "text": "Wchodzi Kamil — z laptopem pod pachą i otwartym notesem. "
                 "Spokojny, skupiony."},
        {"speaker": "Nataniel",
         "text": "O Kamil! Słuchaj, jutro mamy kolosa z analizy. Ratuj."},
        {"speaker": "Kamil",
         "text": "Siadaj Nat, pokaż mi zadania. To nie jest trudne, tylko trzeba "
                 "rozumieć po co się to robi."},
        {"speaker": None,
         "text": "Kamil rozkłada notatki na całym stole. Co druga strona ma "
                 "kolorowe podkreślenia i strzałki."},
        {"speaker": "Friki",
         "text": "Kamil ty jesteś bogiem. Wiesz że jesteś moim wzorem? Daj się przytulić."},
        {"speaker": "Kamil",
         "text": "Friki, później. Najpierw Nat zda kolosa.",
         "_rep_add": {"kamil": 2}},

        # — Dima na koniec —
        {"speaker": None,
         "text": "Ostatni przychodzi Dima — z kawą z automatu i tajemniczym uśmiechem. "
                 "Siada powoli."},
        {"speaker": "Dima",
         "text": "Ej chłopaki. Słuchajcie. Pomyślałem sobie dziś rano coś ważnego."},
        {"speaker": "Juras",
         "text": "O nie. Czuję że to bedzie dobre. Dawaj Dima, zamieniamy się w słuch."},
        {"speaker": "Dima",
         "text": "Fordon to nie jest dzielnica Bydgoszczy. Fordon to jest stan umysłu."},
        {"speaker": None, "text": "Sekunda ciszy. Potem Friki ryczy ze śmiechu, Światas się krztusi kawą."},
        {"speaker": "Dima",
         "text": "Pomyślcie. Ludzie tam mieszkają, ale nigdy się nie zastanowili dlaczego "
                 "budzą się szczęśliwi. Bo Fordon ich kocha. A oni nie wiedzą."},
        {"speaker": "Friki", "text": "Dima, ty mi dzisiaj zostań blisko, ja muszę słyszeć więcej!"},
        {"speaker": "Juras",
         "text": "Hahaha no Dima, gratulacje. Po raz kolejny mistrz przekminki dnia."},
        {"speaker": "Kamil", "text": "Mnie się to faktycznie podoba. Fordon = telos. Spoko."},
        {"speaker": None,
         "text": "Ekipa siedzi razem jeszcze godzinę. Pierwszy raz od dawna "
                 "czujesz że to ekipa.",
         "_set": {"day5_done": 1}},
    ],

    # ── DZIEŃ 6 — WYCIECZKA DO USTKI ────────────────────────────────────────
    6: [
        {"id": "day6_start", "speaker": None, "text": "Dzień 6"},
        {"speaker": None,
         "text": "Wiadomość na grupie 'Chomiki ale gay': "
                 "'Chłopaki, jadę pojutrze na ryby do Ustki, kto wbija?' "
                 "— Kamil."},
        {"speaker": None,
         "text": "W ciągu 10 minut zapisali się wszyscy: Friki, Juras, Dima, "
                 "Nataniel, Szymon, Światas, ty."},
        {"speaker": "Nataniel",
         "text": "Spoko, bierzemy mojego Passata. 7 osób się zmieści, jak Friki "
                 "siądzie Frikiemu na kolanach."},
        {"speaker": "Friki", "text": "Nat, dla ciebie wszystko."},

        # — Spotkanie rano przy aucie —
        {"speaker": None,
         "text": "Sobota, 6:00 rano. Stoicie pod blokiem Nataniela. Passat 2004, "
                 "srebrny, wypolerowany jak nowy."},
        {"speaker": "Nataniel",
         "text": "Tylko po cichutku przy wsiadaniu, ona stara baba jest, "
                 "ale jak ją kocham..."},
        {"speaker": "Światas",
         "text": "Nat, ty z tym autem mówisz jak z dziewczyną. Ty się dobrze czujesz?"},

        # — W aucie, wybór sąsiada —
        {"speaker": None,
         "text": "Nataniel za kierownicą. Friki obok (oczywiście). Z tyłu masz miejsce. "
                 "Obok kogo siedzisz?",
         "choices": [
             {"label": "Obok Dimy",   "next": "ride_dima"},
             {"label": "Obok Jurasa", "next": "ride_juras"},
             {"label": "Obok Kamila", "next": "ride_kamil"},
         ]},

        {"id": "ride_dima", "speaker": "Dima",
         "text": "{mojeimie}, dobry wybór! Wziąłem gitarę, będzie się działo."},
        {"speaker": None,
         "text": "Dima rzeczywiście wyciąga akustyk z pokrowca. Po dwóch akordach "
                 "rozpoznajesz — to Patoreac. Cała ekipa zaczyna nucić."},
        {"speaker": "Friki", "text": "Dima! Brachu! Zrób refren głośniej!"},
        {"speaker": "Dima",
         "text": "Tylko żeby Nataniel nie zlał auta — bo wtedy ja przesiądę się "
                 "na strunę G i się zabiję."},
        {"speaker": None,
         "text": "Cała droga zlecia w mgnieniu oka — Dima gra trzy piosenki, "
                 "potem oddaje gitarę Szymonowi który próbuje Bedoesa na akustyku.",
         "_rep_add": {"dima": 3},
         "_goto": "ustka_arrival"},

        {"id": "ride_juras", "speaker": "Juras",
         "text": "No to organizujemy, {mojeimie}. Bierzesz wodę, kanapki, ja przejmuję "
                 "harmonogram. Friki sprawdzasz przynęty, Kamil — wędki, Dima — "
                 "płacisz na stacji."},
        {"speaker": None, "text": "Juras wszystko ogarnia. Czujesz że dzień będzie udany.",
         "_rep_add": {"juras": 3},
         "_goto": "ustka_arrival"},

        {"id": "ride_kamil", "speaker": "Kamil",
         "text": "{mojeimie}, ty już byłeś w Ustce? Tam jest takie miejsce za starym molo, "
                 "tam zawsze coś bierze. Pokażę ci."},
        {"speaker": None,
         "text": "Kamil opowiada ci wszystko o rybach, mówi że nauczyłeś się więcej "
                 "niż na zajęciach z biologii w liceum.",
         "_rep_add": {"kamil": 3},
         "_goto": "ustka_arrival"},

        # — W drodze drama o muzykę —
        {"id": "ustka_arrival", "speaker": None,
         "text": "Po drodze Friki próbuje przejąć aux."},
        {"speaker": "Friki",
         "text": "Nat puść mnie do aux! Mam playlistę dance, wszyscy potańczymy w aucie!"},
        {"speaker": "Nataniel", "text": "Friki, w Passacie się NIE TAŃCZY."},
        {"speaker": "Szymon",
         "text": "Nat, mogę ja? Mam świeży drop Bedoesa, jeszcze nawet nikt nie zna."},
        {"speaker": "Nataniel", "text": "Pecik, tylko ty. Bedoes może być."},
        {"speaker": None,
         "text": "Bedoes leci od Bydgoszczy do Słupska. Szymon śpiewa każde słowo."},

        # — Ustka, łowienie —
        {"speaker": None,
         "text": "Ustka. Plaża. Wiatr. Kamil prowadzi was za stare molo."},
        {"speaker": None,
         "text": "Po dwóch godzinach łapania pustek — Kamilowi bierze. Ciągnie. "
                 "I ciągnie. Wyciąga rybę 40cm."},
        {"speaker": "Kamil", "text": "Tak. To jest moment dla którego się żyje."},
        {"speaker": "Friki",
         "text": "Kamil!!! Pokaż! Pokaż! Czekaj, ja ją złapię, daj mi ją potrzymać!"},
        {"speaker": None,
         "text": "Friki podbiega do wędki Kamila — niechcący nadepnie na rączkę. "
                 "TRZASK. Wędka pęka na pół.",
         "effect": "shake"},
        {"speaker": "Kamil", "text": "..."},
        {"speaker": "Friki",
         "text": "O kurwa. Kamil. Kamil ja nie chciałem, naprawdę, ja po prostu się "
                 "ucieszyłem dla ciebie."},
        {"speaker": None, "text": "Kamil patrzy na połamaną wędkę. Cisza."},
        {"speaker": None, "text": "Co robisz?",
         "choices": [
             {"label": "Friki to wypadek, każdy widzi.",         "next": "wedka_friki_def"},
             {"label": "Friki, kupisz mu nową w poniedziałek.", "next": "wedka_mediator"},
             {"label": "Friki, znowu coś popsułeś, kurwa.",     "next": "wedka_friki_blame"},
         ]},

        {"id": "wedka_friki_def", "speaker": "Kamil",
         "text": "...{mojeimie}, ja wiem że to wypadek. Ale to była wędka po dziadku.",
         "_rep_add": {"kamil": -3, "friki": 4}},
        {"speaker": "Friki",
         "text": "Stary, kupię ci taką samą, przysięgam. Pójdę z Natanielem do sklepu.",
         "_goto": "ustka_fire"},

        {"id": "wedka_mediator", "speaker": "Kamil",
         "text": "...okej. Friki, czekam.",
         "_rep_add": {"kamil": 2, "friki": 2}},
        {"speaker": "Friki", "text": "Słowo, Kamil. Słowo.",
         "_goto": "ustka_fire"},

        {"id": "wedka_friki_blame", "speaker": "Friki",
         "text": "{mojeimie}... no kurwa, nie tak. Przeprosiłem.",
         "_rep_add": {"friki": -5, "kamil": 3}},
        {"speaker": "Juras",
         "text": "{mojeimie}, spokojnie. To wypadek. Friki kupi nową, koniec.",
         "_rep_add": {"juras": 1}},

        # — Ognisko na plaży, Dima z gitarą —
        {"id": "ustka_fire", "speaker": None,
         "text": "Wieczór. Atmosfera trochę zgaszona po wędce. Kamil rozpala małe "
                 "ognisko z drewna wyrzuconego przez morze."},
        {"speaker": "Dima",
         "text": "Chłopaki, przyniosłem gitarę. Nikt nie protestuje?"},
        {"speaker": "Szymon",
         "text": "Dima, ty na gitarze? Pierwsze słyszę. Pokazuj.",
         "image": "szymon_happy.png"},
        {"speaker": None,
         "text": "Dima siada bliżej ognia, stroi przez chwilę, kaszle teatralnie."},
        {"speaker": "Dima",
         "text": "Coś łatwego na początek. Tylko ostrzegam — śpiewam jak chrześcijanin "
                 "po sześciu piwach."},
        {"speaker": None,
         "text": "Pierwsze akordy. Akustyczna wersja czegoś z radia — wszyscy "
                 "rozpoznają od razu. Nataniel zaczyna nucić, Friki przytula się "
                 "do Jurasa (Juras nawet nie protestuje)."},
        {"speaker": "Kamil",
         "text": "Dima... ty się pod tym śmiejesz, ale serio dobrze grasz. Bez ściemy.",
         "_rep_add": {"dima": 2, "kamil": 1}},
        {"speaker": "Światas",
         "text": "Dima, brachu. Następna piosenka — 'Wonderwall'. Klasyk pod kamerę."},
        {"speaker": "Dima",
         "text": "Świat, nie kazda akustyczna noc musi być 'Wonderwall'. "
                 "Ale dobra, dla ciebie."},
        {"speaker": None,
         "text": "Drugi utwór. Wszyscy śpiewają — fałszywie, głośno, szczerze. "
                 "Nawet Kamil odkłada notatki w plecaku."},
        {"speaker": "Dima",
         "text": "Wiecie co? Czuję się jak na okładce indie zespołu z 2014 roku. "
                 "To miało być smutne, a wyszło ładnie."},
        {"speaker": "Juras", "text": "Dima, kurde, sentymentalisz nam. Daj jeszcze jedną."},
        {"speaker": None,
         "text": "Trzecia piosenka. Ostatnia. Ognisko prawie zgasło, ale nikt "
                 "się nie ruszył. Dobre 20 minut nikt nic nie mówi po niej.",
         "_rep_add": {"dima": 3}},

        # — Wracając —
        {"id": "ustka_return", "speaker": None,
         "text": "Wracając. Passat śmierdzi rybami. Nataniel ledwo wytrzymuje, "
                 "okno otwarte na max."},
        {"speaker": "Nataniel", "text": "Friki, daj mi święte słowo że nie zrobiłeś tego specjalnie."},
        {"speaker": "Friki", "text": "Nat, gdybym chciał to byłbym wzięty na klatę, słowo skauta."},
        {"speaker": "Dima",
         "text": "Spokojnie Nat, ja tę gitarę odłożyłem dalej od ryby. Świat jest sprawiedliwy."},
        {"speaker": "Juras", "text": "Hahaha Dima, ty zawsze jedną nogą w innym wymiarze."},

        # — Friki śpi na ramieniu Nataniela —
        {"speaker": None,
         "text": "Pod koniec drogi Friki zasypia. Z głową na ramieniu Nataniela. "
                 "Ślini się na jego kurtkę. Nataniel patrzy w lusterko bezsilnie."},
        {"speaker": "Nataniel", "text": "Czemu zawsze ja..."},
        {"speaker": None,
         "text": "Wyrzucacie się pod Bydzią. Wszyscy zmęczeni, ale dobry dzień. "
                 "Pierwszy raz czujesz że Kamil cię polubił.",
         "_set": {"day6_done": 1}},
    ],

    # ── DZIEŃ 7 — IMPREZA U FRIKIEGO + ZDRADA ───────────────────────────────
    7: [
        {"id": "day7_start", "speaker": None, "text": "Dzień 7"},
        {"speaker": None,
         "text": "Friki wysyła zaproszenie na grupę: "
                 "'Panowie 20:00 u mnie pre-party, potem do klubu lecimy!'"},
        {"speaker": None,
         "text": "20:15. Mieszkanie Frikiego — mały kawalerek na Bartodziejach, "
                 "głośna muzyka, świece zapachowe (które gasną od dymu)."},
        {"speaker": None,
         "text": "Są wszyscy: Szymon, Juras, Dima, Nataniel, Kamil, Światas, ty."},
        {"speaker": "Friki",
         "text": "PANOWIE! Shoty! Wszyscy! Nikt mi się nie wymknie!"},

        # — Vignettes z imprezy —
        {"speaker": None,
         "text": "Światas po dwóch shotach już mówi z trudem."},
        {"speaker": "Światas",
         "text": "Eee... ja juz po dwóch... normalnie tak nie miało być... ja sobie "
                 "tylko siądę tu pod ścianą."},
        {"speaker": None,
         "text": "Dima stoi w kuchni przy otwartej lodówce. Studiuje zawartość "
                 "jak święte teksty."},
        {"speaker": "Dima",
         "text": "Kurde patrzcie. Friki ma 4 piwa, 1 ser i ketchup. To jest piękne. "
                 "To jest pokój ostatniej wolności."},
        {"speaker": "Kamil",
         "text": "Dima, masz to nagrane? Bo ja muszę to przemyśleć w domu."},
        {"speaker": None,
         "text": "Dima przemyka się do salonu, wyciąga z kąta gitarę Frikiego "
                 "(skąd Friki ma gitarę?), siada na podłodze i zaczyna nucić cicho. "
                 "Tło dla całej imprezy."},
        {"speaker": "Friki",
         "text": "Dima ratuje wieczór jak zawsze. Patrzcie, kto wykrył moją gitarę "
                 "której sam nie umiem używać!"},
        {"speaker": None,
         "text": "Friki krąży po pokoju i całuje każdego w policzek z napisem 'KOCHAM CIĘ'."},
        {"speaker": "Friki",
         "text": "{mojeimie}, ty też! Dawaj policzek! Nie uciekaj!"},
        {"speaker": "Juras",
         "text": "Friki, jeszcze dwa policzki i wzywam ochronę osobistą."},
        {"speaker": None,
         "text": "Szymon siedzi w kącie, słuchawki w uszach. Kiwa głową w rytmie. "
                 "Bedoes oczywiście."},

        # — Plot twist: zarysowany Passat —
        {"speaker": None,
         "text": "21:30. Nataniel wychodzi na chwilę do auta, sprawdzić czy zamknięte. "
                 "Wraca po 3 minutach. Biały jak ściana."},
        {"speaker": "Nataniel",
         "text": "Chłopaki... ktoś mi zarysował Passata. Wielką literą. K. "
                 "Wzdłuż całego boku."},
        {"speaker": None, "text": "Cisza. Tylko Bedoes leci z głośnika."},
        {"speaker": "Friki",
         "text": "K? K... K jak Krystian? K jak Klaudia? K jak Kamil? K jak... kurwa?"},
        {"speaker": "Juras",
         "text": "Friki, zamknij się. Nat, spokojnie. Da się to wypolerować."},
        {"speaker": "Kamil",
         "text": "Nat, sprawdziłeś monitoring osiedla? Pewnie jakiś jest."},
        {"speaker": "Światas",
         "text": "Eee ja nic nie wiem, nikomu nic nie mówiłem... znaczy znaczy, "
                 "ja po prostu siedziałem."},
        {"speaker": "Dima",
         "text": "Wiecie że K jako litera oznacza chaos? Po grecku 'kaos'. To znak."},
        {"speaker": "Nataniel",
         "text": "Dima, stary, kocham cię, ale jutro mi to powiesz. Dzisiaj nie dam rady."},

        # — Wybór gracza —
        {"speaker": None, "text": "Nataniel patrzy na ciebie. Co podpowiadasz?",
         "choices": [
             {"label": "To pewnie jakieś dzieciaki z osiedla.",
              "next": "passat_kids"},
             {"label": "Sprawdź monitoring, Kamil ma rację.",
              "next": "passat_camera"},
             {"label": "K... Może Klaudia? Słyszałem że się z nią pokłóciłeś.",
              "next": "passat_klaudia"},
             {"label": "Nat, ja ci zrzucę kasę na polerkę. Spokojnie.",
              "next": "passat_money"},
         ]},

        {"id": "passat_kids", "speaker": "Nataniel",
         "text": "Pewnie masz rację. Kurwa, no nic. Zgłoszę policji.",
         "_rep_add": {"nataniel": 1},
         "_goto": "passat_aftermath"},

        {"id": "passat_camera", "speaker": "Kamil",
         "text": "{mojeimie}, ty też tak myślisz? Dobra, Nat, jutro pójdę z tobą "
                 "do spółdzielni.",
         "_rep_add": {"kamil": 3, "nataniel": 2},
         "_goto": "passat_aftermath"},

        {"id": "passat_klaudia", "speaker": "Nataniel",
         "text": "Klaudia?! Kurwa. Faktycznie się pokłóciliśmy w środę. "
                 "Ty masz coś z głową, ona by tego nie zrobiła. ...A może by?",
         "_rep_add": {"nataniel": -2}},
        {"speaker": "Friki",
         "text": "{mojeimie}, ja byłbym ostrożny z takimi oskarżeniami, "
                 "Klaudia to jest typ co potrafi przyjść tutaj i rozbić mi okna."},

        {"id": "passat_money", "speaker": "Nataniel",
         "text": "Stary... nie. Doceniam, ale nie. To moja sprawa.",
         "_rep_add": {"nataniel": 4}},
        {"speaker": "Juras",
         "text": "{mojeimie}, dobry gest. Nat, on naprawdę by zrzucił, ja go znam.",
         "_rep_add": {"juras": 1}},

        # — Aftermath —
        {"id": "passat_aftermath", "speaker": None,
         "text": "Wieczór się rozwala. Nataniel nigdzie nie jedzie, zostaje w Bydzi "
                 "do polerki. Klub odwołany."},
        {"speaker": "Friki",
         "text": "Panowie, sorka że tak skończyło. To nie miało tak być..."},
        {"speaker": None,
         "text": "Wracacie po cichu na piechotę. Każdy w swoją stronę. "
                 "Pierwsza raz odkąd jesteście ekipą — czujesz że jest coś nie tak.",
         "_set": {"day7_done": 1}},
    ],

    # ── DZIEŃ 8 — WYKŁAD + NOTATKI KUZYNA SZYMONA ───────────────────────────
    8: [
        {"id": "day8_start", "speaker": None, "text": "Dzień 8"},
        {"speaker": None,
         "text": "Sala wykładowa. 9:45. Profesor monotonnie czyta z slajdów "
                 "o granicach funkcji."},
        {"speaker": None,
         "text": "Połowa sali śpi. Friki rysuje w zeszycie penisy. Światas otwiera "
                 "i zamyka oczy w przypadkowych odstępach."},
        {"speaker": None, "text": "I wtedy Dima podnosi rękę."},
        {"speaker": "Profesor", "text": "Tak, kolego?"},
        {"speaker": "Dima",
         "text": "Panie profesorze, mam pytanie. Czy uważa pan że granica funkcji "
                 "to metafora życia?"},
        {"speaker": "Profesor",
         "text": "Eee... panie kolego, nie do końca rozumiem do czego pan zmierza..."},
        {"speaker": "Dima",
         "text": "No bo wie pan, granica istnieje, ale nigdy się jej nie osiąga. "
                 "Tak jak Fordon w Bydgoszczy."},
        {"speaker": None, "text": "Sala wybucha śmiechem.", "effect": "shake"},
        {"speaker": "Profesor",
         "text": "Panie kolego, proszę się skupić na temacie wykładu."},
        {"speaker": "Dima", "text": "Skupiam się, panie profesorze. Na Fordonie."},
        {"speaker": None,
         "text": "Profesor czerwienieje. Sala nadal się śmieje. Friki "
                 "płacze ze śmiechu."},

        # — Kamil ratuje —
        {"speaker": "Kamil",
         "text": "Panie profesorze, w nawiązaniu — czy w punkcie nieciągłości "
                 "pierwszego rodzaju granica jest dobrze określona, czy "
                 "musimy rozważyć granice jednostronne?"},
        {"speaker": None,
         "text": "Profesor zmiękczy. Wraca do tematu. Kamil mrugnął do Dimy. "
                 "Dima skinął głową z uznaniem.",
         "_rep_add": {"kamil": 2, "dima": 1}},

        # — Po wykładzie SMS od kuzyna Szymona —
        {"speaker": None,
         "text": "Po wykładzie ekipa zbiera się w korytarzu. Szymon ma minę "
                 "jak by wygrał LOTTO."},
        {"speaker": "Szymon",
         "text": "Chłopaki. Dostałem SMS od kuzyna z UKW. On zdawał tego samego "
                 "profesora dwa lata temu. Ma WSZYSTKIE notatki.",
         "image": "szymon_happy.png"},
        {"speaker": "Friki",
         "text": "Pecik. PECIK. Ty wiesz że ja cię kocham? Mogę cię całować w policzek?"},
        {"speaker": "Juras",
         "text": "Friki, dystans. Pecik — dzielisz się, no nie?"},
        {"speaker": "Nataniel",
         "text": "Pecik, ratuj. Jutro mamy ostatni egzamin, ja nic nie umiem."},
        {"speaker": "Kamil",
         "text": "Pecik, fajnie. Jak dasz mi też, to ja wam jeszcze tłumaczę co jest co."},
        {"speaker": None, "text": "Co mówisz Szymonowi?",
         "choices": [
             {"label": "Pecik, podziel się — każdy zda razem.", "next": "notes_share_all"},
             {"label": "Pecik, daj tylko mi, oszczędzimy konkurencji.","next": "notes_share_me"},
             {"label": "Pecik, twoja decyzja.",                  "next": "notes_share_szymon"},
         ]},

        {"id": "notes_share_all", "speaker": "Szymon",
         "text": "Jasne! No oczywiście że się dziele. Po to mam was, chłopaki.",
         "image": "szymon_happy.png",
         "_rep_add": {"szymon": 4, "kamil": 2, "nataniel": 2, "juras": 2, "friki": 2},
         "_set": {"notes_shared": 1},
         "_goto": "day8_end"},

        {"id": "notes_share_me", "speaker": "Szymon",
         "text": "Eee... {mojeimie}, naprawdę? Chłopaki nas potrzebują...",
         "image": "szymon_neutral.png",
         "_rep_add": {"szymon": -6, "kamil": -2, "nataniel": -2, "juras": -2, "friki": -3}},
        {"speaker": "Szymon",
         "text": "Nie, dzielę się z wszystkimi. Sorry {mojeimie}, ale tak nie robimy.",
         "image": "szymon_neutral.png",
         "_set": {"notes_shared": 1},
         "_goto": "day8_end"},

        {"id": "notes_share_szymon", "speaker": "Szymon",
         "text": "Dzielę się z wszystkimi, jasne. Po to są kumple.",
         "image": "szymon_happy.png",
         "_rep_add": {"szymon": 1},
         "_set": {"notes_shared": 1}},

        {"id": "day8_end", "speaker": None,
         "text": "Wieczorem Szymon wysłał PDF na grupę. 87 stron skanowanych notatek. "
                 "Cała ekipa siedzi do 3 w nocy, każdy w swoim mieszkaniu, ucząc się.",
         "_set": {"day8_done": 1}},
    ],

    # ── DZIEŃ 9 — EGZAMIN (CLIMAX) ──────────────────────────────────────────
    9: [
        {"id": "day9_start", "speaker": None, "text": "Dzień 9"},
        {"speaker": None,
         "text": "Rano. 7:50. Sala 312. Wszyscy stoją pod drzwiami, nerwowi, "
                 "przeglądają jeszcze raz notatki Szymona."},
        {"speaker": "Friki",
         "text": "{mojeimie}, ja czuję że zaraz zwymiotuję. Powiedz mi że to nie boli."},
        {"speaker": "Juras",
         "text": "Friki, spokojnie. Trzy oddechy. Jak nie umiesz to zostawiasz, "
                 "lecisz dalej."},
        {"speaker": "Kamil",
         "text": "Spokojnie wszyscy. Notatki Pecika są wystarczające. Tylko myślcie."},
        {"speaker": "Światas",
         "text": "Eee... ja jeszcze pamiętam żeby się obudzić, to dobrze, nie?"},
        {"speaker": "Dima",
         "text": "Egzamin to nie sprawdzenie wiedzy. To sprawdzenie czy jesteś "
                 "obecny w tej chwili. Lecimy."},
        {"speaker": "Szymon",
         "text": "Trzymajcie się chłopaki. Wszyscy zdamy.",
         "image": "szymon_happy.png"},

        # — Egzamin —
        {"speaker": None,
         "text": "8:00. Wchodzicie. Profesor rozdaje arkusze. 5 zadań. 90 minut."},
        {"speaker": "Profesor", "text": "Czas: 90 minut. Powodzenia."},
        {"speaker": None,
         "text": "Piszesz. Idzie. Notatki Pecika ratują tyłek — pierwsze trzy "
                 "zadania znasz."},
        {"speaker": None,
         "text": "Rozglądasz się po sali. Szymon pisze pewnie, uśmiecha się "
                 "do kartki. Światas śpi z otwartymi oczami. Dima patrzy w sufit "
                 "(filozofuje)."},
        {"speaker": None,
         "text": "Nataniel pisze normalnie. Kamil już skończył w połowie czasu — "
                 "oddał, wyszedł, dyskretnie kiwając do wszystkich."},
        {"speaker": None,
         "text": "I wtedy odwraca się do ciebie Friki. Oczy jak u psa porzuconego "
                 "na wsi. Szepcze:"},
        {"speaker": "Friki", "text": "{mojeimie}... błagam... zadanie 4..."},
        {"speaker": None,
         "text": "W tej samej chwili z drugiej strony Juras patrzy na ciebie. "
                 "Spokojny ale błagalny. Kiwa głową — on też potrzebuje."},
        {"speaker": None,
         "text": "Profesor odwrócony do tablicy. Masz 10 sekund."},
        {"speaker": None, "text": "Komu podpowiesz?",
         "choices": [
             {"label": "Frikiemu (Juras nie zda)",  "next": "exam_help_friki"},
             {"label": "Jurasowi (Friki nie zda)", "next": "exam_help_juras"},
             {"label": "Nikomu — niech sami sobie radzą.", "next": "exam_help_none"},
             {"label": "Spróbuję pomóc obu.",       "next": "exam_help_both"},
         ]},

        # — Branch: pomagasz Frikiemu —
        {"id": "exam_help_friki", "speaker": None,
         "text": "Wyciągasz kartkę z odpowiedziami. Friki kopiuje błyskawicznie. "
                 "Juras to widzi. Spuszcza wzrok i zaczyna pisać byle co."},
        {"speaker": None,
         "text": "Egzamin się kończy. Oddajecie kartki. Wychodzicie."},
        {"speaker": "Friki",
         "text": "{mojeimie}, kurwa, jesteś moim BOGIEM. Dziękuję ci. Słowo daję, "
                 "od dziś jestem twoim psem.",
         "_rep_add": {"friki": 8}},
        {"speaker": "Juras",
         "text": "{mojeimie}. Widziałem. Rozumiem. Nikt komu nie jest dłużny.",
         "_rep_add": {"juras": -7}},
        {"speaker": None,
         "text": "Tydzień później wyniki: Friki zdał na 3, Juras nie zdał. "
                 "Juras musi powtarzać przedmiot.",
         "_set": {"exam_winner": "friki"},
         "_goto": "exam_aftermath"},

        # — Branch: pomagasz Jurasowi —
        {"id": "exam_help_juras", "speaker": None,
         "text": "Spojrzeniem dajesz znak Jurasowi. Pokazujesz mu kartkę. "
                 "Juras notuje błyskawicznie i odwraca się z powrotem. "
                 "Friki widzi to. Zamarł."},
        {"speaker": None, "text": "Egzamin się kończy. Wszyscy wychodzą."},
        {"speaker": "Juras",
         "text": "{mojeimie}, dziękuję. Naprawdę. Wiem co to znaczyło. "
                 "Jestem ci to winien.",
         "_rep_add": {"juras": 8}},
        {"speaker": "Friki",
         "text": "{mojeimie}... dlaczego jemu? Czemu nie mi? Ja jestem twoim ziomkiem...",
         "_rep_add": {"friki": -7}},
        {"speaker": None,
         "text": "Tydzień później wyniki: Juras zdał na 4, Friki nie zdał. "
                 "Friki musi powtarzać przedmiot.",
         "_set": {"exam_winner": "juras"},
         "_goto": "exam_aftermath"},

        # — Branch: nikomu —
        {"id": "exam_help_none", "speaker": None,
         "text": "Wzruszasz ramionami w obie strony. Friki opadają ramiona. "
                 "Juras kiwa głową — rozumie."},
        {"speaker": None, "text": "Egzamin się kończy. Oddajecie. Wychodzicie."},
        {"speaker": "Friki", "text": "{mojeimie}... no okej. Sam zawaliłem. Nie ma sprawy.",
         "_rep_add": {"friki": -2}},
        {"speaker": "Juras",
         "text": "{mojeimie}, szanuję. Każdy odpowiada za siebie. To dorosła decyzja.",
         "_rep_add": {"juras": 3}},
        {"speaker": None,
         "text": "Tydzień później wyniki: Friki nie zdał. Juras nie zdał. "
                 "Obaj powtarzają przedmiot, ale nikt nie ma do ciebie żalu.",
         "_set": {"exam_winner": "nobody"},
         "_goto": "exam_aftermath"},

        # — Branch: próbujesz obu —
        {"id": "exam_help_both", "speaker": None,
         "text": "Pokazujesz kartkę raz w lewo, raz w prawo. Niezgrabnie. Głośno."},
        {"speaker": None,
         "text": "Profesor odwraca głowę. Patrzy. Patrzy na ciebie. Wstaje.",
         "effect": "shake"},
        {"speaker": "Profesor",
         "text": "Pan kolega. Proszę o kartkę. I proszę wyjść."},
        {"speaker": None,
         "text": "Twoja kartka idzie do kosza. Friki i Juras zostają sami z zadaniem 4."},
        {"speaker": None,
         "text": "Tydzień później wyniki: TY nie zdałeś (zostałeś zdyskwalifikowany), "
                 "Friki nie zdał, Juras zdał na 3 z resztek własnego rozumu.",
         "_rep_add": {"friki": -5, "juras": 1},
         "_set": {"exam_winner": "disaster"},
         "_goto": "exam_aftermath"},

        # — Aftermath wspólne —
        {"id": "exam_aftermath", "speaker": None,
         "text": "Wieczorem ekipa zbiera się w pubie pod uczelnią. Pijecie. Mało gadacie."},
        {"speaker": "Szymon",
         "text": "{mojeimie}, każdy zrobił co mógł. Ważne że jesteśmy razem.",
         "image": "szymon_happy.png"},
        {"speaker": "Kamil",
         "text": "Egzamin to tylko egzamin. Wiedza zostanie. Sesja minie. "
                 "Pomyślcie o lecie."},
        {"speaker": "Dima",
         "text": "Wiecie że sesja w studenckim życiu to jak Fordon w Bydgoszczy? "
                 "Bardzo intensywna. I też nikt nie wie po co."},
        {"speaker": "Światas", "text": "Dima... ja cię kurwa kocham."},
        {"speaker": None,
         "text": "Wieczór się kończy. Wracasz do domu sam, klucze w dłoni. "
                 "Reflektujesz nad tym co się stało.",
         "_branch_rep": {"char": "szymon",
                         "thresholds": [(15, "day2115")],
                         "default": "end_story"}},
    ],

    # ── DZIEŃ 2115 — SECRET (Bedoes concert) ────────────────────────────────
    2115: [
        {"id": "day2115", "speaker": None,
         "text": "Dzień 2115", "effect": "flash"},
        {"speaker": None,
         "text": "Minęły lata... ale niektóre rzeczy się nie zmieniają."},
        {"speaker": None,
         "text": "Cała wasza grupa z wydziału zebrała się dzisiaj na koncert Bedoesa. "
                 "Nate, Juras, Friki, Krystian, Maciej Reszka, ekipka KKK — "
                 "nawet Dima gdzieś tam się przewinął."},
        {"speaker": None,
         "text": "Stoicie na trybunach. Szymon obok ciebie, w oczach iskry — "
                 "jak u dziecka w sklepie ze słodyczami."},
        {"speaker": None,
         "text": "Bedoes pojawia się na scenie. Stadion eksploduje."},
        {"speaker": None,
         "text": "Pierwsze takty 'Choć nie widać na zewnątrz'. "
                 "Tłum zna każde słowo na pamięć."},
        {"speaker": None,
         "text": "Szymon... Szymon śpiewa z całego serca. Każde słowo, każdą nutę, "
                 "każdy oddech wkłada w te wersy."},
        {"speaker": None,
         "text": "Łzy spływają mu po policzkach. Ale to nie smutek — to euforia."},
        {"speaker": None,
         "text": "I nagle Bedoes się zatrzymuje. Patrzy w tłum. Patrzy bardzo, bardzo długo."},
        {"speaker": None,
         "text": "Wskazuje palcem prosto na Szymona."},
        {"speaker": "Bedoes",
         "text": "TY! TAM, NA TRYBUNACH, W BIAŁEJ KOSZULCE! CHODŹ DO MNIE!"},
        {"speaker": None,
         "text": "Szymon zaskoczony pokazuje na siebie. Bedoes kiwa głową — TAK, TY."},
        {"speaker": None,
         "text": "Cały stadion zaczyna skandować: SZY-MON! SZY-MON! SZY-MON!",
         "effect": "shake"},
        {"speaker": None,
         "text": "Ochrona prowadzi Szymona na scenę. Reflektory go zalewają. "
                 "Bedoes podaje mu mikrofon.",
         "image": "szymon_bedoes_scena.png"},
        {"speaker": "Bedoes",
         "text": "Brachu, śpiewałeś z takim ogniem że nie miałem wyjścia. "
                 "Lecimy razem. Refren.",
         "image": "szymon_bedoes_scena.png"},
        {"speaker": None,
         "text": "Muzyka rusza znowu. Wy dwaj na scenie. Mikrofon w środku.",
         "image": "szymon_bedoes_scena.png"},
        {"speaker": None,
         "text": "'Choć nie widać na zewnątrz, w środku jestem zniszczony...'",
         "image": "szymon_bedoes_scena.png"},
        {"speaker": None,
         "text": "Tysiące głosów krzyczą z wami. Stadion drży. Szymon śpiewa "
                 "tak jakby od tego zależało jego życie.",
         "image": "szymon_bedoes_scena.png"},
        {"speaker": None,
         "text": "Po ostatniej nucie zapada cisza. Absolutna, święta cisza.",
         "image": "szymon_bedoes_scena.png"},
        {"speaker": None,
         "text": "Bedoes patrzy na Szymona. Szymon patrzy na Bedoesa. "
                 "Czas się zatrzymuje.",
         "image": "szymon_bedoes_scena.png"},
        {"speaker": None,
         "text": "I nagle... pocałunek. Na oczach 30 tysięcy ludzi.",
         "effect": "flash",
         "image": "szymon_bedoes_pocalunek.png"},
        {"speaker": None,
         "text": "Stadion eksploduje krzykiem. Telefony unoszą się w górę. "
                 "Każda twarz patrzy na scenę.",
         "image": "szymon_bedoes_scena.png"},
        {"speaker": None,
         "text": "Wśród tłumu ty stoisz nieruchomo. Szymon — którego znałeś "
                 "od pierwszego dnia studiów — całuje swojego idola.",
         "image": "szymon_bedoes_scena.png"},
        {"speaker": None,
         "text": "Twoje serce pęka. Ale jednocześnie... cieszysz się za niego. "
                 "Bo widzisz na jego twarzy to czego nigdy nie widziałeś wcześniej.",
         "image": "szymon_bedoes_scena.png"},
        {"speaker": None,
         "text": "Bo zawsze wiedziałeś — Szymon był wart więcej niż tylko ty.",
         "image": "szymon_bedoes_scena.png"},
        {"speaker": None,
         "text": "— PRAWDZIWY KONIEC —", "effect": "flash",
         "_goto": "end_story"},
    ],

    # ── META: koniec / game over ────────────────────────────────────────────
    99: [
        {"id": "end_story", "speaker": None,
         "text": "— Koniec dostępnej fabuły —\n\n"
                 "Dziękujemy za grę!", "_goto": "title_loop"},
        {"id": "true_game_over", "speaker": None,
         "text": "Dziękujemy za grę.\n\nDo zobaczenia.",
         "_goto": "title_loop"},
        {"id": "title_loop", "speaker": None, "text": "", "_goto": None},
    ],
}


def _build_scenes():
    """Spłaszcza SCENES_BY_DAY do listy i buduje mapę etykiet.

    Kolejność dni w płaskiej liście SCENES:
        0    -> meta (tylko title)
        1    -> Dzień 1
        2    -> Dzień 2 (biblioteka, kawka, ścieżka odmowy)
        3    -> Dzień 3 (Friki/Nate/Juras/Dima)
        4    -> Dzień 4 (Point club)
        5    -> Dzień 5 (stołówka — wprowadzenie Nataniela + Kamila)
        6    -> Dzień 6 (wycieczka do Ustki, drama z wędką Kamila)
        7    -> Dzień 7 (impreza u Frikiego, zarysowany Passat)
        8    -> Dzień 8 (wykład, Dima filozofuje, notatki Szymona)
        9    -> Dzień 9 (egzamin — wybór Friki vs Juras)
        2115 -> SEKRETNY dzień (koncert Bedoesa)
        99   -> meta końca (end_story, game_over, true_game_over)

    Zwraca: (lista_scen, dict_etykiet)
    """
    flat = []
    labels = {}
    for day_key in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 2115, 99):
        for scene in SCENES_BY_DAY[day_key]:
            sid = scene.get("id")
            if sid:
                if sid in labels:
                    raise ValueError(f"Zduplikowana etykieta sceny: {sid!r}")
                labels[sid] = len(flat)
            flat.append(scene)
    return flat, labels


SCENES, LABELS = _build_scenes()


def _resolve_target(target):
    """Konwertuje cel skoku (label-string lub int) na indeks w SCENES.

    Zwraca None jeśli target jest None lub etykieta nie istnieje
    (None = koniec gry / brak skoku).
    """
    if target is None:
        return None
    if isinstance(target, int):
        return target
    return LABELS.get(target)


SAVE_FILE   = "savegame.json"
CONFIG_FILE = "config.json"

# ══════════════════════════════════════════════
#  MUZYKA / KONFIGURACJA
# ══════════════════════════════════════════════
def _load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_config(data):
    try:
        cfg = _load_config()
        cfg.update(data)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False)
    except Exception:
        pass

_cfg = _load_config()
MUSIC_VOLUME = _cfg.get("volume", 0.5)


def _mixer_ok():
    return PYGAME_OK


def _music_play(filename, loop=True, fade_ms=1500):
    if not _mixer_ok():
        return
    path = os.path.join(os.getcwd(), filename)
    if not os.path.exists(path):
        return
    try:
        busy = pygame.mixer.music.get_busy()
        if busy:
            return
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(0)
        pygame.mixer.music.play(-1 if loop else 0)
    except Exception as e:
        print(f"[muzyka] {e}")


def _music_volume(vol):
    if not _mixer_ok():
        return
    try:
        pygame.mixer.music.set_volume(max(0.0, min(1.0, vol)))
    except Exception:
        pass


def _music_stop():
    if not _mixer_ok():
        return
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass


def _music_set_volume(vol):
    global MUSIC_VOLUME
    MUSIC_VOLUME = max(0.0, min(1.0, vol))
    _music_volume(MUSIC_VOLUME)


# ══════════════════════════════════════════════
#  EKRAN SPLASH
# ══════════════════════════════════════════════
class SplashScreen:
    def __init__(self, root, on_done):
        self.root = root
        self.on_done = on_done
        self.root.configure(bg="black")
        self.canvas = tk.Canvas(root, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self._orig_img = None
        self._sized_cache = None
        self._alpha = 0
        self._phase = "in"
        self.root.after(200, self._load)

    def _load(self):
        if not PIL_OK:
            self.on_done(); return
        try:
            self._orig_img = Image.open("logo.jpeg").convert("RGB")
            self._tick()
        except Exception:
            self.on_done()

    def _get_img(self):
        self.root.update_idletasks()
        cw = self.root.winfo_width() or 960
        ch = self.root.winfo_height() or 640
        key = (cw, ch)
        if self._sized_cache is None or self._sized_cache[0] != key:
            img = self._orig_img.resize((cw, ch), Image.BILINEAR)
            self._sized_cache = (key, img)
        return self._sized_cache[1]

    def _tick(self):
        if self._phase == "in":
            self._alpha = min(255, self._alpha + 15)
            self._draw()
            if self._alpha >= 255:
                self._phase = "hold"
                self.root.after(1200, self._tick)
            else:
                self.root.after(30, self._tick)
        elif self._phase == "hold":
            self._phase = "out"
            self.root.after(30, self._tick)
        elif self._phase == "out":
            self._alpha = max(0, self._alpha - 15)
            self._draw()
            if self._alpha <= 0:
                self.canvas.destroy()
                self.on_done()
            else:
                self.root.after(30, self._tick)

    def _draw(self):
        img = self._get_img()
        if self._alpha < 255:
            from PIL import ImageEnhance
            img = ImageEnhance.Brightness(img).enhance(self._alpha / 255.0)
        photo = ImageTk.PhotoImage(img)
        cw = self.root.winfo_width() or 960
        ch = self.root.winfo_height() or 640
        self.canvas.delete("all")
        self.canvas.create_image(cw // 2, ch // 2, image=photo, anchor="center")
        self.canvas.image = photo


# ══════════════════════════════════════════════
#  MENU GŁÓWNE
# ══════════════════════════════════════════════
class MainMenu:
    def __init__(self, root, on_new, on_load, save_exists):
        self.root = root
        self.frame = tk.Frame(root, bg=BG_COLOR)
        self.frame.pack(fill=tk.BOTH, expand=True)

        fn_title = tkfont.Font(family="Georgia", size=32, weight="bold")
        fn_btn   = tkfont.Font(family="Courier", size=13, weight="bold")

        center = tk.Frame(self.frame, bg=BG_COLOR)
        center.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(center, text="COLLEGE WITH SZYMON",
                 font=fn_title, fg=ACCENT, bg=BG_COLOR).pack(pady=(0, 40))

        self._btn(center, "▶  NOWA GRA",     fn_btn, on_new)
        if save_exists:
            self._btn(center, "↺  WCZYTAJ GRĘ", fn_btn, on_load)
        self._btn(center, "⚙  USTAWIENIA",   fn_btn, self._settings)
        self._btn(center, "✕  WYJŚCIE", fn_btn, self._exit)

        _music_play("menu_music.mp3")
        self._fadein_menu()

    def _exit(self):
        _music_stop()
        if PYGAME_OK:
            try:
                pygame.mixer.quit()
            except Exception:
                pass
        self.root.destroy()

    def _fadein_menu(self, steps=25, delay=40, current=0):
        current += MUSIC_VOLUME / steps
        if current >= MUSIC_VOLUME:
            _music_volume(MUSIC_VOLUME)
            return
        _music_volume(current)
        self.root.after(delay, lambda: self._fadein_menu(steps, delay, current))

    def _settings(self):
        if hasattr(self, '_set_overlay') and self._set_overlay:
            self._set_overlay.destroy()
            self._set_overlay = None
            return

        ov = tk.Frame(self.frame, bg=BG_COLOR,
                      highlightbackground=ACCENT, highlightthickness=1)
        ov.place(relx=0.5, rely=0.5, anchor="center", width=320, height=290)
        self._set_overlay = ov

        fn     = tkfont.Font(family="Courier", size=10, weight="bold")
        fn_t   = tkfont.Font(family="Georgia", size=14, weight="bold")
        fn_big = tkfont.Font(family="Courier", size=13, weight="bold")

        tk.Frame(ov, bg=ACCENT, height=2).pack(fill=tk.X)
        tk.Label(ov, text="USTAWIENIA", font=fn_t,
                 fg=ACCENT, bg=BG_COLOR).pack(pady=(14, 8))
        tk.Frame(ov, bg=BORDER, height=1).pack(fill=tk.X, padx=20, pady=(0, 8))

        tk.Label(ov, text="GŁOŚNOŚĆ MUZYKI", font=fn,
                 fg=DIM, bg=BG_COLOR).pack(pady=(0, 6))

        vol_frame = tk.Frame(ov, bg=BG_COLOR)
        vol_frame.pack(pady=(0, 8))

        bar_canvas = tk.Canvas(vol_frame, width=120, height=14,
                               bg=PANEL_COLOR, highlightthickness=0)

        def draw_bar(vol_pct):
            bar_canvas.delete("all")
            fill_w = int(120 * vol_pct / 100)
            bar_canvas.create_rectangle(0, 0, 120, 14, fill=PANEL_COLOR, outline="")
            bar_canvas.create_rectangle(0, 0, fill_w, 14, fill=ACCENT, outline="")

        def change_vol(delta):
            new_vol = max(0, min(100, int(MUSIC_VOLUME * 100) + delta))
            _music_set_volume(new_vol / 100)
            draw_bar(new_vol)

        tk.Button(vol_frame, text="◀", font=fn_big,
                  fg=TEXT_COLOR, bg=PANEL_COLOR,
                  activeforeground=ACCENT, activebackground="#1a1a28",
                  relief="flat", cursor="hand2", padx=10, pady=2,
                  command=lambda: change_vol(-10)).pack(side=tk.LEFT, padx=4)
        bar_canvas.pack(side=tk.LEFT, padx=4)
        tk.Button(vol_frame, text="▶", font=fn_big,
                  fg=TEXT_COLOR, bg=PANEL_COLOR,
                  activeforeground=ACCENT, activebackground="#1a1a28",
                  relief="flat", cursor="hand2", padx=10, pady=2,
                  command=lambda: change_vol(10)).pack(side=tk.LEFT, padx=4)

        draw_bar(int(MUSIC_VOLUME * 100))

        tk.Frame(ov, bg=BORDER, height=1).pack(fill=tk.X, padx=20, pady=(6, 6))

        tk.Label(ov, text="TRYB WYŚWIETLANIA", font=fn,
                 fg=DIM, bg=BG_COLOR).pack(pady=(0, 6))
        mode_frame = tk.Frame(ov, bg=BG_COLOR)
        mode_frame.pack(pady=(0, 8))
        is_fs = self.root.attributes("-fullscreen")

        def set_mode(fullscreen):
            self.root.attributes("-fullscreen", fullscreen)
            ov.destroy()
            setattr(self, '_set_overlay', None)
            self._settings()

        fb1 = tk.Frame(mode_frame, bg=ACCENT if is_fs else BORDER, pady=1)
        fb1.pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(fb1, text="PEŁNY EKRAN", font=fn,
                  fg=BG_COLOR if is_fs else TEXT_COLOR,
                  bg=ACCENT if is_fs else PANEL_COLOR,
                  activeforeground=BG_COLOR, activebackground=ACCENT,
                  relief="flat", cursor="hand2", padx=10, pady=6,
                  command=lambda: set_mode(True)).pack()

        fb2 = tk.Frame(mode_frame, bg=ACCENT if not is_fs else BORDER, pady=1)
        fb2.pack(side=tk.LEFT)
        tk.Button(fb2, text="OKNO", font=fn,
                  fg=BG_COLOR if not is_fs else TEXT_COLOR,
                  bg=ACCENT if not is_fs else PANEL_COLOR,
                  activeforeground=BG_COLOR, activebackground=ACCENT,
                  relief="flat", cursor="hand2", padx=10, pady=6,
                  command=lambda: set_mode(False)).pack()

        tk.Frame(ov, bg=BORDER, height=1).pack(fill=tk.X, padx=20, pady=(6, 6))
        row = tk.Frame(ov, bg=BG_COLOR)
        row.pack(fill=tk.X, padx=24, pady=(2, 6))
        f1 = tk.Frame(row, bg=BORDER, pady=1)
        f1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        tk.Button(f1, text="ZAPISZ I WRÓĆ", font=fn, fg=TEXT_COLOR, bg=PANEL_COLOR,
                  activeforeground=ACCENT, activebackground="#1a1a28",
                  relief="flat", cursor="hand2", pady=6,
                  command=lambda: [_save_config({"volume": MUSIC_VOLUME, "fullscreen": bool(self.root.attributes("-fullscreen"))}), ov.destroy(), setattr(self, '_set_overlay', None)]
                  ).pack(fill=tk.X)
        f2 = tk.Frame(row, bg=BORDER, pady=1)
        f2.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        tk.Button(f2, text="← WRÓĆ", font=fn, fg=TEXT_COLOR, bg=PANEL_COLOR,
                  activeforeground=ACCENT, activebackground="#1a1a28",
                  relief="flat", cursor="hand2", pady=6,
                  command=lambda: [ov.destroy(), setattr(self, '_set_overlay', None)]
                  ).pack(fill=tk.X)
        self.root.after(10, lambda: _autosize_frame(ov))

    def _btn(self, parent, text, font, cmd):
        f = tk.Frame(parent, bg=BORDER, pady=1)
        f.pack(fill=tk.X, pady=4)
        b = tk.Button(f, text=text, font=font,
                      fg=TEXT_COLOR, bg=PANEL_COLOR,
                      activeforeground=ACCENT, activebackground="#1a1a28",
                      relief="flat", cursor="hand2", padx=30, pady=10,
                      command=cmd)
        b.pack(fill=tk.X)

    def destroy(self, fadeout=True):
        self.frame.destroy()


# ══════════════════════════════════════════════
#  GRA
# ══════════════════════════════════════════════
class VisualNovel:
    def __init__(self, root):
        self.root = root
        self.root.title("College with Szymon")
        self.root.configure(bg=BG_COLOR)
        self.root.geometry("960x640")
        self.root.minsize(800, 540)

        self.game_vars = {}
        self.scene_idx = 0
        self.typing = False
        self._stop_typing = False
        self.waiting_input = False
        self._ignore_keys = False
        self._scene_image = None
        self._img_cache = {}

        self._fading = False
        self._fade_out_id = None
        self._fade_in_id  = None
        self._fade_to_id  = None
        self._log = []
        self._load_fonts()
        self._build_ui()
        self.root.bind("<Configure>", self._on_resize)
        self.root.bind("<space>",  lambda e: self._click() if not self.waiting_input else None)
        self.root.bind("<Return>", lambda e: self._click() if not self.waiting_input else None)
        self.root.bind("<Escape>", lambda e: self._pause_menu())

        self._fadeout_music(steps=20, delay=40)

    def _load_fonts(self):
        self.font_name = tkfont.Font(family="Georgia", size=14, weight="bold")
        self.font_text = tkfont.Font(family="Georgia", size=12)
        self.font_btn  = tkfont.Font(family="Courier", size=11, weight="bold")

    def _set_text(self, text):
        self.text_label.config(state="normal")
        self.text_label.delete("1.0", tk.END)
        if text:
            self.text_label.insert("1.0", text)
        self.text_label.config(state="disabled")
        self.text_label.yview_moveto(0)

    def _build_ui(self):
        self.char_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.char_frame.pack(fill=tk.BOTH, expand=True)
        self.char_label = tk.Label(self.char_frame, bg=BG_COLOR, fg=DIM)
        self.char_label.pack(expand=True)

        self.text_panel = tk.Frame(self.root, bg=PANEL_COLOR,
                                   highlightbackground=BORDER, highlightthickness=1, height=220)
        self.text_panel.pack(fill=tk.X, side=tk.BOTTOM)
        self.text_panel.pack_propagate(False)

        tk.Frame(self.text_panel, bg=ACCENT, height=2).pack(fill=tk.X)

        self.name_label = tk.Label(self.text_panel, text="", font=self.font_name,
                                   fg=NAME_COLOR, bg=PANEL_COLOR, anchor="w", padx=24, pady=4)
        self.name_label.pack(fill=tk.X)

        self.text_label = tk.Text(self.text_panel, font=self.font_text,
                                  fg=TEXT_COLOR, bg=TEXT_BOX_BG,
                                  wrap=tk.WORD, padx=24, pady=14,
                                  relief="flat", cursor="arrow",
                                  state="disabled", bd=0)
        self.text_label.bind("<MouseWheel>",
                             lambda e: self.text_label.yview_scroll(int(-1*(e.delta/120)), "units"))

        self.bottom_bar = tk.Frame(self.text_panel, bg=PANEL_COLOR)
        self.bottom_bar.pack(fill=tk.X, padx=12, pady=(0, 12), side=tk.BOTTOM)

        self.text_label.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 4))

        self.continue_btn = tk.Label(self.bottom_bar, text="▶  dalej  [spacja]",
                                     font=self.font_btn, fg=DIM, bg=PANEL_COLOR, cursor="hand2")
        self.continue_btn.pack(side=tk.RIGHT)
        self.continue_btn.bind("<Button-1>", lambda e: self._click())

        tk.Label(self.bottom_bar, text="[ESC] menu",
                 font=self.font_btn, fg=DIM, bg=PANEL_COLOR).pack(side=tk.RIGHT, padx=16)

        self.action_frame = tk.Frame(self.bottom_bar, bg=PANEL_COLOR)
        self.action_frame.pack(side=tk.LEFT)

        self.input_entry = tk.Entry(self.action_frame, font=self.font_btn,
                                    fg=TEXT_COLOR, bg="#1c1c2a",
                                    insertbackground=ACCENT, relief="flat", width=22)
        self.ok_btn = tk.Button(self.action_frame, text="OK →", font=self.font_btn,
                                fg=BG_COLOR, bg=ACCENT, relief="flat",
                                cursor="hand2", padx=10, pady=3,
                                command=self._confirm_input)

        self.input_entry.bind("<Return>",   lambda e: self._confirm_input())
        self.input_entry.bind("<KP_Enter>", lambda e: self._confirm_input())
        self.input_entry.bind("<space>",    lambda e: "break")

    def _autosize_overlay(self, ov, pady=24):
        ov.update_idletasks()
        h = ov.winfo_reqheight()
        try:
            ov.place_info()
            ov.place(height=h + pady)
        except Exception:
            pass

    # ── pauza (overlay w oknie) ─────────────────
    def _pause_menu(self):
        if hasattr(self, '_pause_overlay') and self._pause_overlay:
            self._close_pause()
            return

        self._fade_music_to(MUSIC_VOLUME * 0.25, steps=25, delay=25)

        overlay = tk.Frame(self.root, bg=BG_COLOR,
                           highlightbackground=ACCENT, highlightthickness=1)
        overlay.place(relx=0.5, rely=0.42, anchor="center", width=320, height=1)
        self._pause_overlay = overlay
        self._build_pause_main(overlay)

    def _build_pause_main(self, overlay):
        for w in overlay.winfo_children():
            w.destroy()

        fn_title = tkfont.Font(family="Georgia", size=18, weight="bold")
        fn_btn   = tkfont.Font(family="Courier", size=11, weight="bold")

        tk.Frame(overlay, bg=ACCENT, height=2).pack(fill=tk.X)
        tk.Label(overlay, text="PAUZA", font=fn_title,
                 fg=ACCENT, bg=BG_COLOR).pack(pady=(16, 14))
        tk.Frame(overlay, bg=BORDER, height=1).pack(fill=tk.X, padx=24)

        buttons = [
            ("ZAPISZ GRĘ",  self._save_slots_menu),
            ("WCZYTAJ GRĘ", self._load_slots_menu),
            ("DZIENNIK",    self._show_log),
            ("USTAWIENIA",  self._pause_settings),
            ("MENU GŁÓWNE", lambda: [self._close_pause(), self._goto_menu()]),
            ("WRÓĆ DO GRY", self._close_pause),
        ]
        for text, cmd in buttons:
            f = tk.Frame(overlay, bg=BORDER, pady=1)
            f.pack(fill=tk.X, padx=24, pady=4)
            tk.Button(f, text=text, font=fn_btn, fg=TEXT_COLOR, bg=PANEL_COLOR,
                      activeforeground=ACCENT, activebackground="#1a1a28",
                      relief="flat", cursor="hand2", pady=7,
                      command=cmd).pack(fill=tk.X)
        self.root.after(10, lambda: self._autosize_overlay(overlay))

    def _rebuild_pause(self):
        if self._pause_overlay:
            self._build_pause_main(self._pause_overlay)

    def _show_log(self):
        p = self._pause_overlay
        for w in p.winfo_children(): w.destroy()

        fn_t  = tkfont.Font(family="Georgia", size=14, weight="bold")
        fn_sp = tkfont.Font(family="Courier", size=9, weight="bold")
        fn_tx = tkfont.Font(family="Georgia", size=10)

        tk.Frame(p, bg=ACCENT, height=2).pack(fill=tk.X)
        tk.Label(p, text="DZIENNIK", font=fn_t,
                 fg=ACCENT, bg=BG_COLOR).pack(pady=(12, 6))
        tk.Frame(p, bg=BORDER, height=1).pack(fill=tk.X, padx=20, pady=(0, 6))

        container = tk.Frame(p, bg=BG_COLOR)
        container.pack(fill=tk.BOTH, expand=True, padx=12)

        canvas = tk.Canvas(container, bg=BG_COLOR, highlightthickness=0, height=260)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview,
                                 bg=PANEL_COLOR, troughcolor=BG_COLOR,
                                 activebackground=ACCENT, width=8)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inner = tk.Frame(canvas, bg=BG_COLOR)
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_resize(e):
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())

        canvas.bind("<Configure>", on_resize)

        entries = self._log[-30:]
        if not entries:
            tk.Label(inner, text="Brak historii.", font=fn_tx,
                     fg=DIM, bg=BG_COLOR, wraplength=260).pack(pady=10)
        else:
            for speaker, text in entries:
                frame = tk.Frame(inner, bg=BG_COLOR)
                frame.pack(fill=tk.X, pady=(0, 8))
                if speaker:
                    tk.Label(frame, text=speaker.upper(), font=fn_sp,
                             fg=ACCENT, bg=BG_COLOR, anchor="w").pack(fill=tk.X)
                tk.Label(frame, text=text, font=fn_tx,
                         fg=TEXT_COLOR, bg=BG_COLOR,
                         wraplength=260, justify=tk.LEFT, anchor="w").pack(fill=tk.X)

        inner.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.yview_moveto(1.0)

        def _scroll(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")

        def _bind_scroll(widget):
            widget.bind("<MouseWheel>", _scroll)
            for child in widget.winfo_children():
                _bind_scroll(child)

        _bind_scroll(canvas)
        _bind_scroll(inner)

        tk.Frame(p, bg=BORDER, height=1).pack(fill=tk.X, padx=20, pady=(6, 4))
        fn2 = tkfont.Font(family="Courier", size=10, weight="bold")
        f = tk.Frame(p, bg=BORDER, pady=1)
        f.pack(fill=tk.X, padx=24, pady=(0, 8))
        tk.Button(f, text="← WRÓĆ", font=fn2, fg=TEXT_COLOR, bg=PANEL_COLOR,
                  activeforeground=ACCENT, activebackground="#1a1a28",
                  relief="flat", cursor="hand2", pady=6,
                  command=self._rebuild_pause).pack(fill=tk.X)
        p.place(height=420)

    def _overlay_header(self, parent, title):
        tk.Frame(parent, bg=ACCENT, height=2).pack(fill=tk.X)
        tk.Label(parent, text=title,
                 font=tkfont.Font(family="Georgia", size=14, weight="bold"),
                 fg=ACCENT, bg=BG_COLOR).pack(pady=(14, 8))
        tk.Frame(parent, bg=BORDER, height=1).pack(fill=tk.X, padx=20, pady=(0, 8))

    def _overlay_btn(self, parent, text, cmd=None, dim=False):
        fn = tkfont.Font(family="Courier", size=10, weight="bold")
        f = tk.Frame(parent, bg=BORDER, pady=1)
        f.pack(fill=tk.X, padx=24, pady=3)
        if cmd:
            tk.Button(f, text=text, font=fn,
                      fg=TEXT_COLOR, bg=PANEL_COLOR,
                      activeforeground=ACCENT, activebackground="#1a1a28",
                      relief="flat", cursor="hand2", pady=6,
                      command=cmd).pack(fill=tk.X)
        else:
            tk.Label(f, text=text, font=fn,
                     fg=DIM, bg=PANEL_COLOR, pady=7).pack(fill=tk.X)

    def _overlay_sep(self, parent):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill=tk.X, padx=20, pady=(6, 6))

    def _save_slots_menu(self):
        p = self._pause_overlay
        for w in p.winfo_children(): w.destroy()
        self._overlay_header(p, "ZAPISZ GRĘ")
        for i in range(1, 4):
            sf = f"savegame_slot{i}.json"
            exists, info = _slot_info(sf)
            label = f"SLOT {i}  —  {info}"
            self._overlay_btn(p, label, cmd=lambda s=sf: [self._save(s), self._rebuild_pause()])
        self._overlay_sep(p)
        self._overlay_btn(p, "← WRÓĆ", cmd=self._rebuild_pause, dim=True)
        self.root.after(10, lambda: self._autosize_overlay(self._pause_overlay))

    def _load_slots_menu(self):
        p = self._pause_overlay
        for w in p.winfo_children(): w.destroy()
        fn   = tkfont.Font(family="Courier", size=10, weight="bold")
        fn_s = tkfont.Font(family="Courier", size=9)
        self._overlay_header(p, "WCZYTAJ GRĘ")
        for i in range(1, 4):
            sf = f"savegame_slot{i}.json"
            exists, info = _slot_info(sf)
            label = f"SLOT {i}  —  {info}"
            row = tk.Frame(p, bg=BG_COLOR)
            row.pack(fill=tk.X, padx=24, pady=3)
            if exists:
                fb = tk.Frame(row, bg=BORDER, pady=1)
                fb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
                tk.Button(fb, text=label, font=fn,
                          fg=TEXT_COLOR, bg=PANEL_COLOR,
                          activeforeground=ACCENT, activebackground="#1a1a28",
                          relief="flat", pady=6, cursor="hand2",
                          command=lambda s=sf: [self._load(s), self._rebuild_pause()]
                          ).pack(fill=tk.X)
                fd = tk.Frame(row, bg=BORDER, pady=1)
                fd.pack(side=tk.RIGHT)
                tk.Button(fd, text="✕", font=fn_s,
                          fg=ACCENT, bg=PANEL_COLOR,
                          activeforeground=BG_COLOR, activebackground=ACCENT,
                          relief="flat", cursor="hand2", padx=8, pady=6,
                          command=lambda s=sf: [os.remove(s), self._load_slots_menu()]
                          ).pack()
            else:
                fb = tk.Frame(row, bg=BORDER, pady=1)
                fb.pack(fill=tk.X)
                tk.Label(fb, text=label, font=fn,
                         fg=DIM, bg=PANEL_COLOR, pady=7).pack(fill=tk.X)
        self._overlay_sep(p)
        self._overlay_btn(p, "← WRÓĆ", cmd=self._rebuild_pause, dim=True)
        self.root.after(10, lambda: self._autosize_overlay(self._pause_overlay))

    def _pause_settings(self):
        p = self._pause_overlay
        for w in p.winfo_children(): w.destroy()
        fn     = tkfont.Font(family="Courier", size=10, weight="bold")
        fn_big = tkfont.Font(family="Courier", size=13, weight="bold")
        self._overlay_header(p, "USTAWIENIA")

        tk.Label(p, text="GŁOŚNOŚĆ MUZYKI", font=fn,
                 fg=DIM, bg=BG_COLOR).pack(pady=(0, 6))

        vol_frame = tk.Frame(p, bg=BG_COLOR)
        vol_frame.pack(pady=(0, 8))

        bar_canvas = tk.Canvas(vol_frame, width=120, height=14,
                               bg=PANEL_COLOR, highlightthickness=0)

        def draw_bar(vol_pct):
            bar_canvas.delete("all")
            fill_w = int(120 * vol_pct / 100)
            bar_canvas.create_rectangle(0, 0, 120, 14, fill=PANEL_COLOR, outline="")
            bar_canvas.create_rectangle(0, 0, fill_w, 14, fill=ACCENT, outline="")

        def change_vol(delta):
            new_vol = max(0, min(100, int(MUSIC_VOLUME * 100) + delta))
            _music_set_volume(new_vol / 100)
            _music_volume(new_vol / 100 * 0.25)
            draw_bar(new_vol)

        tk.Button(vol_frame, text="◀", font=fn_big,
                  fg=TEXT_COLOR, bg=PANEL_COLOR,
                  activeforeground=ACCENT, activebackground="#1a1a28",
                  relief="flat", cursor="hand2", padx=10, pady=2,
                  command=lambda: change_vol(-10)).pack(side=tk.LEFT, padx=4)
        bar_canvas.pack(side=tk.LEFT, padx=4)
        tk.Button(vol_frame, text="▶", font=fn_big,
                  fg=TEXT_COLOR, bg=PANEL_COLOR,
                  activeforeground=ACCENT, activebackground="#1a1a28",
                  relief="flat", cursor="hand2", padx=10, pady=2,
                  command=lambda: change_vol(10)).pack(side=tk.LEFT, padx=4)

        draw_bar(int(MUSIC_VOLUME * 100))

        self._overlay_sep(p)

        tk.Label(p, text="TRYB WYŚWIETLANIA", font=fn,
                 fg=DIM, bg=BG_COLOR).pack(pady=(0, 6))
        mode_frame = tk.Frame(p, bg=BG_COLOR)
        mode_frame.pack(pady=(0, 8))
        is_fs = self.root.attributes("-fullscreen")

        def set_mode(fullscreen):
            self.root.attributes("-fullscreen", fullscreen)
            self._pause_settings()

        fb1 = tk.Frame(mode_frame, bg=ACCENT if is_fs else BORDER, pady=1)
        fb1.pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(fb1, text="PEŁNY EKRAN", font=fn,
                  fg=BG_COLOR if is_fs else TEXT_COLOR,
                  bg=ACCENT if is_fs else PANEL_COLOR,
                  activeforeground=BG_COLOR, activebackground=ACCENT,
                  relief="flat", cursor="hand2", padx=10, pady=6,
                  command=lambda: set_mode(True)).pack()

        fb2 = tk.Frame(mode_frame, bg=ACCENT if not is_fs else BORDER, pady=1)
        fb2.pack(side=tk.LEFT)
        tk.Button(fb2, text="OKNO", font=fn,
                  fg=BG_COLOR if not is_fs else TEXT_COLOR,
                  bg=ACCENT if not is_fs else PANEL_COLOR,
                  activeforeground=BG_COLOR, activebackground=ACCENT,
                  relief="flat", cursor="hand2", padx=10, pady=6,
                  command=lambda: set_mode(False)).pack()

        self._overlay_sep(p)
        fn2 = tkfont.Font(family="Courier", size=10, weight="bold")
        row = tk.Frame(p, bg=BG_COLOR)
        row.pack(fill=tk.X, padx=24, pady=(2, 6))
        f1 = tk.Frame(row, bg=BORDER, pady=1)
        f1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        tk.Button(f1, text="ZAPISZ I WRÓĆ", font=fn2, fg=TEXT_COLOR, bg=PANEL_COLOR,
                  activeforeground=ACCENT, activebackground="#1a1a28",
                  relief="flat", cursor="hand2", pady=6,
                  command=lambda: [_save_config({"volume": MUSIC_VOLUME, "fullscreen": bool(self.root.attributes("-fullscreen"))}), self._rebuild_pause()]
                  ).pack(fill=tk.X)
        f2 = tk.Frame(row, bg=BORDER, pady=1)
        f2.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        tk.Button(f2, text="← WRÓĆ", font=fn2, fg=TEXT_COLOR, bg=PANEL_COLOR,
                  activeforeground=ACCENT, activebackground="#1a1a28",
                  relief="flat", cursor="hand2", pady=6,
                  command=self._rebuild_pause
                  ).pack(fill=tk.X)
        self.root.after(10, lambda: self._autosize_overlay(self._pause_overlay))

    def _close_pause(self):
        if hasattr(self, '_pause_overlay') and self._pause_overlay:
            self._pause_overlay.destroy()
            self._pause_overlay = None
        self._fade_music_to(0, steps=25, delay=25)

    # ── zapis / wczytanie ──────────────────────
    def _save(self, slot_file=None):
        if slot_file is None:
            slot_file = SAVE_FILE
        day = 1
        for i in range(self.scene_idx + 1):
            txt = SCENES[i].get("text", "")
            if txt.startswith("Dzień "):
                try:
                    day = int(txt.split()[1])
                except Exception:
                    pass
        data = {"scene_idx": self.scene_idx, "game_vars": self.game_vars, "day": day}
        with open(slot_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        self._toast(f"Zapisano slot!")

    def _load(self, slot_file=None):
        if slot_file is None:
            slot_file = SAVE_FILE
        if not os.path.exists(slot_file):
            return
        with open(slot_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.game_vars = data.get("game_vars", {})
        self._show_scene(data.get("scene_idx", 0))


    def _rep_label(self, pts, char=None):
        if pts >= 20: return "❤ ZAKOCHANY"
        if pts >= 14: return "♡ ZAUROCZONY"
        if pts >= 9:  return "♡ ZAINTERESOWANY"
        if pts >= 15: return "PRZYJACIEL"
        if pts >= 8:  return "KOLEGA"
        if pts >= 3:  return "ZNAJOMY"
        if pts >= 0:  return "NEUTRALNY"
        if pts >= -5: return "CHŁODNY"
        if pts >= -10:return "WROGI"
        return "WRÓG"

    def _toast(self, msg):
        t = tk.Label(self.root, text=msg, font=self.font_btn,
                     fg=BG_COLOR, bg=ACCENT, padx=16, pady=6)
        t.place(relx=0.5, rely=0.05, anchor="center")
        self.root.after(3000, t.destroy)

    def _goto_menu(self):
        self._cancel_fades()
        self.root.unbind("<Escape>")
        self.text_panel.pack_forget()
        self.char_frame.pack_forget()
        self._img_cache.clear()
        _music_volume(0)
        app_start(self.root, show_splash=False)

    def _cancel_fades(self):
        self._fading = False
        for attr in ('_fade_out_id', '_fade_in_id', '_fade_to_id'):
            job = getattr(self, attr, None)
            if job:
                try:
                    self.root.after_cancel(job)
                except Exception:
                    pass
            setattr(self, attr, None)

    def _fadeout_music(self, steps=20, delay=40):
        self._cancel_fades()
        self._fading = True
        self._do_fadeout(MUSIC_VOLUME, steps, delay, steps)

    def _do_fadeout(self, start, steps, delay, remaining):
        if not self._fading or remaining <= 0:
            _music_volume(0)
            self._fading = False
            return
        _music_volume(start * remaining / steps)
        self._fade_out_id = self.root.after(
            delay, lambda: self._do_fadeout(start, steps, delay, remaining - 1))

    def _fadein_music(self, steps=20, delay=40):
        self._cancel_fades()
        self._do_fadein(MUSIC_VOLUME, steps, delay, 1)

    def _do_fadein(self, target, steps, delay, done):
        if done >= steps:
            _music_volume(target)
            return
        _music_volume(target * done / steps)
        self._fade_in_id = self.root.after(
            delay, lambda: self._do_fadein(target, steps, delay, done + 1))

    def _fade_music_to(self, target, steps=15, delay=30):
        self._cancel_fades()
        try:
            start = pygame.mixer.music.get_volume() if PYGAME_OK else 0
        except Exception:
            start = 0
        self._do_fade_to(target, start, steps, delay, 1)

    def _do_fade_to(self, target, start, total, delay, done):
        if done >= total:
            _music_volume(target)
            return
        _music_volume(start + (target - start) * done / total)
        self._fade_to_id = self.root.after(
            delay, lambda: self._do_fade_to(target, start, total, delay, done + 1))

    # ── scena ──────────────────────────────────
    def _show_scene(self, idx):
        if idx is None or idx >= len(SCENES) or idx < 0:
            self._end_game()
            return

        self.scene_idx = idx
        scene = SCENES[idx]

        if scene.get("effect") == "flash": self._flash()
        elif scene.get("effect") == "shake": self._shake()
        if "_set" in scene: self.game_vars.update(scene["_set"])
        if "_inc" in scene:
            for k, delta in scene["_inc"].items():
                self.game_vars[k] = self.game_vars.get(k, 0) + delta
        if "_rep_add" in scene:
            names = {"szymon": "Szymon", "swiatas": "Światas",
                     "juras": "Juras", "friki": "Friki", "dima": "Dima",
                     "nataniel": "Nataniel", "kamil": "Kamil"}
            for char, delta in scene["_rep_add"].items():
                key = f"rep_{char}"
                old = self.game_vars.get(key, 0)
                self.game_vars[key] = old + delta
                new = self.game_vars[key]
                label = names.get(char, char.capitalize())
                arrows = ("▲▲" if delta >= 6 else "▲" if delta > 0 else ("▼▼" if delta <= -6 else "▼"))
                rel = self._rep_label(new, char)
                self.root.after(400, lambda l=label, a=arrows, r=rel: self._toast(f"{l}  {a}  {r}"))

        self._set_image(scene.get("image"))

        speaker = (scene.get("speaker") or "")
        if self.game_vars:
            try: speaker = speaker.format(**self.game_vars)
            except KeyError: pass
        self.name_label.config(text=speaker.upper())

        raw = scene.get("text", "")
        try:
            text = raw.format(**self.game_vars) if self.game_vars else raw
        except KeyError:
            text = raw

        if text and not scene.get("input"):
            entry = (speaker, text)
            if not self._log or self._log[-1] != entry:
                self._log.append(entry)
                if len(self._log) > 50:
                    self._log.pop(0)

        self._clear_actions()
        self.continue_btn.config(fg=DIM)

        if scene.get("input"):
            self.waiting_input = True
            self._set_text(text)
            self.continue_btn.pack_forget()
            self.input_entry.delete(0, tk.END)
            self.input_entry.pack(side=tk.LEFT, ipady=4, padx=(0, 6))
            self.ok_btn.pack(side=tk.LEFT)
            self.root.after(100, self.input_entry.focus_force)
        elif scene.get("choices"):
            self.waiting_input = False
            self.continue_btn.pack(side=tk.RIGHT)
            self._type_text(text, done=lambda: self._show_choices(scene["choices"]))
        elif not text and (
                "_goto" in scene or "_branch" in scene or "_branch_rep" in scene
                or "_branch_var" in scene):
            # Niewidoczna scena routingowa — natychmiast skacz dalej
            self.root.after(1, self._advance)
        else:
            self.waiting_input = False
            self.continue_btn.pack(side=tk.RIGHT)
            self._type_text(text, done=lambda: self.continue_btn.config(fg=ACCENT))

    def _clear_actions(self):
        self.input_entry.pack_forget()
        self.ok_btn.pack_forget()
        for w in self.action_frame.winfo_children():
            if w not in (self.input_entry, self.ok_btn):
                w.destroy()

    def _confirm_input(self):
        val = self.input_entry.get().strip()
        if not val:
            self.input_entry.focus_force()
            return
        scene = SCENES[self.scene_idx]
        self.game_vars[scene["input"]] = val
        self.waiting_input = False
        self._ignore_keys = True
        self._clear_actions()
        self.continue_btn.pack(side=tk.RIGHT)
        self.root.focus_set()
        self.root.after(300, self._enable_keys)
        self._advance()

    def _show_choices(self, choices):
        available = []
        for c in choices:
            req = c.get("_req_rep")
            if req:
                char, threshold = req
                pts = self.game_vars.get(f"rep_{char}", 0)
                if pts < threshold:
                    continue
            available.append(c)

        for i, c in enumerate(available):
            btn = tk.Button(self.action_frame, text=f"[{i+1}] {c['label']}", font=self.font_btn,
                            fg=TEXT_COLOR, bg="#1c1c2a",
                            activeforeground=BG_COLOR, activebackground=ACCENT,
                            relief="flat", cursor="hand2", padx=14, pady=4,
                            command=lambda n=c["next"]: self._choose(n))
            btn.pack(side=tk.LEFT, padx=(0, 8))
        for i, c in enumerate(available):
            key = str(i + 1)
            self.root.bind(key, lambda e, n=c["next"]: self._choose(n))

    def _choose(self, next_target):
        for k in "1234":
            try: self.root.unbind(k)
            except Exception: pass
        self._clear_actions()
        self._show_scene(_resolve_target(next_target))

    def _enable_keys(self):
        self._ignore_keys = False

    def _click(self):
        if self._ignore_keys or self.waiting_input:
            return
        if self.typing:
            self._stop_typing = True
            return
        scene = SCENES[self.scene_idx]
        if scene.get("choices") or scene.get("input"):
            return
        self._advance()

    def _advance(self):
        scene = SCENES[self.scene_idx]
        if "_goto" in scene:
            self._show_scene(_resolve_target(scene["_goto"]))
        elif "_branch" in scene:
            branch = scene["_branch"]
            target = branch.get(None)
            for key, next_t in branch.items():
                if key is not None and key in self.game_vars:
                    target = next_t
                    break
            self._show_scene(_resolve_target(target))
        elif "_branch_rep" in scene:
            br = scene["_branch_rep"]
            char = br["char"]
            pts = self.game_vars.get(f"rep_{char}", 0)
            target = br.get("default")
            for threshold, next_t in br["thresholds"]:
                if pts >= threshold:
                    target = next_t
                    break
            self._show_scene(_resolve_target(target))
        elif "_branch_var" in scene:
            bv = scene["_branch_var"]
            var = bv["var"]
            val = self.game_vars.get(var, 0)
            target = bv.get("default")
            for threshold, next_t in bv["thresholds"]:
                if val >= threshold:
                    target = next_t
                    break
            self._show_scene(_resolve_target(target))
        else:
            self._show_scene(self.scene_idx + 1)

    def _type_text(self, text, done=None):
        self.typing = True
        self._stop_typing = False
        self._set_text("")
        self._type_step(text, 0, done)

    def _type_step(self, text, i, done):
        if self._stop_typing:
            self._set_text(text)
            self.typing = False
            self._stop_typing = False
            if done: done()
            return
        if i <= len(text):
            self._set_text(text[:i])
            self.root.after(CHAR_DELAY, lambda: self._type_step(text, i + 1, done))
        else:
            self.typing = False
            if done: done()

    def _on_resize(self, event):
        if event.widget == self.root and self._scene_image:
            self._img_cache.clear()
            self.root.after(100, lambda: self._load_image(self._scene_image))

    def _set_image(self, filename):
        self._scene_image = filename
        self.char_label.config(image="", text="")
        self.char_label.image = None
        if not filename or not PIL_OK:
            return
        path = os.path.join(IMAGES_DIR, filename)
        if not os.path.exists(path):
            self.char_label.config(text=f"[brak: {filename}]")
            return
        self._load_image(filename)

    def _load_image(self, filename):
        if self._scene_image != filename:
            return
        if filename in self._img_cache:
            photo = self._img_cache[filename]
            self.char_label.config(image=photo)
            self.char_label.image = photo
            return
        path = os.path.join(IMAGES_DIR, filename)
        try:
            img = Image.open(path)
            fw = self.char_frame.winfo_width()
            fh = self.char_frame.winfo_height()
            if fw < 10 or fh < 10:
                fw, fh = 960, 420
            iw, ih = img.size
            scale = fw / iw
            new_w, new_h = fw, int(ih * scale)
            if new_h > fh:
                scale = fh / ih
                new_w, new_h = int(iw * scale), fh
            img = img.resize((new_w, new_h), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._img_cache[filename] = photo
            self.char_label.config(image=photo)
            self.char_label.image = photo
        except Exception as ex:
            self.char_label.config(text=f"[błąd: {ex}]")

    def _flash(self):
        def step(n):
            if n < 0:
                self.root.configure(bg=BG_COLOR); return
            self.root.configure(bg="white" if n % 2 == 0 else BG_COLOR)
            self.root.after(55, lambda: step(n - 1))
        step(5)

    def _shake(self):
        x, y = self.root.winfo_x(), self.root.winfo_y()
        offs = [12, -12, 9, -9, 5, -5, 2, -2, 0]
        def step(i):
            if i >= len(offs): return
            self.root.geometry(f"+{x + offs[i]}+{y}")
            self.root.after(28, lambda: step(i + 1))
        step(0)

    def _end_game(self):
        self._set_text("Koniec gry. Dziękujemy za grę!")
        self.name_label.config(text="")
        self._clear_actions()
        self.continue_btn.config(text="MENU GŁÓWNE", fg=ACCENT)
        self.continue_btn.bind("<Button-1>", lambda e: self._goto_menu())


    # ══════════════════════════════════════════════
    #  URUCHAMIANIE
    # ══════════════════════════════════════════════

def _autosize_frame(frame, pady=16):
    try:
        frame.update_idletasks()
        frame.place(height=frame.winfo_reqheight() + pady)
    except Exception:
        pass


def _slot_info(slot_file):
    if not os.path.exists(slot_file):
        return False, "[pusty]"
    try:
        with open(slot_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        day = data.get("day", "?")
        return True, f"Dzień {day}"
    except Exception:
        return True, "[błąd]"


def app_start(root, show_splash=True):
    save_exists = any(os.path.exists(f"savegame_slot{i}.json") for i in range(1, 4)) or os.path.exists(SAVE_FILE)

    def start_menu():
        menu = MainMenu(
            root,
            on_new=lambda: [menu.destroy(fadeout=True), start_game(root)],
            on_load=lambda: show_load_picker(menu),
            save_exists=save_exists,
        )

    def show_load_picker(menu):
        fn_t = tkfont.Font(family="Georgia", size=14, weight="bold")
        fn   = tkfont.Font(family="Courier", size=10, weight="bold")
        ov = tk.Frame(root, bg=BG_COLOR,
                      highlightbackground=ACCENT, highlightthickness=1)
        ov.place(relx=0.5, rely=0.5, anchor="center", width=320, height=290)

        tk.Frame(ov, bg=ACCENT, height=2).pack(fill=tk.X)
        tk.Label(ov, text="WCZYTAJ GRĘ", font=fn_t,
                 fg=ACCENT, bg=BG_COLOR).pack(pady=(14, 8))
        tk.Frame(ov, bg=BORDER, height=1).pack(fill=tk.X, padx=20, pady=(0, 8))

        for i in range(1, 4):
            slot_file = f"savegame_slot{i}.json"
            exists, info = _slot_info(slot_file)
            label = f"SLOT {i}  —  {info}"
            fn_s = tkfont.Font(family="Courier", size=9)
            row = tk.Frame(ov, bg=BG_COLOR)
            row.pack(fill=tk.X, padx=24, pady=3)
            if exists:
                def on_load(s=slot_file):
                    ov.destroy()
                    menu.destroy(fadeout=True)
                    vn = VisualNovel(root)
                    root.vn = vn
                    vn._load(s)
                fb = tk.Frame(row, bg=BORDER, pady=1)
                fb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
                tk.Button(fb, text=label, font=fn,
                          fg=TEXT_COLOR, bg=PANEL_COLOR,
                          activeforeground=ACCENT, activebackground="#1a1a28",
                          relief="flat", pady=6, cursor="hand2",
                          command=on_load).pack(fill=tk.X)
                fd = tk.Frame(row, bg=BORDER, pady=1)
                fd.pack(side=tk.RIGHT)
                tk.Button(fd, text="✕", font=fn_s,
                          fg=ACCENT, bg=PANEL_COLOR,
                          activeforeground=BG_COLOR, activebackground=ACCENT,
                          relief="flat", cursor="hand2", padx=8, pady=6,
                          command=lambda s=slot_file: [os.remove(s), show_load_picker(menu)] if os.path.exists(s) else None
                          ).pack()
            else:
                fb = tk.Frame(row, bg=BORDER, pady=1)
                fb.pack(fill=tk.X)
                tk.Label(fb, text=label, font=fn,
                         fg=DIM, bg=PANEL_COLOR, pady=7).pack(fill=tk.X)

        tk.Frame(ov, bg=BORDER, height=1).pack(fill=tk.X, padx=20, pady=(6, 6))
        f = tk.Frame(ov, bg=BORDER, pady=1)
        f.pack(fill=tk.X, padx=24, pady=3)
        tk.Button(f, text="← WRÓĆ", font=fn, fg=TEXT_COLOR, bg=PANEL_COLOR,
                  activeforeground=ACCENT, relief="flat", cursor="hand2", pady=6,
                  command=ov.destroy).pack(fill=tk.X)
        root.after(10, lambda: _autosize_frame(ov))

    def start_game(r):
        vn = VisualNovel(r)
        root.vn = vn
        vn._show_scene(0)

    if show_splash:
        SplashScreen(root, on_done=start_menu)
    else:
        start_menu()


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("960x640")
    root.configure(bg="black")
    root.title("College with Szymon")
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        try:
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
        except NameError:
            pass

    _cfg = _load_config()
    if _cfg.get("fullscreen", False):
        root.attributes("-fullscreen", True)

    def on_close():
        try:
            if PYGAME_OK:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
        except Exception:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    app_start(root)
    root.mainloop()
