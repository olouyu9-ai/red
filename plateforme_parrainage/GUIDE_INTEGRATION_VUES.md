# 🔧 GUIDE RAPIDE D'INTÉGRATION AUX VUES

## 1️⃣ Template - Afficher le Bouton Protégé

### HTML Standard
```html
<div class="retrait-section">
    {% if user.is_authenticated %}
        {% load prets_tags %}
        
        {% if user|can_withdraw_credit %}
            <!-- Utilisateur ÉLIGIBLE -->
            <div class="alert alert-success">
                ✅ Vous êtes éligible au retrait crédit
            </div>
            <a href="{% url 'demander_retrait_credit' %}" class="btn btn-primary btn-lg">
                💰 Demander Retrait Crédit
            </a>
        {% else %}
            <!-- Utilisateur NON ÉLIGIBLE -->
            <div class="alert alert-warning">
                ❌ Retrait crédit non disponible
            </div>
            <div class="eligibilite-info">
                {% if filleuls_info %}
                    <p>Filleuls valides: <strong>{{ filleuls_info }}</strong> (minimum 5 requis)</p>
                {% endif %}
            </div>
            <button class="btn btn-secondary" disabled>
                🔒 Retrait Crédits Bloqué
            </button>
            <small class="text-muted">
                Vous avez besoin de parrainer {{ filleuls_manquants }} personne(s) de plus 
                avec des achats de produits à 20$ ou 100$.
            </small>
        {% endif %}
    {% else %}
        <p><a href="{% url 'login' %}">Se connecter</a> pour accéder aux retraits crédit</p>
    {% endif %}
</div>
```

### Bootstrap 5 Simplifiée
```html
{% if user|can_withdraw_credit %}
    <a href="{% url 'demander_retrait_credit' %}" class="btn btn-success">
        💰 Demander Retrait Crédit
    </a>
{% else %}
    <button class="btn btn-outline-danger" disabled title="Non éligible">
        🔒 Retrait Bloqué
    </button>
{% endif %}
```

---

## 2️⃣ View - Function-Based

### Décorateur Simple
```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from applications.prets.decorators import requerir_eligibilite_retrait
from applications.prets.utils import GestionnairePret

@login_required
@requerir_eligibilite_retrait
def demander_retrait_credit(request):
    """Vue protégée pour demander un retrait crédit."""
    
    if request.method == 'POST':
        montant = request.POST.get('montant')
        duree = request.POST.get('duree', 12)
        taux = request.POST.get('taux', 0)
        
        retrait, message = GestionnairePret.demander_retrait_credit(
            utilisateur=request.user,
            montant=montant,
            duree_mois=int(duree),
            taux_annuel=taux
        )
        
        if retrait:
            messages.success(request, f"✅ {message}")
            return redirect('voir_retrait', retrait_id=retrait.id)
        else:
            messages.error(request, f"❌ {message}")
    
    return render(request, 'prets/demander_retrait.html')
```

### Sans Décorateur (Vérification Manuelle)
```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from applications.prets.utils import VerificateurEligibilite, GestionnairePret

@login_required
def demander_retrait_credit(request):
    """Vue avec vérification d'éligibilité manuelle."""
    
    # Vérifier l'éligibilité
    is_eligible, nb_filleuls, nb_requis = VerificateurEligibilite.verifier_utilisateur(request.user)
    
    if not is_eligible:
        messages.error(
            request,
            f"❌ Non éligible. Filleuls: {nb_filleuls}/{nb_requis}"
        )
        return redirect('tableau_de_bord')
    
    if request.method == 'POST':
        montant = request.POST.get('montant')
        retrait, msg = GestionnairePret.demander_retrait_credit(request.user, montant)
        
        if retrait:
            messages.success(request, "✅ Demande créée")
            return redirect('voir_retrait', retrait.id)
        else:
            messages.error(request, f"❌ {msg}")
    
    return render(request, 'prets/demander_retrait.html')
```

---

## 3️⃣ View - Class-Based

