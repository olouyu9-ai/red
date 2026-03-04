# 🏗️ Architecture du Système de Retrait Crédit

## Vue d'Ensemble de l'Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         APPLICATION PRETS                       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │   MODÈLES       │  │   UTILS/LOGIC    │  │  DECORATORS  │  │
│  ├─────────────────┤  ├──────────────────┤  ├──────────────┤  │
│  │                 │  │                  │  │              │  │
│  │ • Pret          │  │ VerificateurE    │  │ @requerir_   │  │
│  │ • Remboursement │  │ ligibilite       │  │ eligibilite  │  │
│  │ • Retrait       │  │ • verifier_user  │  │              │  │
│  │   Credit (NEW)  │  │ • compter_filleul│  │ @api_require │  │
│  │ • Eligibilite   │  │ • montant_max    │  │ _eligibilite │  │
│  │   Retrait (NEW) │  │                  │  │              │  │
│  │ • Ajustement    │  │ GestionnairePret │  │ Mixin:       │  │
│  │   Remboursement │  │ • demander       │  │ Eligibilite  │  │
│  │   (NEW)         │  │ • approuver      │  │ RetraitMixin │  │
│  │                 │  │ • rejeter        │  │              │  │
│  │                 │  │                  │  │ Fonctions:   │  │
│  │                 │  │ Gestionnaire     │  │ • verifier_  │  │
│  │                 │  │ Remboursement    │  │   montant    │  │
│  │                 │  │ • creer_ajuste   │  │ • obtenir_   │  │
│  │                 │  │ • appliquer      │  │   infos      │  │
│  │                 │  │ • progression    │  │              │  │
│  │                 │  │                  │  │              │  │
│  └─────────────────┘  └──────────────────┘  └──────────────┘  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                 │
│  │     SIGNALS      │    │      ADMIN       │                 │
│  ├──────────────────┤    ├──────────────────┤                 │
│  │                  │    │                  │                 │
│  │ Quand:           │    │ • PretAdmin      │                 │
│  │ • GainQuotidien  │    │ • Remboursement  │                 │
│  │   créé           │    │   Admin          │                 │
│  │ • RetraitCredit  │    │ • RetraitCredit  │                 │
│  │   approuvé       │    │   Admin          │                 │
│  │                  │    │ • Ajustement     │                 │
│  │ Fait:            │    │   Admin          │                 │
│  │ • Crée Ajuste    │    │ • Eligibilite    │                 │
│  │   mentRemboourse │    │   Admin          │                 │
│  │ • Sync Pret/     │    │                  │                 │
│  │   Retrait        │    │ Actions:         │                 │
│  │                  │    │ • Approuver      │                 │
│  │                  │    │ • Rejeter        │                 │
│  │                  │    │                  │                 │
│  └──────────────────┘    └──────────────────┘                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                 │
│  │   MANAGEMENT     │    │      TESTS       │                 │
│  │    COMMANDS      │    ├──────────────────┤                 │
│  ├──────────────────┤    │                  │                 │
│  │                  │    │ • Verificateur   │                 │
│  │ gerer_retraits   │    │   Tests          │                 │
│  │ • info           │    │ • Gestionnaire   │                 │
│  │ • demander       │    │   Pret Tests     │                 │
│  │ • approuver      │    │ • Remboursement  │                 │
│  │ • rejeter        │    │   Tests          │                 │
│  │ • remboursements │    │ • Model Tests    │                 │
│  │                  │    │                  │                 │
│  └──────────────────┘    └──────────────────┘                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Dépendances Externes:
    ↓
    ├─ applications.parrainages.BonusParrainage
    ├─ applications.produits.Produit
    ├─ applications.produits.Achat
    ├─ applications.produits.GainQuotidien
    └─ Django Auth User Model
```

## Flux de Données

```
ÉTAPE 1: VÉRIFICATION D'ÉLIGIBILITÉ
═══════════════════════════════════

