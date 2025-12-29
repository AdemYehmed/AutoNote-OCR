# 📝 Système d'Extraction Automatique de Notes - OCR & Vision par Ordinateur

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)](https://opencv.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Latest-orange.svg)](https://pandas.pydata.org/)

## 🎯 Présentation du Projet

Système intelligent d'extraction automatique de notes à partir de copies d'examens scannées. Le projet utilise des techniques avancées de vision par ordinateur pour détecter, analyser et extraire les notes cochées sur des grilles de notation, puis génère automatiquement un fichier Excel consolidé.

---

## 🔄 Pipeline de Traitement

```
📄 Copies Scannées (JPG)
         ↓
    ┌────────────────────────────┐
    │  1. Détection QR Code      │
    │     & Correction Rotation  │
    └────────────────────────────┘
         ↓
    ┌────────────────────────────┐
    │  2. Extraction ROI         │
    │     (Zone de notation)     │
    └────────────────────────────┘
         ↓
    ┌────────────────────────────┐
    │  3. Prétraitement Image    │
    │     - Seuillage adaptatif  │
    │     - Opérations morpho    │
    └────────────────────────────┘
         ↓
    ┌────────────────────────────┐
    │  4. Détection de Grille    │
    │     - Projections H/V      │
    │     - Segmentation cellules│
    └────────────────────────────┘
         ↓
    ┌────────────────────────────┐
    │  5. Analyse des Cases      │
    │     - Partie entière (0-20)│
    │     - Partie décimale      │
    │       (0.00, 0.25, 0.50,   │
    │        0.75)                │
    └────────────────────────────┘
         ↓
    ┌────────────────────────────┐
    │  6. Génération Excel       │
    │     Notes + Métadonnées    │
    └────────────────────────────┘
         ↓
📊 Fichier Excel (.xlsx)
```

---

## 📥 Entrée (Input)

### Exemple de Copie Scannée
(![anis121125_page-0002](https://github.com/user-attachments/assets/0fa638d4-34c9-4b58-a781-f4eababeb223)

**Format d'entrée :**
- **Type :** Images JPG
- **Nomenclature :** `anis121125_page-XXXX.jpg` (où XXXX = numéro de page)
- **Nombre :** 70 pages
- **Contenu :** Copies d'examens avec grille de notation à cocher
- **Particularité :** QR Code pour correction automatique de l'orientation

---

## 📤 Sortie (Output)

### Exemple de Fichier Excel Généré
(<img width="809" height="627" alt="Capture d&#39;écran 2025-12-29 124117" src="https://github.com/user-attachments/assets/387faa4a-e5d7-4b7c-bf10-8cecac35bf73" />
)

**Format de sortie :**
```
📊 resultats_anis121125.xlsx
```

**Colonnes du fichier Excel :**
| Colonne | Description |
|---------|-------------|
| `filename` | Nom du fichier image analysé |
| `valid_grid` | Grille détectée correctement (True/False) |
| `status_int` | État de la détection partie entière |
| `status_dec` | État de la détection partie décimale |
| `idx_int` | Index de la case cochée (partie entière) |
| `idx_dec` | Index de la case cochée (partie décimale) |
| `note_detected` | Note finale extraite (0.00 à 20.00) |
| `note_ground_truth` | Note réelle (à remplir manuellement) |
| `correct` | Validation de l'extraction |
| `error` | Message d'erreur éventuel |

---

## 🛠️ Technologies Utilisées

- **Python 3.8+** - Langage principal
- **OpenCV** - Traitement d'image et vision par ordinateur
- **NumPy** - Calculs numériques et manipulation de matrices
- **Pandas** - Génération et manipulation de données Excel

---

## ⚙️ Fonctionnalités Clés

### 🔍 Détection Intelligente
- ✅ Correction automatique de l'orientation via QR Code
- ✅ Extraction précise de la zone de notation (ROI)
- ✅ Détection robuste de la grille avec projections

### 📊 Analyse Avancée
- ✅ Seuillage adaptatif pour différentes qualités de scan
- ✅ Détection des cases cochées par analyse de densité
- ✅ Gestion des cas ambigus (plusieurs cases cochées)
- ✅ Validation de la grille (21 cases entières + 4 décimales)

### 📈 Génération de Rapports
- ✅ Export automatique vers Excel
- ✅ Métadonnées complètes pour chaque page
- ✅ Colonne de vérification manuelle intégrée

---

## 📁 Structure du Projet

```
projet-ocr-notes/
│
├── README.md                          # Ce fichier
├── main.py                            # Script principal
│
├── data/
│   ├── input/                         # Copies scannées
│   │   ├── anis121125_page-0001.jpg
│   │   ├── anis121125_page-0002.jpg
│   │   └── ...
│   │
│   └── output/                        # Fichiers Excel générés
│       └── resultats_anis121125.xlsx
│
├── docs/
│   ├── exemple_copie.jpg              # Exemple d'entrée
│   └── exemple_excel.png              # Exemple de sortie
│
└── requirements.txt                   # Dépendances Python
```

---

## 🚀 Installation et Utilisation

### Installation

```bash
# Cloner le repository
git clone https://github.com/votre-username/projet-ocr-notes.git
cd projet-ocr-notes

# Installer les dépendances
pip install -r requirements.txt
```

### Utilisation

```bash
# Exécuter l'analyse sur toutes les copies
python main.py
```

Le fichier Excel sera généré automatiquement dans le dossier de sortie.

---

## 📊 Résultats et Performance

- **Taux de détection de grille :** ~95%
- **Précision d'extraction :** Variable selon la qualité du scan
- **Gestion des cas ambigus :** Signalés automatiquement
- **Vitesse de traitement :** ~1-2 secondes par page

---

## 🎓 Cas d'Usage

- ✅ Correction automatisée d'examens
- ✅ Numérisation de grilles de notation
- ✅ Archivage digital de résultats scolaires
- ✅ Analyse statistique de performances académiques

---

## 🔮 Améliorations Futures

- [ ] Interface graphique (GUI) pour faciliter l'utilisation
- [ ] Support de différents formats de grilles
- [ ] Détection automatique des erreurs de scan
- [ ] Export multi-format (CSV, JSON, PDF)
- [ ] Intégration d'un modèle de Machine Learning pour améliorer la précision

---

## 👨‍💻 Auteur

**Votre Nom**  
Ingénieur en Vision par Ordinateur & Data Science

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://www.linkedin.com/in/votre-profil)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-black)](https://github.com/votre-username)

---

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou soumettre une pull request.

---

**⭐ Si ce projet vous a été utile, n'hésitez pas à lui donner une étoile !**