### Avec Mixin Complet
```python
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from applications.prets.decorators import EligibiliteRetraitMixin
from applications.prets.models import RetraitCredit
from applications.prets.utils import GestionnairePret

class DemanderRetraitCreditView(EligibiliteRetraitMixin, CreateView):
    """Demander un retrait crédit (protégé par mixin)."""
    model = RetraitCredit
    fields = ['montant_demande']
    template_name = 'prets/demander_retrait.html'
    success_url = reverse_lazy('voir_retraits')
    
    def form_valid(self, form):
        montant = form.cleaned_data['montant_demande']
        
        retrait, msg = GestionnairePret.demander_retrait_credit(
            utilisateur=self.request.user,
            montant=montant
        )
        
        if retrait:
            messages.success(self.request, "✅ Demande créée")
            return super().form_valid(form)
        else:
            messages.error(self.request, f"❌ {msg}")
            return self.form_invalid(form)


class VoirRetraitsView(EligibiliteRetraitMixin, TemplateView):
    """Voir les retraits (seulement si éligible)."""
    template_name = 'prets/voir_retraits.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Les infos d'éligibilité sont déjà dans le contexte grâce au mixin
        # context['nb_filleuls_valides'] 
        # context['montant_max_autorise']
        
        # Ajouter les retraits de l'utilisateur
        from applications.prets.models import RetraitCredit
        context['retraits'] = RetraitCredit.objects.filter(
            utilisateur=self.request.user
        ).order_by('-demande_le')
        
        return context
```

---

## 4️⃣ API View - JSON

### API Vérification Éligibilité
```python
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from applications.prets.decorators import api_requerir_eligibilite_retrait
from applications.prets.decorators import obtenir_infos_eligibilite_complet

@require_POST
@login_required
def api_verifier_eligibilite(request):
    """API pour vérifier l'éligibilité."""
    
    infos = obtenir_infos_eligibilite_complet(request.user)
    
    return JsonResponse({
        'success': True,
        'data': {
            'est_eligible': infos['is_eligible'],
            'nb_filleuls_valides': infos['nombre_filleuls_valides'],
            'nb_filleuls_requis': infos['nombre_filleuls_requis'],
            'montant_max': str(infos['montant_maximum_autorise']),
            'filleuls_manquants': infos['filleuls_manquants'],
            'statut': infos['statut'],
        }
    })


@require_POST
@api_requerir_eligibilite_retrait
def api_demander_retrait(request):
    """API pour demander un retrait."""
    import json
    
    try:
        data = json.loads(request.body)
        montant = data.get('montant')
        
        if not montant:
            return JsonResponse({'error': 'Montant requis'}, status=400)
        
        retrait, msg = GestionnairePret.demander_retrait_credit(
            request.user, montant
        )
        
        if retrait:
            return JsonResponse({
                'success': True,
                'message': msg,
                'retrait_id': retrait.id,
                'statut': retrait.get_statut_display()
            })
        else:
            return JsonResponse({
                'success': False,
                'error': msg
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
```

### API pour infos remboursement
```python
from applications.prets.models import RetraitCredit
from applications.prets.utils import GestionnaireRemboursement

@login_required
def api_infos_remboursement(request, retrait_id):
    """Obtenir les infos de remboursement."""
    
    try:
        retrait = RetraitCredit.objects.get(
            id=retrait_id,
            utilisateur=request.user
        )
    except RetraitCredit.DoesNotExist:
        return JsonResponse({'error': 'Non trouvé'}, status=404)
    
    infos = GestionnaireRemboursement.obtenir_infos_remboursement(retrait)
    
    return JsonResponse({
        'success': True,
        'data': {
            'montant_initial': str(infos['montant_initial']),
            'montant_approuve': str(infos['montant_approuve']),
            'montant_rembourse': str(infos['montant_rembourse']),
            'montant_restant': str(infos['montant_restant']),
            'pourcentage_rembourse': float(infos['pourcentage_rembourse']),
            'pourcentage_prelevement': float(infos['pourcentage_prelevement']),
            'statut': infos['statut'],
        }
    })
```

---

## 5️⃣ URLs - Enregistrer les Routes

```python
# applications/prets/urls.py

from django.urls import path
from . import views

app_name = 'prets'

urlpatterns = [
    # Pages
    path('demander/', views.DemanderRetraitCreditView.as_view(), name='demander_retrait_credit'),
    path('mes-retraits/', views.VoirRetraitsView.as_view(), name='voir_retraits'),
    
    # APIs
    path('api/verifier-eligibilite/', views.api_verifier_eligibilite, name='api_verifier_eligibilite'),
    path('api/demander-retrait/', views.api_demander_retrait, name='api_demander_retrait'),
    path('api/remboursement/<int:retrait_id>/', views.api_infos_remboursement, name='api_infos_remboursement'),
]
```

---

## 6️⃣ Template Tags Personnalisés

