# 🏦 Système de Retrait Crédit avec Protection d'Éligibilité

## 📋 Vue d'ensemble

Ce système garantit que seuls les utilisateurs **ayant parrainé au minimum 5 personnes** avec des achats de produits élégibles (20$ ou 100$) peuvent demander un retrait crédit.

## 🔐 Fonctionnement

### 1. **Vérification d'Éligibilité**

L'utilisateur doit avoir:
- ✅ Minimum **5 filleuls** avec achats actifs
- ✅ Produits achetés coûtant **20$ ou 100$**
- ✅ L'achat doit être dans le statut **'actif'**

### 2. **Montants Élégibles**

| Montant | Filleuls Requis |
|---------|-----------------|
| 100$    | 5              |
| 500$    | 10             |
| 1000$   | 15             |
| 5000$   | 20             |

### 3. **Cycle de Remboursement**

Quand un utilisateur emprunte:
1. Une demande de `RetraitCredit` est créée
2. L'administrateur approuve ou rejette
3. Si approuvé, un `Pret` est activé
4. Le statut passe à **"en_remboursement"**
5. **Automatiquement**, un pourcentage des gains quotidiens est prélevé
6. Les ajustements sont trackés dans `AjustementRemboursement`
7. Quand le montant est remboursé, le prêt est marqué comme "remboursé"

## 🛠️ Modèles Créés

### `EligibiliteRetrait`
```python
- utilisateur (OneToOne)
- nombre_filleuls_requis
- nombre_filleuls_valides
- est_eligible (Boolean)
- derniere_verification (DateTime)
```

### `RetraitCredit`
```python
- utilisateur (ForeignKey)
- pret (OneToOne)
- montant_demande
- montant_approuve
- statut (demande | approuve | reject | en_remboursement | rembourse)
- nombre_filleuls_valides
- pourcentage_remboursement (10% par défaut)
- montant_rembourse
- montant_restant
- dates importantes (demande_le, approuve_le, debute_le, termine_le)
```

### `AjustementRemboursement`
```python
- retrait_credit (ForeignKey)
- gain_quotidien (ForeignKey)
- montant_gain
- montant_rembourse
- pourcentage_applique
- statut (en_attente | applique | annule)
```

## 📦 Utilisation dans les Vues

### Décorateur de Vue (Function-Based)
```python
from applications.prets.decorators import requerir_eligibilite_retrait

@requerir_eligibilite_retrait
def demander_retrait(request):
    # Code de la vue
    pass
```

### Mixin pour Class-Based Views
```python
from applications.prets.decorators import EligibiliteRetraitMixin

class DemanderRetraitView(EligibiliteRetraitMixin, CreateView):
    template_name = 'prets/demander_retrait.html'
    # ...
```

### API JSON
```python
from applications.prets.decorators import api_requerir_eligibilite_retrait

@api_requerir_eligibilite_retrait
def api_demander_retrait(request):
    return JsonResponse({...})
```

## 🔧 Utilisation du Code

### 1. Vérifier l'éligibilité
```python
from applications.prets.utils import VerificateurEligibilite

is_eligible, nb_filleuls, nb_requis = VerificateurEligibilite.verifier_utilisateur(user)
montant_max = VerificateurEligibilite.obtenir_montant_max_autorise(user)
```

### 2. Demander un retrait
```python
from applications.prets.utils import GestionnairePret

retrait, message = GestionnairePret.demander_retrait_credit(
    utilisateur=user,
    montant=100,
    duree_mois=12,
    taux_annuel=5
)

if retrait:
    print(f"Demande créée: {retrait.id}")
else:
    print(f"Erreur: {message}")
```

### 3. Approuver un retrait
```python
success, message = GestionnairePret.approuver_retrait(retrait)
```

### 4. Obtenir les infos de remboursement
```python
from applications.prets.utils import GestionnaireRemboursement

infos = GestionnaireRemboursement.obtenir_infos_remboursement(retrait)
# {
#     'montant_initial': ...,
#     'montant_rembourse': ...,
#     'montant_restant': ...,
#     'pourcentage_rembourse': 45.5,
#     'pourcentage_prelevement': 10.0,
# }
```

