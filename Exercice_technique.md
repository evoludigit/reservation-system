# Exercice technique – Développeur Python/Django

## Contexte

Nous souhaitons mettre en place un petit système de gestion de réservations de logements.
L'objectif est de vérifier votre compréhension de Django ORM, vos capacités de modélisation et
votre logique. L'exercice est conçu pour être réalisable en **moins d'une heure**.

## Consignes

- Fournissez uniquement du **code Python clair et lisible**, avec commentaires si nécessaire.
- Vous n'avez pas besoin de créer un projet Django complet (pas de migrations, pas de serveur à lancer).
- L'important est **la logique** et **la compréhension**, pas le packaging du projet.

## Énoncé

1. Un **logement** a :
   - un nom
   - une capacité (nombre de personnes)

2. Une **réservation** correspond à :
   - un logement
   - une date d'arrivée
   - une date de départ
   - un nom de client
   - un nombre de voyageurs

3. Il ne peut pas y avoir **deux réservations qui se chevauchent** pour un même logement.

## Travail demandé

1. Définir les modèles Django des logements et réservations
2. Implémenter une méthode qui valide qu'une réservation ne chevauche pas une autre.
3. *(Bonus)* Proposer des vues d'API permettant :
   - de créer une réservation
   - de lister les réservations (le nom du logement et sa capacité doivent apparaître dans les données renvoyées)
