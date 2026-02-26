from django.db import models

class ConfigurationSysteme(models.Model):
    """Modèle pour les configurations système."""
    cle = models.CharField(max_length=64, unique=True, verbose_name="Clé")
    valeur = models.TextField(verbose_name="Valeur")
    mis_a_jour_le = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    def __str__(self):
        return self.cle