## 💾 Commandes Management

### Afficher les infos d'éligibilité
```bash
python manage.py gerer_retraits info --email=user@example.com
```

### Demander un retrait
```bash
python manage.py gerer_retraits demander --email=user@example.com --montant=100 --duree=12 --taux=5
```

### Approuver un retrait
```bash
python manage.py gerer_retraits approuver --email=user@example.com
```

### Rejeter un retrait
```bash
python manage.py gerer_retraits rejeter --email=user@example.com --raison="Raison du rejet"
```

### Afficher les remboursements
```bash
python manage.py gerer_retraits remboursements --email=user@example.com
```

## 🔄 Signaux Automatiques

### Création d'ajustements
Quand un `GainQuotidien` est créé:
- ✅ Détecte tous les retraits "en_remboursement" de l'utilisateur
- ✅ Crée automatiquement un `AjustementRemboursement`
- ✅ Calcule le pourcentage à prélever
- ✅ Applique le remboursement

### Synchronisation Prêt/Retrait
- Quand le retrait est remboursé → Le prêt devient "remboursé"
- Quand le retrait est rejeté → Le prêt devient "défaut"

## 📊 Exemples Pratiques

### Exemple 1: Utilisateur demande 100$
1. Vérifie: 7 filleuls avec achats → ✅ Éligible
2. Crée demande de `RetraitCredit` (montant=100, statut='demande')
3. Crée un `Pret` associé (statut='en_attente')
4. Admin approuve
5. Prêt devient 'actif', retrait 'en_remboursement'
6. Chaque jour, si l'utilisateur gagne 50$:
   - 10% de 50$ = 5$ prélevés automatiquement
   - Crée `AjustementRemboursement` (5$)
   - Montant_restant devient 95$
7. Après 20 jours ≈ 100$ remboursés
8. Retrait et Prêt marqués "remboursé"

### Exemple 2: Utilisateur non éligible
1. Seuls 3 filleuls avec achats → ❌ Non éligible
2. Le bouton "Retrait Crédit" est désactivé
3. Message: "Vous avez 3/5 filleuls requis"

## 🎯 Protection du Bouton

### HTML
```html
{% if user.is_authenticated %}
    {% load prets_tags %}
    {% if user|can_withdraw_credit %}
        <button class="btn btn-primary">Demander Retrait Crédit</button>
    {% else %}
        <button class="btn btn-secondary" disabled title="Non éligible">
            Retrait Crédit Bloqué
        </button>
    {% endif %}
{% endif %}
```

### Template Tag Custom (Optionnel)
```python
# applications/prets/templatetags/prets_tags.py
from django import template
from applications.prets.utils import VerificateurEligibilite

register = template.Library()

@register.filter
def can_withdraw_credit(user):
    is_eligible, _, _ = VerificateurEligibilite.verifier_utilisateur(user)
    return is_eligible

@register.filter
def filleuls_info(user):
    is_eligible, nb, requis = VerificateurEligibilite.verifier_utilisateur(user)
    return f"{nb}/{requis}"
```

## 🚀 Migration

N'oublie pas de créer les migrations:
```bash
python manage.py makemigrations prets
python manage.py migrate
```

## ⚙️ Configuration

### Modifier les exigences
Edit `applications/prets/utils.py`:
```python
class VerificateurEligibilite:
    MONTANTS_ELIGIBILITE = {
        Decimal('100'): 5,
        Decimal('500'): 10,
        # ...
    }
    MONTANTS_PRODUITS_ELIGIBLES = [Decimal('20'), Decimal('100')]
```

### Modifier le pourcentage de remboursement
```python
retrait = RetraitCredit.objects.get(id=1)
retrait.pourcentage_remboursement = Decimal('15.00')  # 15% au lieu de 10%
retrait.save()
```

## 🐛 Debugging

Activer les logs:
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'applications.prets': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 📞 Support

Pour toute question sur:
- L'éligibilité: Voir `VerificateurEligibilite`
- Les retraits: Voir `GestionnairePret`
- Les remboursements: Voir `GestionnaireRemboursement`

