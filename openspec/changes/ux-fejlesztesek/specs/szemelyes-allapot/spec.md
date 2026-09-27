# Spec Delta

## Purpose

Lehetővé teszi, hogy a felhasználó személyesen jelölje kész a feladatokat anélkül, hogy ez más felhasználók nézetét befolyásolná.

## ADDED Requirements

### Requirement: Megcsináltam jelölés

A rendszer SHALL minden feladatkártyán egy pipálható jelölőt megjeleníteni. A jelölés állapota felhasználónként és eszközönként localStorage-ban tárolódik, és nem kerül a Google Sheetsbe.

#### Scenario: Feladat megjelölése kész

- **WHEN** a felhasználó a "✓" jelölőre kattint egy kártyán
- **THEN** a jelölő aktív állapotba kerül, a kártyán látható vizuális visszajelzés (elhalványulás / pipált ikon) jelenik meg, az állapot localStorage-ba mentődik

#### Scenario: Kész feladatok pozíciója a listában

- **WHEN** a feladatlista renderelődik és vannak megjelölt (kész) feladatok
- **THEN** a kész feladatok a lista aljára kerülnek az aktív feladatok után, határidő szerinti rendezésen belül

#### Scenario: Jelölés visszavonása

- **WHEN** a felhasználó egy már kész jelölésű kártyán ismét a jelölőre kattint
- **THEN** a feladat visszakerül az aktív sorba, a localStorage-ból törlődik a jelölés

#### Scenario: Állapot megőrzése

- **WHEN** az oldal frissül vagy újratöltődik
- **THEN** a korábban megjelölt feladatok kész állapota visszaáll
