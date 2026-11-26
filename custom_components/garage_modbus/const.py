"""Constantes de l'integration Garage Modbus."""

from __future__ import annotations

DOMAIN = "garage_modbus"

CONF_BAUDRATE = "baudrate"
CONF_SLAVE = "slave"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_MANUAL_PATH = "manual_path"

DEFAULT_BAUDRATE = 9600
DEFAULT_SLAVE = 1
DEFAULT_SCAN_INTERVAL = 5  # s : la porte bouge ; une lecture groupee suffit
DEFAULT_TIMEOUT = 5  # s
BAUDRATES = [9600, 19200, 38400, 57600, 115200]

# Carte des registres du firmware v6 (voir le README du firmware)
REG_FIRST = 100  # 100 a 108 lus en une seule requete
REG_COUNT = 9
COIL_DOOR = 0  # 1 = ouvrir, 0 = fermer
COIL_LAMP = 1  # 1 = allumer, 0 = eteindre
COIL_STOP = 5  # 1 = stop (retombe tout seul)

# Bits du registre 102 (etat groupe)
BIT_OPEN = 0
BIT_PRESENCE = 1
BIT_LAMP = 2
BIT_FAULT = 3
BIT_BEAM = 4
BIT_BATTERY_LOW = 5
BIT_SAFETY_EDGE = 6
BIT_OPEN_LIMIT = 7  # fin de course ouvert (optionnel sur la carte)
BIT_VEHICLE = 8  # voiture garee (capteur de vehicule optionnel sur la carte)
BIT_WICKET = 9  # portillon de la porte ouvert (optionnel sur la carte)

# Registre 105 (etat pour le cover)
COVER_CLOSED = 0
COVER_OPEN = 1
COVER_OPENING = 3
COVER_CLOSING = 4

# Registre 104 (etat brut de l'automate)
DOOR_STATES = ["fermee", "ouverte", "arretee", "monte", "descend", "pause"]
# Registre 107 (cible du radar)
RADAR_TARGETS = ["personne", "mouvement", "immobile", "mouvement_immobile"]