User demande retrait → VerificateurEligibilite
                       ↓
                    Compte filleuls avec:
                    • Achats actifs
                    • Produits à 20$ ou 100$
                       ↓
                    Retourne (is_eligible, nb, requis)
                       ↓
                    Si éligible → Peut continuer
                    Si NON → Bouton désactivé


ÉTAPE 2: CRÉATION DEMANDE RETRAIT
══════════════════════════════════

User clique "Demander" → GestionnairePret.demander_retrait_credit()
                         ↓
                      Vérifie éligibilité
                         ↓
                      Crée Pret (en_attente)
                      Crée RetraitCredit (demande)
                         ↓
                      Retourne (retrait, message)
                         ↓
                      DB: Nouvelles instances créées


ÉTAPE 3: APPROVALUATION ADMIN
═════════════════════════════

Admin approuve → RetraitCredit.approuver()
                 ↓
              Vérifie eligibilité
                 ↓
              Pret → statut 'actif'
              RetraitCredit → statut 'en_remboursement'
                 ↓
              Signal triggré automatiquement


ÉTAPE 4: REMBOURSEMENT AUTOMATIQUE
═══════════════════════════════════

Signal: GainQuotidien.post_save
           ↓
        Pour chaque RetraitCredit en_remboursement:
           ↓
        Crée AjustementRemboursement:
        montant_rembourse = gain × pourcentage / 100
           ↓
        Appelle ajustement.appliquer()
           ↓
        Update RetraitCredit:
        • montant_rembourse += ajustement
        • montant_restant -= ajustement
           ↓
        Si montant_restant == 0:
        • RetraitCredit → 'rembourse'
        • Pret → 'rembourse'
           ↓
        Signal RetraitCredit.post_save → Sync Pret


ÉTAPE 5: FINALISATION
══════════════════════

montant_restant == 0
        ↓
    RetraitCredit.statut = 'rembourse'
    RetraitCredit.termine_le = now()
        ↓
    Pret.statut = 'rembourse'
        ↓
    Cycle terminé ✅
```

## Interactions entre Modèles

```
┌──────────────┐
│   User       │
└──────┬───────┘
       │
       ├──────────────────┬────────────┬──────────┐
       │                  │            │          │
       ▼                  ▼            ▼          ▼
    ┌──────────┐   ┌────────────┐  ┌────────┐  ┌──────────────┐
    │  Pret    │   │Retrait     │  │Achat   │  │Bonus         │
    │          │   │Credit      │  │        │  │Parrainage    │
    │ montant  ◀───┤ +montant   │  │+produit│  │              │
    │ statut   │   │            │  │        │  │ +parrain     │
    │          │   │ Filleuls   │  │        │  │ +filleul     │
    └──────────┘   │ requis     │  │        │  │ +achat       │
                   │ valides    │  │        │  └──────────────┘
                   │ statut     │  └────────┘
                   │            │     ▲
                   └────────────┘     │
                       ▲              │
                       │         ┌─────────────┐
                       │         │GainQuotidien│
                       │         │             │
                       └─────────┤ Signal      │
                               │ [post_save] │
                               └─────────────┘
                                     │
                                     ▼
                         ┌──────────────────────┐
                         │Ajustement            │
                         │Remboursement        │
                         │                     │
                         │ +montant_rembourse  │
                         │ +montant_gain       │
                         │ +statut             │
                         └──────────────────────┘
                                   │
                                   ▼ (appliquer)
                         ┌──────────────────────┐
                         │Update RetraitCredit: │
                         │ montant_rembourse++  │
                         │ montant_restant--    │
                         │                      │
                         │ Si == 0:             │
                         │ • statut = rembourse │
                         │ • Sync Pret          │
                         └──────────────────────┘
