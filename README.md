# Garage Modbus pour Home Assistant

Intégration Home Assistant du contrôleur de porte de garage **Garage Modbus** (ESP32-S3, carte Waveshare 8DI-8DO, firmware v6), relié en **Modbus RTU** par un pont **LoRa USB** ou un adaptateur **USB-RS485**.

- Ajout par l'interface : **le port USB se choisit dans une liste**, avec saisie manuelle possible.
- Un appareil **Garage** avec toutes ses entités : porte, lampe, bouton Stop, température, humidité, position, radar, pile du bouton Bluetooth, défaut, cellule, palpeur…
- **Une seule lecture groupée** des registres 100 à 108 par cycle : économe pour le LoRa.
- Port, vitesse et esclave modifiables ensuite (*Reconfigurer*), intervalle de lecture dans les *Options*.

## Installation

### Par HACS (dépôt personnalisé)

1. HACS → menu ⋮ → **Dépôts personnalisés**.
2. Adresse : `https://github.com/UltraFlashers/ha-garage-modbus`, catégorie **Intégration**, puis **Ajouter**.
3. Chercher **Garage Modbus** dans HACS, **Télécharger**, puis redémarrer Home Assistant.

### À la main

Copier le dossier `custom_components/garage_modbus` dans `/config/custom_components/`, puis redémarrer Home Assistant.

## Configuration

**Paramètres → Appareils et services → Ajouter une intégration → Garage Modbus**

| Champ | Valeur |
|---|---|
| Port USB | choisi dans la liste des ports détectés (chemin stable `/dev/serial/by-id/…`), ou *Saisir le chemin à la main…* |
| Vitesse | celle réglée sur la page `/config` de la carte, section *Modbus* (9600 par défaut) |
| Numéro d'esclave | 1 par défaut |

Le garage doit répondre pour que l'ajout aboutisse. Ensuite :

- **Reconfigurer** (menu ⋮ de l'intégration) : changer de port USB, de vitesse ou d'esclave ;
- **Options** : intervalle de lecture (5 s par défaut).

Si le garage ne répond plus (LoRa coupé, carte éteinte), l'intégration passe en *nouvel essai* et se reconnecte toute seule.

> Ne pas garder en même temps le package YAML `garage_modbus.yaml` du dépôt firmware : les deux ouvriraient le même port USB. Utiliser l'un **ou** l'autre.

## Entités

| Entité | Source |
|---|---|
| Porte (`cover`) | ouvrir = coil 0 à 1, fermer = coil 0 à 0, stop = coil 5 ; état dans le registre 105, position (estimée) dans le 103 |
| Lampe (`light`) | coil 1 ; état réel : bit 2 du registre 102 |
| Stop (`button`) | coil 5 |
| Température, Humidité | registres 100 et 101 (× 10) ; *inconnu* si la sonde ne répond pas |
| Position | registre 103 |
| Distance radar, Cible radar | registres 106 et 107 ; *inconnu* sans radar |
| Pile du bouton | registre 108, pile la plus basse des boutons Bluetooth |
| État de l'automate (diagnostic) | registre 104 |
| Présence, Défaut, Cellule, Pile du bouton faible, Palpeur | bits 1, 3, 4, 5 et 6 du registre 102 |
| Fin de course ouvert (diagnostic, **désactivée par défaut**) | bit 7 du registre 102 ; à activer dans l'appareil si le contact est câblé sur DI7 de la carte |

Toutes les commandes passent par la machine d'état de la carte et ses sécurités : cellule ou palpeur actifs, la fermeture est refusée ; bouton STOP tenu, rien ne démarre.

## Compatibilité

- Home Assistant **2025.2** ou plus récent.
- Firmware Garage Modbus **v6** (carte des registres 100 à 108, coils 0 à 6).
- `pymodbus` est déjà présent dans Home Assistant (intégration Modbus officielle) ; aucune autre dépendance.

## Développement

```sh
pip install pytest-homeassistant-custom-component pymodbus pyserial aiousbwatcher
python -m pytest -q
```

Les tests montent un **faux garage** : un esclave Modbus RTU pymodbus avec la carte des registres du firmware. L'intégration lui parle avec de vraies trames (porte, lampe, stop, alertes, garage injoignable), et l'assistant de configuration est testé (liste des ports, saisie manuelle, garage muet, doublon, reconfiguration, options).
