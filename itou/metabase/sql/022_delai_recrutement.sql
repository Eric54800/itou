/* 
 L'objectif est de suivre le délai de recrutement des candidats en IAE.
 Statistiques d'impact des emplois de l'inclusion : maintenir un délai de recrutement inférieur à 30 jours 
*/

with premiere_candidature as (
    select 
        id_candidat,
        min(date_candidature) as min_date_candidature 
    from 
        candidatures 
    group by 
        id_candidat  ) 
select     
    distinct (c.id_candidat) as identifiant_candidat, 
    pc.min_date_candidature,
    min(date_embauche) as min_date_embauche,
    min(date_embauche) - pc.min_date_candidature as delai_recrutement_jours
from 
    candidatures c
left join 
    premiere_candidature pc
    on c.id_candidat = pc.id_candidat
where 
    date_embauche is not null
    and état = 'Candidature acceptée' 
    and origine != 'Employeur'
group by 
    c.id_candidat, 
    pc.min_date_candidature