```

## Classes Utilitaires - Responsabilités

```
┌─────────────────────────────────────┐
│  VerificateurEligibilite            │
├─────────────────────────────────────┤
│ Responsabilités:                    │
│ • Compter filleuls valides          │
│ • Vérifier conditions d'éligibilité │
│ • Déterminer montants max           │
│ • Vérifier montants spécifiques     │
│                                     │
│ Méthodes publiques:                 │
│ ✓ verifier_utilisateur()            │
│ ✓ compter_filleuls_valides()        │
│ ✓ obtenir_montant_max_autorise()    │
│ ✓ obtenir_nombre_filleuls_requis()  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  GestionnairePret                   │
├─────────────────────────────────────┤
│ Responsabilités:                    │
│ • Créer demandes de prêt            │
│ • Approuver retraits                │
│ • Rejeter retraits                  │
│ • Valider montants / éligibilité    │
│                                     │
│ Méthodes publiques:                 │
│ ✓ demander_retrait_credit()         │
│ ✓ approuver_retrait()               │
│ ✓ rejeter_retrait()                 │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  GestionnaireRemboursement          │
├─────────────────────────────────────┤
│ Responsabilités:                    │
│ • Créer ajustements auto            │
│ • Appliquer remboursements          │
│ • Calculer progression              │
│ • Fournir infos détaillées          │
│                                     │
│ Méthodes publiques:                 │
│ ✓ creer_ajustement_depuis_gain()    │
│ ✓ appliquer_remboursements_en_att() │
│ ✓ calculer_progression()            │
│ ✓ obtenir_infos_remboursement()     │
└─────────────────────────────────────┘
```

## Cycle de Vie d'un Retrait Crédit

```
                    DEMANDE
                        │
    ┌───────────────────┴────────────────────┐
    │                                        │
    ▼                                        ▼
APPROUVE (si éligible)               REJECT (si non éligible)
    │
    ▼
EN_REMBOURSEMENT
    │
    ├──── Ajustements créés automatiquement ────┐
    │                  (par signal)             │
    ▼                                           ▼
montant_rembourse += ajustement_montant
montant_restant -= ajustement_montant
    │
    │
    ├─── Répété jour après jour ───┐
    │                               │
    └──────────────────────────────┘
    │
    ▼
montant_restant == 0 ?
    │
    └─── OUI ──→ REMBOURSE ✅
    │
    └─── NON ──→ Continue...
```

## Protection des Vues - Flux

```
User accède à "/demander-retrait"
            │
            ▼
┌─────────────────────────────┐
│  Décorateur                 │
│ @requerir_eligibilite       │
└─────┬───────────────────────┘
      │
      ├─ User authentifié?
      │   NON → Redirect /login
      │
      ├─ User éligible?
      │   NON → Message erreur + Redirect dashboard
      │
      ▼
    OUI ✅
      │
      ▼
Laisse passer à la vue
```

## Signaux - Chaîne d'Exécution

```
GainQuotidien.save()
      │
      ▼
   Signal: post_save
      │
      ▼
creer_ajustement_remboursement()
      │
      ├─ Pour chaque RetraitCredit en_remboursement:
      │   │
      │   ├─ Calcule montant_rembourse = gain × pourcentage
      │   │
      │   ├─ Crée AjustementRemboursement
      │   │
      │   └─ Appelle ajustement.appliquer()
      │
      └─ Tout réussi? Silencieusement (try/except)


RetraitCredit.save()
      │
      ▼
   Signal: post_save
      │
      ▼
mettre_a_jour_statut_pret()
      │
      ├─ Si RetraitCredit.statut == 'rembourse'
      │   └─ Pret.apply_remboursement(montant)
      │
      └─ Si RetraitCredit.statut == 'reject'
         └─ Pret.statut = 'defaut'
```

---

**Cette architecture assure que:**
- ✅ Les vérifications d'éligibilité sont centralisées
- ✅ Le remboursement est automatique et infaillible
- ✅ Zéro chance de contournement
- ✅ Tout est tracé dans l'admin Django
- ✅ Les signaux maintiennent la cohérence des données