### Créer le fichier
```bash
mkdir -p applications/prets/templatetags
touch applications/prets/templatetags/__init__.py
touch applications/prets/templatetags/prets_tags.py
```

### Contenu
```python
# applications/prets/templatetags/prets_tags.py

from django import template
from applications.prets.utils import VerificateurEligibilite, GestionnaireRemboursement
from applications.prets.models import RetraitCredit

register = template.Library()

@register.filter
def can_withdraw_credit(user):
    """Vérifie si l'utilisateur peut faire un retrait."""
    is_eligible, _, _ = VerificateurEligibilite.verifier_utilisateur(user)
    return is_eligible

@register.filter
def filleuls_info(user):
    """Retourne les infos filleuls (nb/requis)."""
    is_eligible, nb, requis = VerificateurEligibilite.verifier_utilisateur(user)
    return f"{nb}/{requis}"

@register.filter
def montant_max_retrait(user):
    """Montant maximum que peut s'emprunter."""
    from decimal import Decimal
    montant = VerificateurEligibilite.obtenir_montant_max_autorise(user)
    return f"{montant}$"

@register.simple_tag
def filleuls_manquants(user):
    """Nombre de filleuls manquants."""
    is_eligible, nb, requis = VerificateurEligibilite.verifier_utilisateur(user)
    return max(0, requis - nb)

@register.simple_tag
def retrait_actif(user):
    """Récupère le retrait en cours de l'utilisateur."""
    return RetraitCredit.objects.filter(
        utilisateur=user,
        statut__in=['demande', 'approuve', 'en_remboursement']
    ).first()

@register.simple_tag
def progression_retrait(retrait):
    """Progression du remboursement en %."""
    if not retrait:
        return 0
    return GestionnaireRemboursement.calculer_progression(retrait)
```

### Utilisation dans Template
```html
{% load prets_tags %}

{{ user|can_withdraw_credit }}
{{ user|filleuls_info }}
{{ user|montant_max_retrait }}

{% filleuls_manquants user as manquants %}
Il vous faut encore {{ manquants }} filleul(s)

{% retrait_actif user as retrait %}
{% if retrait %}
    Remboursement: {% progression_retrait retrait %}%
{% endif %}
```

---

## 7️⃣ Modal Bootstrap - Demander Retrait

```html
<!-- Modal -->
<div class="modal fade" id="retraitModal">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">💰 Demander Retrait Crédit</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                {% if eligibilite.is_eligible %}
                    <form id="formRetrait">
                        {% csrf_token %}
                        
                        <div class="mb-3">
                            <label for="montant" class="form-label">Montant $</label>
                            <input type="number" class="form-control" id="montant" 
                                   name="montant" min="100" max="{{ eligibilite.montant_max_autorise }}"
                                   placeholder="100 - {{ eligibilite.montant_max_autorise }}" required>
                            <small class="text-muted">
                                Max: {{ eligibilite.montant_max_autorise }}$
                            </small>
                        </div>
                        
                        <div class="alert alert-info">
                            ✅ Vous avez {{ eligibilite.nb_filleuls_valides }} filleuls valides
                        </div>
                    </form>
                {% else %}
                    <div class="alert alert-warning">
                        ❌ Non éligible
                        <p>{{ eligibilite.nb_filleuls_valides }}/{{ eligibilite.nb_filleuls_requis }} filleuls</p>
                    </div>
                {% endif %}
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                {% if eligibilite.is_eligible %}
                    <button type="button" class="btn btn-success" id="btnRetrait">Demander</button>
                {% else %}
                    <button type="button" class="btn btn-secondary" disabled>Non disponible</button>
                {% endif %}
            </div>
        </div>
    </div>
</div>

<script>
document.getElementById('btnRetrait').addEventListener('click', function() {
    const montant = document.getElementById('montant').value;
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('{% url "prets:api_demander_retrait" %}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({ montant: montant })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            alert('✅ Demande créée!');
            location.reload();
        } else {
            alert('❌ Erreur: ' + data.error);
        }
    })
    .catch(e => alert('Erreur: ' + e));
});
</script>
```

---

## 🎯 Résumé d'intégration

```
1. ✅ Créer template avec bouton protégé
2. ✅ Créer vue avec décorateur
3. ✅ Enregistrer URL
4. ✅ Tester l'accès (éligible vs non-éligible)
5. ✅ Ajouter template tags (optionnel)
6. ✅ Tester le flux complet
```

Tout le code est prêt à l'emploi - copier/coller directement! 🚀

